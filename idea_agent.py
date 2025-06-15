import os
import json
import random
from typing import List, Dict, Any, Optional
# from config import *
from subfields import AstronomySubfield, ASTRONOMY_SUBFIELDS

# from anthropic import Anthropic
# Removed unused genai import

import streamlit as st

# Import the LLMClient wrapper
from llm_client import LLMClient

# Removed duplicate genai import attempt

class IdeaAgent:
    """Stateful agent that generates and improves astronomy research ideas."""
    def __init__(self, api_key, provider="azure"):
        self.api_key = api_key # Keep api_key for potential future use if needed directly
        self.provider = provider
        
        # Initialize the LLM client with the appropriate provider
        try:
            self.llm_client = LLMClient(api_key, provider)
        except ValueError as e:
            raise ValueError(f"Error initializing idea agent: {str(e)}")
                
        # Removed unused self.original_prompt
        self.current_idea = None
        self.student_profile = None
        self.feedback_history = []
        self.improvement_count = 0
    
    def structure_and_rephrase_idea(
        self,
        user_idea: str,
        student_interests: Optional[List[str]] = None,
        skill_level: str = "beginner",
        time_frame: str = "1 year",
        available_resources: Optional[List[str]] = None,
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """
        Takes a user's raw idea and structures it into a formal research proposal.
        """
        self.student_profile = {
            "student_interests": student_interests,
            "skill_level": skill_level,
            "time_frame": time_frame,
            "available_resources": available_resources,
            "additional_context": additional_context
        }

        prompt = f"""
You are an expert astronomy research advisor. A student has come to you with a research idea. Your task is to take their raw input and rephrase it into a structured, coherent, and scientifically sound research proposal concept.

**DO NOT INVENT A NEW IDEA.** Your sole purpose is to clarify, structure, and formalize the student's existing idea based *only* on the information they have provided.

**Student's Raw Idea:**
"{user_idea}"

**Student's Context:**
- Interests: {', '.join(student_interests) if student_interests else 'Not specified'}
- Skill Level: {skill_level}
- Time Frame: {time_frame}
- Available Resources: {', '.join(available_resources) if available_resources else 'Not specified'}
- Additional Context: {additional_context}

Based on the student's idea and context, please structure it into the following JSON format. Fill in each field by interpreting their request. If their idea is vague, make reasonable, scientifically-grounded inferences to fill out the sections, but clearly state that you are making an assumption.

Your response MUST be a single JSON object.

{{
  "title": "[Create a concise, descriptive title for the research project based on the user's idea]",
  "subfields": ["Identify the most relevant astronomy subfields (e.g., 'Exoplanet Atmospheres', 'Cosmology', 'Stellar Astrophysics')"],
  "skill_level": "{skill_level}",
  "time_frame": "{time_frame}",
  "idea": {{
    "Research Question": "[Based on the user's idea, formulate a single, clear, and testable research question. If the user's idea is a statement, turn it into a question.]",
    "Background": "[Provide 1-2 paragraphs of background context. Explain why the user's question is scientifically interesting and relevant. If possible, mention what makes it timely.]",
    "Methodology": "[Propose a high-level, 2-3 step methodology appropriate for the skill level and resources. For example: 1. Data Acquisition (mentioning a plausible public dataset like SDSS, Gaia, TESS). 2. Analysis (mentioning a plausible technique like photometry, spectroscopy, or statistical analysis). 3. Interpretation.]",
    "Expected Outcomes": "[Describe 2-3 potential, concrete outcomes from this research. What would be the tangible result? (e.g., a catalog of objects, a measurement of a parameter, a confirmation of a theory).]",
    "Potential Challenges": "[List 1-2 key challenges the student might face (e.g., 'Data quality may be a concern', 'Distinguishing signal from noise could be difficult').]",
    "Required Skills": "[List key skills needed, aligned with the methodology (e.g., 'Python programming (pandas, astropy)', 'Basic data analysis', 'Understanding of stellar evolution').]"
  }},
  "resources_needed": ["List the specific resources from the user's context that would be needed for this project."]
}}
"""
        
        try:
            response_text = self.llm_client.generate(prompt)
            # Clean the response to ensure it's valid JSON
            json_response = self.llm_client.extract_json(response_text)
            self.current_idea = json_response
            return self.current_idea
        except Exception as e:
            print(f"An error occurred while structuring the idea: {e}")
            # In case of a failure, return a structured error message
            return {
                "error": "Failed to structure the research idea.",
                "details": str(e)
            }
    
    def improve_idea(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Improve the current idea based on expert feedback and optional literature insights."""
        if not self.current_idea:
            raise ValueError("No current idea exists. Generate an initial idea first.")
        
        # Track feedback history
        self.feedback_history.append(feedback)
        self.improvement_count += 1
        
        # Extract feedback components
        scientific_concerns = []
        methodological_concerns = []
        recommendations = []
        summary = ""
        
        # Handle different feedback formats
        if isinstance(feedback, dict):
            # Extract from dictionary structure
            scientific_dict = feedback.get("scientific_validity", {})
            if isinstance(scientific_dict, dict):
                scientific_concerns = scientific_dict.get("concerns", [])
            
            methodology_dict = feedback.get("methodology", {})
            if isinstance(methodology_dict, dict):
                methodological_concerns = methodology_dict.get("concerns", [])
            
            recommendations = feedback.get("recommendations", [])
            summary = feedback.get("summary", "")
        
        # Check for literature insights (new)
        literature_insights = feedback.get("literature_insights", {})
        literature_recommendations = []
        literature_summary = ""
        novel_suggestions = []
        emerging_trends = ""
        novelty_score = 0
        
        if literature_insights:
            literature_recommendations = literature_insights.get("recommended_improvements", [])
            novel_suggestions = literature_insights.get("differentiation_suggestions", [])
            emerging_trends = literature_insights.get("emerging_trends", "")
            literature_summary = literature_insights.get("summary", "")
            novelty_score = literature_insights.get("novelty_score", 0)
        
        # Format the concerns and recommendations for the prompt
        scientific_concerns_text = "\n".join([f"- {concern}" for concern in scientific_concerns])
        methodological_concerns_text = "\n".join([f"- {concern}" for concern in methodological_concerns])
        recommendations_text = "\n".join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)])
        
        # Format literature feedback (new)
        literature_recommendations_text = "\n".join([f"- {rec}" for rec in literature_recommendations])
        novel_suggestions_text = "\n".join([f"- {suggestion}" for suggestion in novel_suggestions])
        
        # Get the original research question format for reference
        original_research_question = self.current_idea['idea'].get('Research Question', '')
        
        # Create improvement prompt that includes original context and literature insights
        improvement_prompt = f"""
    You are an astronomy researcher revising your research proposal based on expert feedback and literature review.

    YOUR ORIGINAL PROPOSAL:
    Title: "{self.current_idea['title']}"

    Research Question:
    {original_research_question}

    Background:
    {self.current_idea['idea'].get('Background', '')}

    Methodology:
    {self.current_idea['idea'].get('Methodology', '')}

    Expected Outcomes:
    {self.current_idea['idea'].get('Expected Outcomes', '')}

    Potential Challenges:
    {self.current_idea['idea'].get('Potential Challenges', '')}

    EXPERT FEEDBACK TO ADDRESS:

    Scientific Validity Concerns:
    {scientific_concerns_text}

    Methodological Concerns:
    {methodological_concerns_text}

    Expert Recommendations:
    {recommendations_text}

    Overall Assessment:
    {summary}
    """

        # Add literature review section if available
        if literature_insights:
            improvement_prompt += f"""
    LITERATURE REVIEW INSIGHTS:

    Novelty Assessment (Score: {novelty_score}/10):
    {literature_insights.get('novelty_assessment', '')}

    Innovation Opportunities:
    {novel_suggestions_text}

    Emerging Research Trends:
    {emerging_trends}

    Novelty Recommendations:
    {literature_recommendations_text}

    Literature Summary:
    {literature_summary}
    """

        # Add instructions
        improvement_prompt += f"""
    INSTRUCTIONS:

    Create an improved version of your research proposal that:
    1. Maintains your original research direction but addresses ALL identified scientific concerns
    2. Fixes the methodological issues while keeping the project feasible
    3. Incorporates the expert recommendations
    """

        # Add novelty-specific instructions if literature review was performed
        if literature_insights:
            improvement_prompt += """
    4. Enhances novelty based on the **expert's synthesized novelty assessment and recommendations**
    5. Positions your work clearly with respect to the existing literature
    """

        improvement_prompt += f"""
    {4 if not literature_insights else 6}. Ensures claims are proportional to what methods can actually measure
    {5 if not literature_insights else 7}. Is appropriate for your skill level ({self.student_profile['skill_level']}) within your timeframe ({self.student_profile['time_frame']})
    {6 if not literature_insights else 8}. Uses only the available resources: {', '.join(self.student_profile['available_resources'])}

    Keep the research question direct and concise!

    Your response MUST follow this exact format:

    # [Create a specific improved title here - NOT a placeholder]

    ## Research Question
    "In this project, we aim to [solve problem/achieve goal] by [summary of solution]."

    Then break down the proposed project into a 2-3 key steps, following rigorous scientific methodology. Format this as:
    "Specifically, we will first [first step], then we will [second step]. Finally, we will [final step] to [obtain result/achieve goal]."

    IMPORTANT: Explicitly state the specific problem or gap in knowledge this research aims to solve. Format this as:
    "This research addresses the problem of [specific problem statement], which is currently unresolved because [reasons for knowledge gap]."

    Finally, explain why the proposed method is best-suited for the problem. Format this as:
    "The proposed method is best-suited for the problem because [specific advantages of approach]."

    [Additional context and importance of the research, addressing the scientific concerns raised in the feedback]

    ## Background
    [Improved background]

    ## Methodology
    Begin with: "To address the problem of [restate the specific problem], we will use the following approach:"

    Provide a CONCISE methodology in 3-4 paragraphs that follows a clear logical flow. Each paragraph should focus on a distinct phase of the research:

    Paragraph 1: Data Acquisition and Processing
    - Specify exact data sources (survey names, telescope facilities, or dataset identifiers)
    - Describe initial data selection criteria and preprocessing steps

    Paragraph 2: Analysis Approach
    - Outline the core analytical methods in a logical sequence
    - Specify software tools and programming languages to be used
    - Explain how these methods directly connect to answering the research question

    Paragraph 3: Validation and Interpretation
    - Describe how results will be validated (e.g., statistical tests, comparison with models)
    - Explain how potential biases or limitations will be addressed
    - Briefly outline how results will be interpreted in the context of the research question

    Optional Paragraph 4: Timeline
    - Provide a brief timeline showing how these steps will be completed within the {self.student_profile['time_frame']}

    IMPORTANT: Maintain a clear logical flow between steps. Each step should naturally lead to the next, forming a coherent research pipeline. Avoid excessive technical details that obscure the overall approach.

    ## Expected Outcomes
    [Improved expected outcomes]

    ## Potential Challenges
    [Improved potential challenges]

    ## Required Skills
    [Improved required skills]

    ## Broader Connections
    [Improved broader connections]

    Make sure your revised proposal is scientifically accurate, methodologically sound, feasible, and novel.
    """
            
        # Generate the improved idea
        improved_idea_text = self.llm_client.generate_content(improvement_prompt)
        
        # Parse the improved idea
        sections = [
            "Research Question",
            "Background",
            "Methodology",
            "Expected Outcomes",
            "Potential Challenges",
            "Required Skills",
            "Broader Connections"
        ]
        
        # Extract the title with better fallback handling
        title = ""
        for line in improved_idea_text.split('\n'):
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                break
        
        # Fallback if title is missing or a placeholder
        if not title or title == "[Create a specific improved title here - NOT a placeholder]" or title == "IMPROVED PROJECT TITLE":
            # Use original title with "Improved" prefix if no valid title found
            title = f"Improved: {self.current_idea['title']}"
        
        # Parse sections
        parsed_idea = {}
        current_section = None
        section_content = []
        
        for line in improved_idea_text.split('\n'):
            if line.startswith('# '):
                continue
                
            if line.startswith('## '):
                section_name = line.replace('## ', '').strip()
                if current_section and section_content:
                    parsed_idea[current_section] = '\n'.join(section_content).strip()
                current_section = section_name
                section_content = []
            elif current_section is not None:
                section_content.append(line)
        
        # Add the last section
        if current_section and section_content:
            parsed_idea[current_section] = '\n'.join(section_content).strip()
        
        # Ensure all required sections exist
        for section in sections:
            if section not in parsed_idea:
                # Copy from original idea if possible, otherwise use placeholder
                if section in self.current_idea.get('idea', {}):
                    parsed_idea[section] = self.current_idea['idea'][section]
                else:
                    parsed_idea[section] = f"[Improved {section.lower()} - content preserved from original]"
        
        # Update the current idea
        self.current_idea = {
            "title": title,
            "subfields": self.current_idea.get("subfields", []),
            "skill_level": self.student_profile.get("skill_level", ""),
            "time_frame": self.student_profile.get("time_frame", ""),
            "resources_needed": self.student_profile.get("available_resources", []),
            "idea": parsed_idea,
            "version": self.improvement_count
        }
        
        return self.current_idea

    def improve_idea_with_user_feedback(self, user_feedback: str) -> Dict[str, Any]:
        """Improve the current idea based on direct user feedback."""
        if not self.current_idea:
            raise ValueError("No current idea exists. Generate an initial idea first.")
        
        # Track that we're using user feedback
        self.improvement_count += 1
        
        # Get the original research idea components
        original_research_question = self.current_idea['idea'].get('Research Question', '')
        
        # Create improvement prompt that includes original idea and user feedback
        improvement_prompt = f"""
    You are an astronomy researcher revising your research proposal based on direct user feedback.

    YOUR ORIGINAL PROPOSAL:
    Title: "{self.current_idea['title']}"

    Research Question:
    {original_research_question}

    Background:
    {self.current_idea['idea'].get('Background', '')}

    Methodology:
    {self.current_idea['idea'].get('Methodology', '')}

    Expected Outcomes:
    {self.current_idea['idea'].get('Expected Outcomes', '')}

    Potential Challenges:
    {self.current_idea['idea'].get('Potential Challenges', '')}

    USER FEEDBACK TO ADDRESS:
    {user_feedback}

    INSTRUCTIONS:

    Create an improved version of your research proposal that:
    1. Maintains your original research direction but addresses the user's feedback
    2. Ensures the methodology is sound and the project is feasible
    3. Keeps the research focused and scientifically rigorous
    4. Ensures claims are proportional to what methods can actually measure
    5. Is appropriate for your skill level ({self.student_profile['skill_level']}) within your timeframe ({self.student_profile['time_frame']})
    6. Uses only the available resources: {', '.join(self.student_profile['available_resources'])}

    Keep the research question direct and concise!

    Your response MUST follow this exact format:

    # [Create a specific improved title here - NOT a placeholder]

    ## Research Question
    "In this project, we aim to [solve problem/achieve goal] by [summary of solution]."

    Then break down the proposed project into a 2-3 key steps, following rigorous scientific methodology. Format this as:
    "Specifically, we will first [first step], then we will [second step]. Finally, we will [final step] to [obtain result/achieve goal]."

    IMPORTANT: Explicitly state the specific problem or gap in knowledge this research aims to solve. Format this as:
    "This research addresses the problem of [specific problem statement], which is currently unresolved because [reasons for knowledge gap]."

    Finally, explain why the proposed method is best-suited for the problem. Format this as:
    "The proposed method is best-suited for the problem because [specific advantages of approach]."

    [Additional context and importance of the research, addressing the user's feedback]

    ## Background
    [Improved background]

    ## Methodology
    Begin with: "To address the problem of [restate the specific problem], we will use the following approach:"

    [Improved methodology that addresses the user's feedback]

    ## Expected Outcomes
    [Improved expected outcomes]

    ## Potential Challenges
    [Improved potential challenges]

    ## Required Skills
    [Improved required skills]

    ## Broader Connections
    [Improved broader connections]

    Make sure your revised proposal is scientifically accurate, methodologically sound, feasible, and addresses all aspects of the user's feedback.
    """
            
        # Generate the improved idea
        improved_idea_text = self.llm_client.generate_content(improvement_prompt)
        
        # Parse the improved idea using the same parsing logic as in improve_idea
        sections = [
            "Research Question",
            "Background",
            "Methodology",
            "Expected Outcomes",
            "Potential Challenges",
            "Required Skills",
            "Broader Connections"
        ]
        
        parsed_idea = {}
        current_section = None
        section_content = []
        
        # Extract the title first (should be on the first line with # prefix)
        title = ""
        for line in improved_idea_text.split('\n'):
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                break
        
        # Now parse the rest of the content
        for line in improved_idea_text.split('\n'):
            # Skip the title line we already processed
            if line.startswith('# '):
                continue
                
            # Check if line starts a new section
            new_section = False
            
            if line.startswith('## '):
                section_name = line.replace('## ', '').strip()
                if section_name in sections:
                    if current_section and section_content:
                        parsed_idea[current_section] = '\n'.join(section_content).strip()
                    current_section = section_name
                    section_content = []
                    new_section = True
            
            if not new_section and current_section is not None:
                section_content.append(line)
        
        # Add the last section
        if current_section and section_content:
            parsed_idea[current_section] = '\n'.join(section_content).strip()
        
        # Create the improved idea with the same structure as the original
        improved_idea = {
            "title": title if title else "Improved Research Project",
            "subfields": self.current_idea.get("subfields", []),
            "skill_level": self.current_idea.get("skill_level", "beginner"),
            "time_frame": self.current_idea.get("time_frame", "1 year"),
            "resources_needed": self.current_idea.get("resources_needed", []),
            "idea": parsed_idea
        }
        
        # Update the current idea to the improved version
        self.current_idea = improved_idea
        
        return improved_idea

if __name__ == "__main__":
    # Example usage
    student_profile = {
        "student_interests": ["Observational Cosmology", "Galaxy Formation and Evolution"],
        "skill_level": "beginner",
        "time_frame": "2 years",
        "available_resources": ["Public datasets", "Large telescope time via hosting institution", "University computing cluster"]
    }
    
    # Example using the original function
    print("GENERATING IDEA USING FUNCTION:")
    research_idea = generate_research_idea(**student_profile)
    print(json.dumps(research_idea, indent=2))
    
    # Example using the new stateful agent
    print("\nGENERATING IDEA USING STATEFUL AGENT:")
    idea_agent = IdeaAgent()
    initial_idea = idea_agent.structure_and_rephrase_idea(**student_profile)
    print(json.dumps(initial_idea, indent=2))
    
    # Example of improvement (would normally come from a reflection agent)
    sample_feedback = {
        "scientific_validity": {
            "concerns": [
                "The proposed method may not have sufficient sensitivity to detect the claimed features",
                "The relationship between the observed quantities and the inferred properties is not clearly established"
            ]
        },
        "methodology": {
            "concerns": [
                "The data processing pipeline is underspecified",
                "The validation approach doesn't account for systematic errors"
            ]
        },
        "recommendations": [
            "Focus on a smaller sample with deeper observations",
            "Add a detailed error analysis section",
            "Use simulations to validate the methodology"
        ],
        "summary": "This proposal has potential but needs refinement in methodology and more realistic expectations about what can be measured."
    }
    
    print("\nIMPROVING IDEA BASED ON FEEDBACK:")
    improved_idea = idea_agent.improve_idea(sample_feedback)
    print(json.dumps(improved_idea, indent=2))