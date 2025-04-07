import os
import json
import random
from typing import List, Dict, Any, Optional
# from config import * # Assuming config details are handled elsewhere or passed in
from subfields import AstronomySubfield, ASTRONOMY_SUBFIELDS # Assuming this import works

# Import the LLMClient wrapper
from llm_client import LLMClient # Assuming this import works

# Try to import Google's genai library for backward compatibility
try:
    from google import genai
except ImportError:
    genai = None

# NOTE: This file implements the two-call approach for initial idea generation.
# It now includes the detailed topic selection logic from the original idea_agent.py
# and the creativity prompts discussed.

class IdeaAgentTwoCalls:
    """
    Stateful agent that generates astronomy research ideas using a two-call approach
    (generate question, then generate solution) and improves them.
    Includes detailed topic selection logic prioritizing user context and creativity prompts.
    """
    def __init__(self, api_key, provider="azure"):
        self.api_key = api_key
        self.provider = provider

        # Initialize the LLM client with the appropriate provider
        try:
            self.llm_client = LLMClient(api_key, provider)
        except ValueError as e:
            raise ValueError(f"Error initializing idea agent: {str(e)}")

        self.original_prompt_question = None # Store the prompt for question generation
        self.original_prompt_solution = None # Store the prompt for solution generation
        self.current_idea = None
        self.student_profile = None
        self.feedback_history = []
        self.improvement_count = 0

    def generate_initial_idea(
        self,
        student_interests: Optional[List[str]] = None,
        skill_level: str = "beginner",
        time_frame: str = "2-3 years",
        available_resources: Optional[List[str]] = None,
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generate initial research idea using a two-step (question, then solution) approach.
        """
        # Store student profile
        self.student_profile = {
            "student_interests": student_interests or [random.choice(ASTRONOMY_SUBFIELDS).name],
            "skill_level": skill_level,
            "time_frame": time_frame,
            "available_resources": available_resources or ["Public astronomical datasets", "University computing cluster"],
            "additional_context": additional_context
        }

        # --- Step 1: Generate Research Question ---
        generated_question_text = self._generate_research_question(
            student_interests=self.student_profile["student_interests"],
            skill_level=skill_level,
            time_frame=time_frame,
            available_resources=self.student_profile["available_resources"],
            additional_context=additional_context
        )

        # Basic parsing for the question
        parsed_question = generated_question_text.strip()
        if not parsed_question:
            # Fallback: If question generation fails, maybe try original agent or raise clearer error
            print("WARNING: Failed to generate a specific research question. Falling back or raising error might be needed.")
            # For now, let's create a placeholder question to allow solution generation attempt
            parsed_question = f"Explore {', '.join(self.student_profile['student_interests'])} using available resources."
            # Alternatively: raise RuntimeError("Failed to generate a research question.")


        # --- Step 2: Generate Solution/Proposal based on the Question ---
        generated_solution_dict = self._generate_solution_proposal(
            research_question=parsed_question,
            skill_level=skill_level,
            time_frame=time_frame,
            available_resources=self.student_profile["available_resources"],
            student_interests=self.student_profile["student_interests"],
            additional_context=additional_context
        )

        # --- Step 3: Combine Question and Solution into Final Structure ---
        self.current_idea = self._combine_question_solution(
            parsed_question,
            generated_solution_dict,
            self.student_profile # Pass the full profile for metadata
        )

        return self.current_idea

    def _generate_research_question(self, student_interests, skill_level, time_frame, available_resources, additional_context) -> str:
        """Generates *only* the research question text using an LLM call, including detailed topic selection."""

        # --- Detailed Topic Selection Logic (from original idea_agent.py) ---
        relevant_subfields = []
        for subfield in ASTRONOMY_SUBFIELDS:
            if subfield.name in student_interests or any(interest in subfield.related_fields for interest in student_interests):
                relevant_subfields.append(subfield)
        if not relevant_subfields:
            relevant_subfields = random.sample(ASTRONOMY_SUBFIELDS, 2) # Fallback

        # Check if the user has specified research directions in additional_context
        user_specified_topics = []
        if additional_context and additional_context.strip():
            context_sentences = additional_context.split('.')
            for sentence in context_sentences:
                sentence = sentence.strip()
                interest_indicators = [
                    "interested in", "want to study", "focus on", "research on",
                    "investigate", "explore", "work on", "curious about", "question is",
                    "wondering about", "like to understand", "project on"
                ]
                if any(indicator in sentence.lower() for indicator in interest_indicators) and len(sentence) > 20:
                    user_specified_topics.append(sentence)

        # Initialize selected_topics
        selected_topics = []
        topic_source = "User Context" # Track where topics came from

        # If user specified topics, use ONLY those
        if user_specified_topics:
            selected_topics = user_specified_topics[:4] # Limit to 4 user topics
        else:
            # Only if no user topics are found, generate from subfields
            topic_source = "Subfield Challenges/Concepts"
            random_topics_pool = []
            for subfield in relevant_subfields:
                # Add challenges
                if subfield.current_challenges:
                    challenge_count = min(2, len(subfield.current_challenges))
                    selected_challenges = random.sample(subfield.current_challenges, challenge_count)
                    random_topics_pool.extend(selected_challenges)
                # Add key concepts from description
                key_concepts = []
                description_sentences = subfield.description.split('.')
                for sentence in description_sentences:
                    words = sentence.split()
                    if len(words) > 3 and any(word[0].isupper() for word in words if len(word) > 1):
                        clean_sentence = sentence.strip()
                        if clean_sentence:
                            key_concepts.append(clean_sentence)
                if key_concepts:
                    concept_count = min(1, len(key_concepts))
                    selected_concepts = random.sample(key_concepts, concept_count)
                    random_topics_pool.extend(selected_concepts)

            # Shuffle and limit if pool is not empty
            if random_topics_pool:
                random.shuffle(random_topics_pool)
                # Select a few diverse topics as seeds
                selected_topics = random_topics_pool[:max(1, len(relevant_subfields))] # Get 1 or more topics
            else:
                # Fallback if no challenges/concepts found
                 selected_topics = [f"Explore topics within {', '.join(s.name for s in relevant_subfields)}"]


        # Remove duplicates while preserving order
        selected_topics = list(dict.fromkeys(selected_topics))
        # --- End of Detailed Topic Selection Logic ---


        # *** Prompt for Question Generation ***
        # Includes creativity prompts
        self.original_prompt_question = f"""
Generate ONE single, specific, compelling, and potentially **novel** astronomy research question suitable for a {skill_level} graduate student.

Parameters:
- Student interests: {', '.join(student_interests)}
- Relevant subfields: {', '.join(subfield.name for subfield in relevant_subfields)}
- Time frame: {time_frame}
- Available resources: {', '.join(available_resources)}
- Skill level: {skill_level}
- Additional Student Context: {additional_context or "None provided."}

The generated question should be strongly guided by these specific directions (derived from {topic_source}):
{chr(10).join(f"- {topic}" for topic in selected_topics)}

**Key Goal:** Generate a focused, scientifically interesting, and novel research question that addresses a specific problem or knowledge gap. **Enhance creativity by seeking scientifically plausible connections between different concepts or the provided challenges.** The question must be potentially answerable within the student's constraints (skills, time, resources).

**Output:**
Respond ONLY with the research question itself. It should be concise and clear. Optionally, include a brief (1-sentence) statement of the problem it addresses. Do NOT include methodology, background, or any other sections.

Example Question Format:
"How can [Specific Method/Data] be used to investigate [Specific Phenomenon/Object] to address the problem of [Specific Knowledge Gap]?"
OR just the question itself.
"""
        print("--- Generating Question ---")
        # print("Question Prompt:", self.original_prompt_question) # Optional: print prompt for debugging

        try:
            question_text = self.llm_client.generate_content(self.original_prompt_question)
            return question_text
        except Exception as e:
            print(f"Error generating research question: {str(e)}")
            # Consider more robust error handling here
            return f"Error generating question: {e}" # Return error message


    def _generate_solution_proposal(self, research_question, skill_level, time_frame, available_resources, student_interests, additional_context) -> Dict[str, Any]:
        """Generates the proposal sections (Background, Methodology, etc.) for a given research question."""

        # Condensed scientific principles + creativity nudge
        condensed_guidelines = f"""
**Key Scientific Principles:**
- Methods must be scientifically sound, clearly linked to the **provided research question**, and appropriate for the data/resources.
- Claims must be realistic and proportional to what the methods and data can actually measure (consider S/N, statistical power, parameter degeneracies).
- Describe phenomena and use terminology accurately according to established scientific understanding.
- Scope: The project must be feasible for the student's level ({skill_level}), completable within the timeframe ({time_frame}), and utilize only the specified available resources ({', '.join(available_resources)}).
- Enhance creativity by seeking scientifically plausible connections between different concepts, subfields, or techniques relevant to answering the question.
"""

        # *** Prompt for Solution Generation ***
        # Includes request for novel proposal
        self.original_prompt_solution = f"""
Develop a detailed, scientifically sound, **novel,** and feasible research proposal to address the following specific astronomy research question:

**Research Question:**
"{research_question}"

**Develop the proposal sections for a {skill_level} graduate student with this profile:**
- Student interests: {', '.join(student_interests)}
- Time frame: {time_frame}
- Available resources: {', '.join(available_resources)}
- Skill level: {skill_level}
- Additional Student Context: {additional_context or "None provided."}

{condensed_guidelines}

**Output Format:**
Generate ONLY the content for the following sections. Adhere strictly to the required headings and content guidelines:

# [DESCRIPTIVE PROJECT TITLE]
IMPORTANT: Create a SPECIFIC, DESCRIPTIVE title for the project addressing the provided Research Question.

## Solution Summary
Begin with: "To answer this question, we will use the following approach:" followed by 2-3 clear sentences outlining the key steps of the solution. Be concise and rigorous.
Then in one sentence, explain the significance and impact of the proposed project by stating: "This project is impactful because...". Be concise and punchy. 

## Background
Provide 3-4 paragraphs explaining the context, significance, and knowledge gap related *specifically* to the Research Question. Why is this question important and timely?

## Methodology
Begin with: "To address the research question '{research_question}...', we will use the following approach:"
Provide a CONCISE methodology (3-4 paragraphs: Data Acquisition/Processing, Analysis Approach, Validation/Interpretation). Specify data sources, methods, tools, and ensure a logical flow feasible within the constraints.

## Expected Outcomes
Describe at least three concrete, measurable results expected from answering the Research Question. How do they contribute to solving the identified problem?

## Potential Challenges
List potential challenges specific to this project and briefly suggest mitigation strategies.

## Required Skills
List precise technical and knowledge-based skills needed, suggesting how they could be developed.

## Broader Connections
Explain how answering this Research Question connects to larger questions in astronomy/astrophysics.

**IMPORTANT:** Focus entirely on developing a scientifically sound and feasible proposal *for the given Research Question*. Ensure all sections directly relate to answering it.
"""
        print("--- Generating Solution Proposal ---")
        # print("Solution Prompt:", self.original_prompt_solution) # Optional: print prompt for debugging

        try:
            solution_text = self.llm_client.generate_content(self.original_prompt_solution)
            # Parse the generated text into sections
            return self._parse_proposal_sections(solution_text)
        except Exception as e:
            print(f"Error generating solution proposal: {str(e)}")
            # Return dict with error indication
            return {"title": "Error", "Background": f"Failed to generate proposal: {e}"}


    def _parse_proposal_sections(self, text: str) -> Dict[str, Any]:
        """Parses the LLM response containing the proposal sections."""
        parsed_output = {}
        sections = [
            "Solution Summary", "Background", "Methodology", "Expected Outcomes",
            "Potential Challenges", "Required Skills", "Broader Connections"
        ]
        current_section = None
        section_content = []

        # Extract Title first
        title = "Untitled Research Project" # Default
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # More robust title check - ensure it's not just a section header
            if line.startswith('# ') and not any(f'## {s.lower()}' in line.lower() for s in sections) and not line.lower().startswith('# background'):
                title = line.replace('# ', '').strip()
                lines = lines[i+1:] # Remove title line from further processing
                break
        parsed_output["title"] = title

        # Parse Sections
        for line in lines:
            stripped_line_lower = line.strip().lower()
            found_section = False
            for section_name in sections:
                if stripped_line_lower == f'## {section_name.lower()}':
                    if current_section and section_content:
                        parsed_output[current_section] = '\n'.join(section_content).strip()
                    current_section = section_name
                    section_content = []
                    found_section = True
                    break # Found the section header for this line

            if not found_section and current_section is not None:
                section_content.append(line)

        # Add the last section
        if current_section and section_content:
            parsed_output[current_section] = '\n'.join(section_content).strip()

        # Ensure all expected sections are present, add placeholders if missing
        for section in sections:
            if section not in parsed_output:
                parsed_output[section] = f"[Content for {section} not generated]"

        return parsed_output


    def _combine_question_solution(self, question_text: str, solution_dict: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Combines the generated question and solution into the final idea structure."""
        
        # Get the Solution Summary section 
        solution_summary = solution_dict.get("Solution Summary", "")
        
        # Clean up the solution summary
        clean_summary = self._extract_solution_summary(solution_summary)
        
        # Create a comprehensive Idea Summary following the structured format
        idea_summary = f"""Proposed question: {question_text.strip()}.
        
{clean_summary}
"""
        
        # Store the full idea content
        idea_content = {
            "Research Question": idea_summary.strip(),  # Use our comprehensive summary here
            "Background": solution_dict.get("Background", "[Missing Background]"),
            "Methodology": solution_dict.get("Methodology", "[Missing Methodology]"),
            "Expected Outcomes": solution_dict.get("Expected Outcomes", "[Missing Expected Outcomes]"),
            "Potential Challenges": solution_dict.get("Potential Challenges", "[Missing Potential Challenges]"),
            "Required Skills": solution_dict.get("Required Skills", "[Missing Required Skills]"),
            "Broader Connections": solution_dict.get("Broader Connections", "[Missing Broader Connections]")
        }
        
        final_idea = {
            "title": solution_dict.get("title", "Untitled Research Project"),
            "subfields": profile.get("student_interests", []),
            "skill_level": profile.get("skill_level", "beginner"),
            "time_frame": profile.get("time_frame", "1 year"),
            "resources_needed": profile.get("available_resources", []),
            "idea": idea_content,
            "version": 0  # Initial version
        }
        print("--- Final Idea ---")
        print(final_idea.get("idea").get("Research Question"))
        return final_idea
    
    def _extract_solution_summary(self, solution_summary: str) -> str:
        """Simple cleanup of the solution summary text."""

        # Remove any markdown formatting that might be present
        cleaned_summary = solution_summary.replace("#", "").strip()
        
        # Check if the summary starts with our expected format and clean it up
        if "to answer this question" in cleaned_summary.lower():
            # Replace the intro phrase with our standard format
            cleaned_summary = cleaned_summary.replace("To answer this question, we will use the following approach:", "Proposed solution:")
        
        return cleaned_summary
    
    # Remove the unused extraction functions
    def _extract_methodology_approach(self, methodology_text: str) -> str:
        """Extract the actual methodology approach, skipping the introductory sentence."""
        if not methodology_text:
            return "using appropriate methodologies and data analysis techniques"
        
        # Check if the text contains the templated intro sentence
        intro_markers = [
            "to address the research question", 
            "we will use the following approach",
            "will be addressed using",
            "will be investigated using"
        ]
        
        # Find where the introduction ends and the actual approach begins
        start_pos = 0
        found_intro = False
        
        # Look for the intro pattern, which typically ends with a colon
        for marker in intro_markers:
            if marker.lower() in methodology_text.lower():
                found_intro = True
                colon_pos = methodology_text.lower().find(":", methodology_text.lower().find(marker))
                if colon_pos > 0:
                    start_pos = colon_pos + 1
                    break
                
                # If no colon, try to find the end of the sentence
                period_pos = methodology_text.lower().find(".", methodology_text.lower().find(marker))
                if period_pos > 0:
                    start_pos = period_pos + 1
                    break
        
        # If we found an intro, get the text after it
        if found_intro and start_pos > 0:
            remaining_text = methodology_text[start_pos:].strip()
            
            # Get the first substantive sentence or paragraph
            if remaining_text:
                # Try to get the first paragraph
                paragraphs = remaining_text.split("\n\n")
                if len(paragraphs) > 0 and paragraphs[0].strip():
                    # Just get the first 1-2 sentences for brevity
                    sentences = paragraphs[0].split('.')
                    return self._format_first_sentences(sentences, 2)
                
                # If that failed, just get the first 1-2 sentences
                sentences = remaining_text.split('.')
                return self._format_first_sentences(sentences, 2)
        
        # Fallback: If we couldn't extract properly, try to get the second paragraph which likely has substance
        paragraphs = methodology_text.split("\n\n")
        if len(paragraphs) > 1 and paragraphs[1].strip():
            sentences = paragraphs[1].split('.')
            return self._format_first_sentences(sentences, 2)
        
        # Further fallback: Get any substantive content from the entire methodology
        sentences = methodology_text.split('.')
        # Skip any sentence with the introductory text
        content_sentences = [s.strip() for s in sentences if s.strip() and not any(marker.lower() in s.lower() for marker in intro_markers)]
        if content_sentences:
            return self._format_first_sentences(content_sentences, 2)
        
        # Last resort fallback
        return "using appropriate methodologies and data analysis techniques specific to this research context"
    
    def _extract_importance_statement(self, broader_connections_text: str) -> str:
        """Extract a meaningful statement about the importance of the research."""
        if not broader_connections_text:
            return "it will contribute to our understanding of astronomical phenomena and may have broader implications for the field"
        
        # Look for key phrases indicating importance
        importance_markers = [
            "important because", 
            "significance of", 
            "impact on",
            "contribute to",
            "advances our",
            "enhances understanding",
            "addresses key"
        ]
        
        # Find a sentence containing an importance marker
        sentences = broader_connections_text.split('.')
        for sentence in sentences:
            if any(marker.lower() in sentence.lower() for marker in importance_markers):
                return sentence.strip().lower()
        
        # If no explicit importance sentence found, use the first sentence
        if sentences and sentences[0].strip():
            return sentences[0].strip().lower()
        
        # Fallback
        return "it will contribute to our understanding of astronomical phenomena and may have broader implications for the field"
    
    def _format_first_sentences(self, sentences: List[str], num_sentences: int) -> str:
        """Format the first few sentences into a readable text."""
        result_sentences = []
        
        for sentence in sentences:
            if sentence.strip() and len(result_sentences) < num_sentences:
                result_sentences.append(sentence.strip())
        
        if not result_sentences:
            return "using appropriate methodologies and data analysis techniques"
        
        # Combine the sentences and make sure the result starts lowercase (for insertion into a larger sentence)
        result = '. '.join(result_sentences)
        if result.endswith('.'):
            result = result[:-1]  # Remove the trailing period
            
        if result and not result.endswith('.'):
            result += ''  # Ensure no trailing period
            
        return result.lower() if result else "using appropriate methodologies and data analysis techniques"


    # --- Methods below are largely unchanged from original idea_agent.py ---
    # --- They might need adjustments if the structure/flow changes significantly ---

    def improve_idea(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Improve the current idea based on expert feedback and optional literature insights."""
        if not self.current_idea:
            raise ValueError("No current idea exists. Generate an initial idea first.")

        # Track feedback history
        self.feedback_history.append(feedback)
        self.improvement_count += 1

        # Extract feedback components (copied from original idea_agent.py)
        scientific_concerns = []
        methodological_concerns = []
        recommendations = []
        summary = ""
        if isinstance(feedback, dict):
            scientific_dict = feedback.get("scientific_validity", {})
            if isinstance(scientific_dict, dict): scientific_concerns = scientific_dict.get("concerns", [])
            methodology_dict = feedback.get("methodology", {})
            if isinstance(methodology_dict, dict): methodological_concerns = methodology_dict.get("concerns", [])
            recommendations = feedback.get("recommendations", [])
            summary = feedback.get("summary", "")

        literature_insights = feedback.get("literature_insights", {})
        literature_recommendations = []
        novel_suggestions = []
        emerging_trends = ""
        novelty_score = 0
        literature_summary = ""
        if literature_insights:
             literature_recommendations = literature_insights.get("recommended_improvements", [])
             novel_suggestions = literature_insights.get("differentiation_suggestions", [])
             emerging_trends = literature_insights.get("emerging_trends", "")
             literature_summary = literature_insights.get("summary", "")
             novelty_score = literature_insights.get("novelty_score", 0)

        # Format concerns and recommendations (copied from original idea_agent.py)
        scientific_concerns_text = "\n".join([f"- {concern}" for concern in scientific_concerns])
        methodological_concerns_text = "\n".join([f"- {concern}" for concern in methodological_concerns])
        recommendations_text = "\n".join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)])
        literature_recommendations_text = "\n".join([f"- {rec}" for rec in literature_recommendations])
        novel_suggestions_text = "\n".join([f"- {suggestion}" for suggestion in novel_suggestions])

        original_research_question = self.current_idea['idea'].get('Research Question', '')

        # *** Create improvement prompt ***
        # Kept similar to original, but emphasizes addressing feedback for the *original question*
        improvement_prompt = f"""
    You are an astronomy researcher revising your research proposal based on expert feedback and literature review.

    YOUR ORIGINAL PROPOSAL:
    Title: "{self.current_idea['title']}"
    Research Question: "{original_research_question}" # This is the initially generated question
    Background: {self.current_idea['idea'].get('Background', '')}
    Methodology: {self.current_idea['idea'].get('Methodology', '')}
    # ... (include other original sections if helpful) ...

    EXPERT FEEDBACK TO ADDRESS (relative to the original proposal):
    Scientific Validity Concerns: {scientific_concerns_text or "None"}
    Methodological Concerns: {methodological_concerns_text or "None"}
    Expert Recommendations: {recommendations_text or "None"}
    Overall Assessment: {summary or "N/A"}
    """
        # Add literature review section if available
        if literature_insights:
            improvement_prompt += f"""
    LITERATURE REVIEW INSIGHTS (relative to the original proposal):
    Novelty Assessment (Score: {novelty_score}/10): {literature_insights.get('novelty_assessment', '')}
    Innovation Opportunities: {novel_suggestions_text or "None"}
    Emerging Research Trends: {emerging_trends or "None"}
    Novelty Recommendations: {literature_recommendations_text or "None"}
    Literature Summary: {literature_summary or "N/A"}
    """

        # Add instructions (tweaked based on previous discussion)
        improvement_prompt += f"""
    INSTRUCTIONS:
    Create an improved version of the research proposal sections (Background, Methodology, etc.) that addresses ALL feedback provided above (scientific, methodological, expert recommendations, and literature/novelty insights).
    The goal is to refine the approach for answering the **original Research Question:** "{original_research_question}".
    Ensure the revised proposal is scientifically sound, feasible for the student profile ({self.student_profile['skill_level']}, {self.student_profile['time_frame']}, {', '.join(self.student_profile['available_resources'])}), and enhances novelty where possible.

    Your response MUST follow this exact format:

    # [Create a specific improved title here - NOT a placeholder]

    ## Research Question
    "{original_research_question}" # Reiterate the original question EXACTLY.

    ## Background
    [Improved background addressing feedback]

    ## Methodology
    [Improved methodology addressing feedback and feasibility]

    ## Expected Outcomes
    [Improved expected outcomes]

    ## Potential Challenges
    [Improved potential challenges]

    ## Required Skills
    [Improved required skills]

    ## Broader Connections
    [Improved broader connections]
    """

        # Generate the improved idea
        improved_idea_text = self.llm_client.generate_content(improvement_prompt)

        # --- Parse the improved idea ---
        # Re-using parsing logic, ensuring Research Question is not overwritten
        parsed_improved_idea = {}
        sections = [
            "Research Question", "Background", "Methodology", "Expected Outcomes",
            "Potential Challenges", "Required Skills", "Broader Connections"
        ]
        current_section = None
        section_content = []

        # Extract Title first
        title = ""
        lines = improved_idea_text.split('\n')
        for i, line in enumerate(lines):
             if line.startswith('# ') and not line.lower().startswith('# research question'):
                  title = line.replace('# ', '').strip()
                  lines = lines[i+1:]
                  break
        if not title or title.startswith("[Create a specific improved title"): title = f"Improved: {self.current_idea['title']}"
        # Assign title directly to the idea being updated
        self.current_idea['title'] = title


        # Parse Sections, storing content temporarily
        temp_parsed_sections = {}
        for line in lines:
            stripped_line_lower = line.strip().lower()
            found_section = False
            for section_name in sections:
                 # Handle potential variations like "## Research Question" vs "## research question"
                 if stripped_line_lower == f'## {section_name.lower()}':
                      if current_section and section_content:
                           temp_parsed_sections[current_section] = '\n'.join(section_content).strip()
                      current_section = section_name
                      section_content = []
                      found_section = True
                      break
            if not found_section and current_section is not None:
                 section_content.append(line)

        # Add the last parsed section
        if current_section and section_content:
            temp_parsed_sections[current_section] = '\n'.join(section_content).strip()


        # Update self.current_idea['idea'] carefully, preserving original question
        for section in sections:
            if section == "Research Question":
                # Always keep the original question from self.current_idea
                self.current_idea['idea'][section] = original_research_question
            elif section in temp_parsed_sections and temp_parsed_sections[section]:
                # Update with newly generated content if available
                self.current_idea['idea'][section] = temp_parsed_sections[section]
            # else: keep the potentially existing content from self.current_idea['idea'] if LLM failed to generate

        # Update version number
        self.current_idea["version"] = self.improvement_count

        return self.current_idea


    def improve_idea_with_user_feedback(self, user_feedback: str) -> Dict[str, Any]:
        """Improve the current idea based on direct user feedback. (Adapted for two-call structure)"""
        if not self.current_idea:
            raise ValueError("No current idea exists. Generate an initial idea first.")

        self.improvement_count += 1
        original_research_question = self.current_idea['idea'].get('Research Question', '')

        # Prompt using user feedback
        improvement_prompt = f"""
    You are an astronomy researcher revising your research proposal based on direct user feedback.

    YOUR ORIGINAL PROPOSAL SECTIONS (to answer the Research Question below):
    Title: "{self.current_idea['title']}"
    Background: {self.current_idea['idea'].get('Background', '')}
    Methodology: {self.current_idea['idea'].get('Methodology', '')}
    # ... (Include other sections if helpful) ...

    RESEARCH QUESTION (This should NOT be changed):
    "{original_research_question}"

    USER FEEDBACK TO ADDRESS (Apply this feedback to the proposal sections like Background, Methodology, etc.):
    {user_feedback}

    INSTRUCTIONS:
    Create an improved version of the proposal sections (Background, Methodology, etc.) addressing the user's feedback, while maintaining scientific rigor and feasibility for the student profile ({self.student_profile['skill_level']}, {self.student_profile['time_frame']}, {', '.join(self.student_profile['available_resources'])}). The goal is to refine the approach for answering the **original Research Question**.

    Your response MUST follow this exact format:
    # [Create a specific improved title here - NOT a placeholder]
    ## Research Question
    "{original_research_question}" # Reiterate original question EXACTLY.
    ## Background
    [Improved background addressing user feedback]
    ## Methodology
    [Improved methodology addressing user feedback]
    # ... (Other sections: Expected Outcomes, Potential Challenges, Required Skills, Broader Connections) ...
    """

        improved_idea_text = self.llm_client.generate_content(improvement_prompt)

        # --- Parse the improved idea (using similar logic as improve_idea) ---
        temp_parsed_sections = {}
        sections = [
            "Research Question", "Background", "Methodology", "Expected Outcomes",
            "Potential Challenges", "Required Skills", "Broader Connections"
        ]
        current_section = None
        section_content = []

        # Extract Title
        title = ""
        lines = improved_idea_text.split('\n')
        for i, line in enumerate(lines):
             if line.startswith('# ') and not line.lower().startswith('# research question'):
                  title = line.replace('# ', '').strip()
                  lines = lines[i+1:]
                  break
        if not title or title.startswith("[Create a specific improved title"): title = f"Improved: {self.current_idea['title']}"
        self.current_idea['title'] = title

        # Parse Sections
        for line in lines:
            stripped_line_lower = line.strip().lower()
            found_section = False
            for section_name in sections:
                if stripped_line_lower == f'## {section_name.lower()}':
                    if current_section and section_content:
                        temp_parsed_sections[current_section] = '\n'.join(section_content).strip()
                    current_section = section_name
                    section_content = []
                    found_section = True
                    break
            if not found_section and current_section is not None:
                 section_content.append(line)

        # Add last section
        if current_section and section_content:
            temp_parsed_sections[current_section] = '\n'.join(section_content).strip()

        # Update self.current_idea['idea'] carefully, preserving original question
        for section in sections:
            if section == "Research Question":
                self.current_idea['idea'][section] = original_research_question
            elif section in temp_parsed_sections and temp_parsed_sections[section]:
                self.current_idea['idea'][section] = temp_parsed_sections[section]
            # else: keep existing content if LLM failed to generate

        self.current_idea["version"] = self.improvement_count

        return self.current_idea


# Main execution block for testing
if __name__ == "__main__":
    print("EXAMPLE USING TWO-CALL AGENT (requires valid API key/provider setup)")
    try:
        # --- Replace with your actual API key setup ---
        # Example: Using Google (requires config.py with google_key)
        try:
            from config import google_key
            api_key = google_key
            provider = "google"
        except ImportError:
             print("ERROR: Could not import google_key from config.py. Please ensure config.py exists and contains the key.")
             exit()
        # --- End API key setup ---


        idea_agent = IdeaAgentTwoCalls(api_key=api_key, provider=provider)

        student_profile = {
            "student_interests": ["Observational Cosmology", "Galaxy Formation and Evolution"],
            "skill_level": "intermediate",
            "time_frame": "3 years",
            "available_resources": ["Public datasets (SDSS, DES)", "University computing cluster"],
            #"additional_context": "Interested in weak lensing techniques." # Example context
            "additional_context": "" # Example: No specific context provided
        }

        print("\nGENERATING INITIAL IDEA (TWO-CALL PROCESS):")
        initial_idea = idea_agent.generate_initial_idea(**student_profile)
        print("\n--- FINAL COMBINED IDEA ---")
        print(json.dumps(initial_idea, indent=2))

        # Example of improvement (using dummy feedback)
        sample_feedback = {
            "scientific_validity": {"concerns": ["Selection bias in sample not fully addressed."]},
            "methodology": {"concerns": ["Assumed cosmology might affect results.", "Error propagation needs detail."]},
            "recommendations": ["Implement stricter sample selection.", "Test sensitivity to cosmological parameters.", "Detail error analysis."],
            "summary": "Solid foundation, needs refinement on selection and error handling."
        }

        print("\nIMPROVING IDEA BASED ON FEEDBACK:")
        improved_idea = idea_agent.improve_idea(sample_feedback)
        print("\n--- IMPROVED IDEA ---")
        print(json.dumps(improved_idea, indent=2))

    except Exception as e:
        import traceback
        print(f"\nAn error occurred during execution: {e}")
        print(traceback.format_exc())