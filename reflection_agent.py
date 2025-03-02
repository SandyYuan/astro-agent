import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from google import genai

# Import functions from idea_agent.py
from idea_agent import (
    generate_research_idea,
    generate_multiple_ideas,
    AstronomySubfield,
    ASTRONOMY_SUBFIELDS
)

# Assuming you've set up API keys in a config.py file
# from config import google_key

# Initialize API client
# client = genai.Client(api_key=google_key)

client = None

def initialize_client(api_key):
    """Initialize the API client with the provided key"""
    global client
    if api_key:
        client = genai.Client(api_key=api_key)
    return client

@dataclass
class ProposalFeedback:
    """Structured feedback on an astronomy research proposal."""
    scientific_validity: Dict[str, List[str]]  # strengths and concerns
    methodology: Dict[str, List[str]]  # strengths and concerns 
    novelty_assessment: str
    impact_assessment: str
    feasibility_assessment: str
    recommendations: List[str]
    summary: str

class AstronomyReflectionAgent:
    """Expert astronomer agent that evaluates research proposals."""

    def __init__(self, api_key):
        """Initialize with an API key."""
        self.api_key = api_key
        self.llm_client = genai.Client(api_key=api_key)
    
    def evaluate_proposal(self, proposal: Dict[str, Any]) -> ProposalFeedback:
        """Evaluate a proposal and return structured feedback."""
        # Create a detailed prompt for the LLM
        prompt = self._create_evaluation_prompt(proposal)
        
        # Get response from LLM
        response = self._get_llm_evaluation(prompt)
        
        # Parse the response into structured feedback
        feedback = self._parse_feedback(response)
        
        return feedback
    
    def _create_evaluation_prompt(self, proposal: Dict[str, Any]) -> str:
        """Create a detailed prompt for the LLM to evaluate the proposal."""
        title = proposal.get("title", "")
        research_question = proposal.get("idea", {}).get("Research Question", "")
        background = proposal.get("idea", {}).get("Background", "")
        methodology = proposal.get("idea", {}).get("Methodology", "")
        skill_level = proposal.get("skill_level", "")
        time_frame = proposal.get("time_frame", "")
        
        prompt = f"""
        You are an expert astronomy professor with decades of experience evaluating research proposals.
        
        Analyze this astronomy research proposal titled "{title}" thoroughly and provide critical but constructive feedback.
        
        RESEARCH QUESTION:
        {research_question}
        
        BACKGROUND:
        {background}
        
        METHODOLOGY:
        {methodology}
        
        STUDENT SKILL LEVEL: {skill_level}
        TIMEFRAME: {time_frame}
        
        EVALUATION INSTRUCTIONS:
        
        Step by step, evaluate this proposal according to these criteria:
        
        1. SCIENTIFIC VALIDITY AND ACCURACY
        - Are there direct, established connections between methods and claimed measurements?
        - Is the approach based on correct physical and astronomical principles?
        - Are there any incorrect assumptions or scientific inaccuracies?
        - Are the instruments/surveys/data sources capable of measuring what's claimed?
        
        2. METHODOLOGICAL SOUNDNESS
        - Is there a clear logical chain from methods to results?
        - Are the proposed techniques appropriate for the research question?
        - Are there statistical or data quality issues not addressed?
        - Is the signal-to-noise ratio sufficient for the measurements?
        
        3. NOVELTY AND KNOWLEDGE GAP
        - Does this address a genuine gap in current understanding?
        - How does it advance beyond existing literature?
        
        4. IMPACT AND SIGNIFICANCE
        - How would results from this project advance astronomical understanding?
        - Is the research question important to the field?
        
        5. FEASIBILITY AND RESOURCE ALIGNMENT
        - Is this project feasible for a {skill_level} student in {time_frame}?
        - Are required resources and skills appropriately matched?
        
        RESPONSE FORMAT:
        
        SCIENTIFIC VALIDITY:
        Strengths:
        - [List specific scientific strengths]
        Concerns:
        - [List specific scientific concerns with detailed technical explanations]
        
        METHODOLOGY:
        Strengths:
        - [List specific methodological strengths]
        Concerns:
        - [List specific methodological concerns with detailed technical explanations]
        
        NOVELTY ASSESSMENT:
        [1-2 paragraphs on novelty and knowledge gap]
        
        IMPACT ASSESSMENT:
        [1-2 paragraphs on significance and potential impact]
        
        FEASIBILITY ASSESSMENT:
        [1-2 paragraphs on feasibility for skill level and timeframe]
        
        KEY RECOMMENDATIONS:
        1. [Specific, actionable recommendation 1]
        2. [Specific, actionable recommendation 2]
        3. [Specific, actionable recommendation 3]
        4. [Specific, actionable recommendation 4]
        5. [Specific, actionable recommendation 5]
        
        SUMMARY ASSESSMENT:
        [1 paragraph final assessment]
        
        Be technically specific and detailed in your assessment. Reference relevant astronomy literature, limitations of instruments/methods, and statistical considerations where appropriate. Focus on constructive improvements.
        """
        
        return prompt
    
    def _get_llm_evaluation(self, prompt: str) -> str:
        """Get evaluation from the LLM."""
        try:
            # Create a fresh client with only required parameters
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash-thinking-exp", 
                contents=prompt
                # No additional parameters
            )
            return response.text
        except Exception as e:
            print(f"Error in LLM evaluation: {str(e)}")
            raise
        
    
    def _parse_feedback(self, response: str) -> ProposalFeedback:
        """Parse the LLM response into structured feedback."""
        # Extract sections using string manipulation (implement based on your LLM's output format)
        scientific_validity = self._extract_category_feedback(response, "SCIENTIFIC VALIDITY:", "METHODOLOGY:")
        methodology = self._extract_category_feedback(response, "METHODOLOGY:", "NOVELTY ASSESSMENT:")
        
        novelty = self._extract_section(response, "NOVELTY ASSESSMENT:", "IMPACT ASSESSMENT:")
        impact = self._extract_section(response, "IMPACT ASSESSMENT:", "FEASIBILITY ASSESSMENT:")
        feasibility = self._extract_section(response, "FEASIBILITY ASSESSMENT:", "KEY RECOMMENDATIONS:")
        
        recommendations_text = self._extract_section(response, "KEY RECOMMENDATIONS:", "SUMMARY ASSESSMENT:")
        recommendations = [r.strip() for r in recommendations_text.split("\n") if r.strip() and any(c.isalpha() for c in r)]
        
        summary = self._extract_section(response, "SUMMARY ASSESSMENT:", "")
        
        return ProposalFeedback(
            scientific_validity=scientific_validity,
            methodology=methodology,
            novelty_assessment=novelty,
            impact_assessment=impact,
            feasibility_assessment=feasibility,
            recommendations=recommendations,
            summary=summary
        )
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract text between two markers."""
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""
        
        start_idx += len(start_marker)
        
        if end_marker:
            end_idx = text.find(end_marker, start_idx)
            if end_idx == -1:
                return text[start_idx:].strip()
            return text[start_idx:end_idx].strip()
        else:
            return text[start_idx:].strip()
    
    def _extract_category_feedback(self, text: str, category_start: str, category_end: str) -> Dict[str, List[str]]:
        """Extract strengths and concerns for a category."""
        category_text = self._extract_section(text, category_start, category_end)
        
        strengths_text = self._extract_section(category_text, "Strengths:", "Concerns:")
        strengths = [s.strip()[2:] for s in strengths_text.split("\n") if s.strip().startswith("- ")]
        
        concerns_text = self._extract_section(category_text, "Concerns:", "")
        concerns = [c.strip()[2:] for c in concerns_text.split("\n") if c.strip().startswith("- ")]
        
        return {"strengths": strengths, "concerns": concerns}
    
    def format_feedback_for_idea_agent(self, feedback: ProposalFeedback) -> str:
        """Format feedback in a clear structure for the idea_agent."""
        result = "# EXPERT ASTRONOMY FEEDBACK\n\n"
        
        result += "## SCIENTIFIC VALIDITY CONCERNS\n"
        for concern in feedback.scientific_validity.get("concerns", []):
            result += f"- {concern}\n"
        
        result += "\n## METHODOLOGICAL CONCERNS\n"
        for concern in feedback.methodology.get("concerns", []):
            result += f"- {concern}\n"
        
        result += "\n## RECOMMENDATIONS FOR IMPROVEMENT\n"
        for i, rec in enumerate(feedback.recommendations, 1):
            result += f"{i}. {rec}\n"
        
        result += f"\n## OVERALL ASSESSMENT\n{feedback.summary}\n"
        
        return result
    
    def generate_improvement_prompt(self, original_proposal: Dict[str, Any], feedback: ProposalFeedback) -> str:
        """Generate a prompt for the idea_agent to improve the proposal based on feedback."""
        scientific_concerns = "\n".join([f"- {concern}" for concern in feedback.scientific_validity.get("concerns", [])])
        methodological_concerns = "\n".join([f"- {concern}" for concern in feedback.methodology.get("concerns", [])])
        recommendations = "\n".join([f"- {rec}" for rec in feedback.recommendations])
        
        prompt = f"""
        Revise the following astronomy research proposal based on expert feedback:
        
        Original proposal title: "{original_proposal.get('title', '')}"
        
        SCIENTIFIC VALIDITY CONCERNS:
        {scientific_concerns}
        
        METHODOLOGICAL CONCERNS:
        {methodological_concerns}
        
        EXPERT RECOMMENDATIONS:
        {recommendations}
        
        OVERALL ASSESSMENT:
        {feedback.summary}
        
        Create an improved research proposal that:
        1. Addresses ALL identified scientific concerns
        2. Fixes the methodological issues
        3. Incorporates the expert recommendations
        4. Maintains scientific rigor throughout
        5. Ensures claims are proportional to what methods can actually measure
        6. Is appropriate for a {original_proposal.get('skill_level', '')} student within a {original_proposal.get('time_frame', '')} timeframe
        
        The improved proposal should follow the same format with all required sections.
        """
        
        return prompt
    
def generate_improved_idea(original_proposal: Dict[str, Any], feedback: ProposalFeedback, client) -> Dict[str, Any]:
    """Generate an improved research idea based on expert feedback."""
    # Create reflection agent
    reflection_agent = AstronomyReflectionAgent(client)
    
    # Generate improvement prompt
    improvement_prompt = reflection_agent.generate_improvement_prompt(original_proposal, feedback)
    
    # Get improved idea from LLM
    response = client.models.generate_content(
        model="gemini-2.0-flash-thinking-exp", contents=improvement_prompt
    )
    improved_idea_text = response.text
    
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
    
    # Extract the title (first line with # prefix)
    title = ""
    for line in improved_idea_text.split('\n'):
        if line.startswith('# '):
            title = line.replace('# ', '').strip()
            break
    
    # Parse sections
    parsed_idea = {}
    current_section = None
    section_content = []
    
    for line in improved_idea_text.split('\n'):
        if line.startswith('## '):
            section_name = line.replace('## ', '').strip()
            if current_section and section_content:
                parsed_idea[current_section] = '\n'.join(section_content).strip()
            current_section = section_name
            section_content = []
        elif current_section:
            section_content.append(line)
    
    # Add the last section
    if current_section and section_content:
        parsed_idea[current_section] = '\n'.join(section_content).strip()
    
    # Create result structure
    result = {
        "title": title if title else "Improved Research Project",
        "subfields": original_proposal.get("subfields", []),
        "skill_level": original_proposal.get("skill_level", ""),
        "time_frame": original_proposal.get("time_frame", ""),
        "resources_needed": original_proposal.get("resources_needed", []),
        "idea": parsed_idea
    }
    
    return result

if __name__ == "__main__":
    """Run the full idea generation, reflection, and improvement pipeline."""
    # Import necessary modules
    from idea_agent import IdeaAgent
    from google import genai
    from config import google_key
    
    # Initialize API client
    client = genai.Client(api_key=google_key)
    
    # Step 1: Define a student profile
    student_profile = {
        "student_interests": ["Observational Cosmology", "Galaxy Formation and Evolution"],
        "skill_level": "beginner",
        "time_frame": "2 years",
        "available_resources": ["Public datasets", "Large telescope time via hosting institution", "University computing cluster"]
    }
    
    # Step 2: Initialize both agents
    idea_agent = IdeaAgent(client)
    reflection_agent = AstronomyReflectionAgent(client)
    
    print("\n" + "="*100)
    print("STEP 1: GENERATING INITIAL RESEARCH IDEA...")
    print("="*100)
    # Step 3: Generate initial research idea
    initial_idea = idea_agent.generate_initial_idea(**student_profile)
    
    print(f"\n=== ORIGINAL RESEARCH IDEA ===")
    print(f"Title: {initial_idea['title']}")
    print("\nResearch Question:")
    print(initial_idea['idea']['Research Question'])
    print("\nMethodology (excerpt):")
    methodology = initial_idea['idea']['Methodology']
    print(methodology[:300] + "..." if len(methodology) > 300 else methodology)
    
    print("\n" + "="*100)
    print("STEP 2: EVALUATING RESEARCH IDEA...")
    print("="*100)
    # Step 4: Evaluate the research idea
    feedback = reflection_agent.evaluate_proposal(initial_idea)
    
    # Step 5: Format and print the feedback
    formatted_feedback = reflection_agent.format_feedback_for_idea_agent(feedback)
    print("\n=== EXPERT FEEDBACK ===")
    print(formatted_feedback)
    
    print("\n" + "="*100)
    print("STEP 3: GENERATING IMPROVED RESEARCH IDEA...")
    print("="*100)
    # Step 6: Improve the idea based on feedback
    improved_idea = idea_agent.improve_idea(feedback.__dict__)
    
    print("\n=== IMPROVED RESEARCH IDEA ===")
    print(f"Title: {improved_idea['title']}")
    print("\nResearch Question:")
    print(improved_idea['idea']['Research Question'])
    print("\nMethodology (excerpt):")
    improved_methodology = improved_idea['idea']['Methodology']
    print(improved_methodology[:300] + "..." if len(improved_methodology) > 300 else improved_methodology)
    
    # Step 7: Compare key changes
    print("\n" + "="*100)
    print("IMPROVEMENT COMPARISON")
    print("="*100)
    print("\n1. TITLE CHANGE:")
    print(f"   BEFORE: {initial_idea['title']}")
    print(f"   AFTER:  {improved_idea['title']}")

    # Fix the scientific concerns display
    print("\n2. KEY SCIENTIFIC CHANGES:")
    if hasattr(feedback, "scientific_validity") and isinstance(feedback.scientific_validity, dict):
        scientific_concerns = feedback.scientific_validity.get("concerns", [])
        if scientific_concerns:
            for concern in scientific_concerns:
                print(f"   - Addressed: {concern}")
        else:
            print("   No specific scientific concerns were identified.")
    else:
        print("   Unable to extract scientific concerns from feedback.")

    # Fix the methodological concerns display
    print("\n3. METHODOLOGICAL IMPROVEMENTS:")
    if hasattr(feedback, "methodology") and isinstance(feedback.methodology, dict):
        methodological_concerns = feedback.methodology.get("concerns", [])
        if methodological_concerns:
            for concern in methodological_concerns:
                print(f"   - Improved: {concern}")
        else:
            print("   No specific methodological concerns were identified.")
    else:
        print("   Unable to extract methodological concerns from feedback.")

    # Display recommendations
    print("\n4. RECOMMENDATIONS IMPLEMENTED:")
    if hasattr(feedback, "recommendations") and feedback.recommendations:
        for i, rec in enumerate(feedback.recommendations, 1):
            print(f"   ✓ {rec}")
    else:
        print("   No specific recommendations were provided.")