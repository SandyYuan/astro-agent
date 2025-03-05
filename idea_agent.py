import os
import json
import random
from typing import List, Dict, Any, Optional
# from config import *
from subfields import AstronomySubfield, ASTRONOMY_SUBFIELDS

# from anthropic import Anthropic
from google import genai

# client = Anthropic(api_key=anthropic_key)    
# client = genai.Client(api_key=google_key)

import streamlit as st

# Import the LLMClient wrapper
from llm_client import LLMClient

# Try to import Google's genai library for backward compatibility
try:
    from google import genai
except ImportError:
    genai = None

class IdeaAgent:
    """Stateful agent that generates and improves astronomy research ideas."""
    def __init__(self, api_key, provider="azure"):
        self.api_key = api_key
        self.provider = provider
        
        # Initialize the LLM client with the appropriate provider
        self.llm_client = LLMClient(api_key, provider)
                
        self.original_prompt = None
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
        """Generate initial research idea based on student profile."""
        # Store student profile
        self.student_profile = {
            "student_interests": student_interests or [random.choice(ASTRONOMY_SUBFIELDS).name],
            "skill_level": skill_level,
            "time_frame": time_frame,
            "available_resources": available_resources or ["Public astronomical datasets", "University computing cluster"],
            "additional_context": additional_context
        }
        
        # Use the existing client to generate the research idea
        self.current_idea = generate_research_idea(
            api_key=self.api_key,
            client=self.llm_client,  # Pass the existing client instance
            student_interests=student_interests,
            skill_level=skill_level,
            time_frame=time_frame,
            available_resources=available_resources,
            additional_context=additional_context
        )
        
        return self.current_idea
    
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
    4. Enhances novelty by incorporating differentiation suggestions and emerging trends
    5. Positions your work clearly with respect to the existing literature
    """

        improvement_prompt += f"""
    {4 if not literature_insights else 6}. Ensures claims are proportional to what methods can actually measure
    {5 if not literature_insights else 7}. Is appropriate for your skill level ({self.student_profile['skill_level']}) within your timeframe ({self.student_profile['time_frame']})
    {6 if not literature_insights else 8}. Uses only the available resources: {', '.join(self.student_profile['available_resources'])}

    CRITICAL FORMAT REQUIREMENTS:
    1. The Research Question must follow the same format as the original, beginning with "In this project, we will use..." 
    DO NOT phrase it as an interrogative question starting with "How" or "What"
    2. Keep the research question direct and concise
    3. Maintain the same structure but improve the content to address the feedback

    Your response MUST follow this exact format:

    # [Create a specific improved title here - NOT a placeholder]

    ## Research Question
    "In this project, we will use [specific data sets/observations] and [specific methods/tools/techniques] to [clear research objective - what will be measured, detected, or analyzed]."

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

def generate_research_idea(
    api_key: str,
    client: Optional[Any] = None,  # Add client parameter
    student_interests: Optional[List[str]] = None,
    skill_level: str = "beginner",
    time_frame: str = "2-3 years",
    available_resources: Optional[List[str]] = None,
    additional_context: str = "",
    provider: str = "azure"  # Add provider parameter with default to Azure
) -> Dict[str, Any]:
    """
    Generate a tailored astronomy research idea for a graduate student.
    
    Args:
        api_key: API key for the selected provider
        client: Optional existing client instance
        student_interests: List of astronomy topics the student is interested in
        skill_level: Student's current skill level (beginner, intermediate, advanced)
        time_frame: Expected duration of the research project
        available_resources: Equipment, datasets, or collaborations available
        additional_context: Additional information about the student's background and interests
        provider: Model provider to use ('azure' or 'google')
        
    Returns:
        A dictionary containing the research idea and supporting information
    """
    # Use the provided client or create a new one if not provided
    if client is None:
        client = LLMClient(api_key, provider)
    
    # Default values if none provided
    if student_interests is None:
        student_interests = [random.choice(ASTRONOMY_SUBFIELDS).name]
    
    if available_resources is None:
        available_resources = ["Public astronomical datasets", "University computing cluster"]
    
    # Find relevant subfields based on student interests
    relevant_subfields = []
    for subfield in ASTRONOMY_SUBFIELDS:
        if subfield.name in student_interests or any(interest in subfield.related_fields for interest in student_interests):
            relevant_subfields.append(subfield)
    
    # If no relevant subfields found, select random ones
    if not relevant_subfields:
        relevant_subfields = random.sample(ASTRONOMY_SUBFIELDS, 2)
    
    # Create challenges list separately
    challenges_list = []
    for subfield in relevant_subfields:
        for challenge in subfield.current_challenges[:2]:
            challenges_list.append(f"- {challenge}")
    
    challenges_text = "\n".join(challenges_list)
    
    # Prepare the additional context section
    context_section = ""
    if additional_context and additional_context.strip():
        context_section = f"""
Additional Student Context:
{additional_context}

Use the above information about the student's background, previous projects, and specific interests to tailor the research idea accordingly.
"""
    
    # Construct improved prompt for the LLM
    prompt = f"""Generate a novel and scientifically accurate astronomy research idea for a {skill_level} graduate student.

IMPORTANT: Create a SPECIFIC, DESCRIPTIVE title that clearly describes the exact research project. The title should precisely capture what the student will be investigating.

Parameters:
- Student interests: {', '.join(student_interests)}
- Relevant subfields: {', '.join(subfield.name for subfield in relevant_subfields)}
- Time frame: {time_frame}
- Available resources: {', '.join(available_resources)}
- Skill level: {skill_level}

Current challenges in the field:
{challenges_text}
{context_section}

Your response MUST follow this exact format with all sections thoroughly completed:

# [DESCRIPTIVE PROJECT TITLE]

## Research Question
Begin with a clear, explicit mission statement formatted as follows:

"In this project, we will use [specific data sets/observations] and [specific methods/tools/techniques] to [clear research objective - what will be measured, detected, or analyzed]."

Then provide 2-3 sentences explaining why this research is important, impactful, and how it addresses current challenges in the field. Be extremely specific about the objects, phenomena, or data to be studied.

IMPORTANT: Explicitly state the specific problem or gap in knowledge this research aims to solve. Format this as:
"This research addresses the problem of [specific problem statement], which is currently unresolved because [reasons for knowledge gap]."

## Background
Provide 3-4 paragraphs explaining:
1. The current state of knowledge in this specific area, citing recent developments (within the last 3-5 years)
2. Key gaps or uncertainties this research addresses
3. Why this gap is scientifically significant and timely
4. Why this project is particularly suitable for a {skill_level} student

The first paragraph must begin by clearly stating: "The key problem this research addresses is [concise problem statement]." Then elaborate on why this problem matters to the field.

## Methodology
Begin with: "To address the problem of [restate the specific problem], we will use the following approach:"

Provide a CONCISE methodology in 3-4 paragraphs that follows a clear logical flow. Each paragraph should focus on a distinct phase of the research:

1: Data Acquisition and Processing
- Specify exact data sources (survey names, telescope facilities, or dataset identifiers)
- Describe initial data selection criteria and preprocessing steps

2: Analysis Approach
- Outline the core analytical methods in a logical sequence
- Specify software tools and programming languages to be used
- Explain how these methods directly connect to answering the research question

3: Validation and Interpretation
- Describe how results will be validated (e.g., statistical tests, comparison with models)
- Explain how potential biases or limitations will be addressed
- Briefly outline how results will be interpreted in the context of the research question

Optional Paragraph 4: Timeline
- Provide a brief timeline showing how these steps will be completed within the {time_frame}

IMPORTANT: Maintain a clear logical flow between steps. Each step should naturally lead to the next, forming a coherent research pipeline. Avoid excessive technical details that obscure the overall approach.

## Expected Outcomes
Describe at least three concrete, measurable results this research could produce, such as:
1. Specific measurements or constraints on particular parameters
2. New catalogs or data products
3. Statistical relationships or correlations
4. Potential for publication or contribution to larger surveys

For each outcome, explicitly state how it contributes to solving the identified problem.
## Required Skills
List at least five precise technical and knowledge-based skills needed, suggesting how these could be developed during the project. Include both initial skills needed and those that will be developed.

## Broader Connections
Explain in detail how this research connects to at least three larger questions in astronomy and astrophysics, and how results from this project might inform future work.

IMPORTANT SCIENTIFIC ACCURACY GUIDELINES:
1. Do NOT propose methods that are incompatible with the mentioned data sources or resources
2. Ensure that the method is based on SCIENTIFICALLY CORRECT information
3. Be realistic about what can be achieved with the available resources and time frame
4. Double-check that the research question actually addresses the challenge it claims to address
5. Verify that the methodology logically connects to the expected outcomes
6. Ensure physical principles and astronomical phenomena are described accurately
7. Avoid suggesting breakthrough discoveries for beginner projects; focus on incremental advances
8. For observational projects, consider practical limitations like telescope time availability
9. Don't overstate the impact - be honest about the scope and limitations
10. Ensure all astronomical terminology and concepts are used correctly

CRITICAL SCIENTIFIC REASONING REQUIREMENTS:
1. DIRECT CONNECTIONS: Only propose research where there is a DIRECT, ESTABLISHED connection between the method and what it can measure. Avoid tenuous or speculative connections.
2. METHOD-GOAL ALIGNMENT: For every claimed measurement or constraint, explicitly justify WHY the proposed method is sensitive to that specific parameter or phenomenon.
3. DATA SENSITIVITY REALISM: Consider detection limits, signal-to-noise ratios, and statistical power. Never claim precision beyond what current methods allow.
4. LOGICAL WORKFLOW: Each step in the methodology must logically lead to the next, forming a coherent research pipeline.
5. PARAMETER DEGENERACIES: Acknowledge parameter degeneracies and explain how they will be addressed. Never claim unique constraints when degeneracies exist.

Make sure the idea is:
- GENUINELY NOVEL yet connected to existing literature
- Timely and of high impact
- Appropriately scoped (not too broad or narrow)
- Utilizes available resources: {', '.join(available_resources)}
- Has a VERY SPECIFIC research question with clear data sources, methods, and objectives
- Scientifically sound and technically feasible

Also make sure to follow the following skill level guideline. For a {skill_level} student within a {time_frame} timeframe:

BEGINNER STUDENTS:
- Focus on applying ESTABLISHED methods to well-understood problems
- Prioritize data analysis of public datasets over novel technique development
- Include explicit mentorship/learning components for new skills
- Limit to 1-2 new techniques to learn during the project

INTERMEDIATE STUDENTS:
- May combine established methods in novel ways
- Can develop modest extensions to existing techniques
- Should still rely primarily on proven methodologies
- May handle datasets requiring moderate preprocessing
- Limit to 2-3 advanced components

ADVANCED STUDENTS:
- May develop new methodological approaches
- Can address more open-ended research questions
- Should still maintain logical connections between methods and goals
- Realistic about complexity within timeframe

ALL PROJECTS MUST: 
- Maintain scientific integrity regardless of skill level
- Have clear, logical connections between methods and measurements
- Be completable within the specified timeframe
- Produce meaningful results even if preliminary
"""

    # Call the LLM to generate the research idea using the client
    try:
        idea_text = client.generate_content(prompt)
    except Exception as e:
        print(f"Error generating research idea: {str(e)}")
        raise RuntimeError(f"Failed to generate research idea: {str(e)}")
    
    # Parse the response into structured sections
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
    for line in idea_text.split('\n'):
        if line.startswith('# '):
            title = line.replace('# ', '').strip()
            break
    
    # Now parse the rest of the content
    for line in idea_text.split('\n'):
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
    
    # Add metadata to the result
    result = {
        "title": title if title else "Untitled Research Project",
        "subfields": [subfield.name for subfield in relevant_subfields],
        "skill_level": skill_level,
        "time_frame": time_frame,
        "resources_needed": available_resources,
        "idea": parsed_idea
    }
    
    return result

def get_title_from_text(text: str) -> str:
    """Extract or generate a title from the response text."""
    # Look for title patterns in the first few lines
    lines = text.split('\n')[:10]
    for line in lines:
        if line.strip() and not line.startswith(('1.', '2.', '#', '-')) and len(line) < 100:
            return line.strip().rstrip(':')
    
    # If no clear title is found, return the first part of the research question
    for line in lines:
        if "research question" in line.lower() or "1." in line.lower():
            question = line.split(':', 1)[-1] if ':' in line else line
            return question.strip()[:80].rstrip('?') + "?"
    
    # Fallback
    return "Astronomy Research Proposal"

def generate_multiple_ideas(count: int = 3, api_key: str = None, client: Optional[Any] = None, provider: str = "azure", **kwargs) -> List[Dict[str, Any]]:
    """Generate multiple research ideas with variations."""
    # Use the provided client or create a new one
    used_client = client
    if not used_client and api_key:
        used_client = LLMClient(api_key, provider)
    
    ideas = []
    for _ in range(count):
        ideas.append(generate_research_idea(api_key=api_key, client=used_client, provider=provider, **kwargs))
    return ideas

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
    initial_idea = idea_agent.generate_initial_idea(**student_profile)
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