import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import the LLMClient wrapper
from llm_client import LLMClient

# Try to import Google's genai library for backward compatibility
try:
    from google import genai
except ImportError:
    genai = None

# Remove incorrect import block from idea_agent_twocalls
# from idea_agent_twocalls import (
#     IdeaAgentTwoCalls as IdeaAgent,
#     AstronomySubfield,
#     ASTRONOMY_SUBFIELDS
# )

# Assuming you've set up API keys in a config.py file
# from config import google_key

# Initialize API client
# client = genai.Client(api_key=google_key)

client = None

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
    literature_insights: Optional[Dict[str, Any]] = None  # Added field for literature feedback

class AstronomyReflectionAgent:
    """Expert astronomer agent that evaluates research proposals."""

    def __init__(self, api_key, provider="azure", model=None):
        """Initialize with an API key and provider."""
        self.api_key = api_key
        self.provider = provider
        self.model = model
        
        # Initialize the LLM client with the appropriate provider
        try:
            self.llm_client = LLMClient(api_key, provider)
        except ValueError as e:
            raise ValueError(f"Error initializing reflection agent: {str(e)}")
    
    def provide_feedback(self, research_proposal: Dict[str, Any]) -> ProposalFeedback:
        """
        Evaluates a structured research proposal and returns feedback.
        """
        prompt = self._create_evaluation_prompt(research_proposal)
        
        try:
            response_text = self.llm_client.generate(prompt)
            feedback_json = self.llm_client.extract_json(response_text)
            
            return ProposalFeedback(
                scientific_validity=feedback_json.get("scientific_validity", {}),
                methodology=feedback_json.get("methodology", {}),
                novelty_assessment=feedback_json.get("novelty_assessment", "N/A"),
                impact_assessment=feedback_json.get("impact_assessment", "N/A"),
                feasibility_assessment=feedback_json.get("feasibility_assessment", "N/A"),
                recommendations=feedback_json.get("recommendations", []),
                summary=feedback_json.get("summary", "N/A")
            )
        except Exception as e:
            print(f"Error parsing reflection feedback: {e}")
            # Return a default/error object
            return ProposalFeedback(
                scientific_validity={'strengths': [], 'concerns': ['Failed to parse AI feedback.']},
                methodology={'strengths': [], 'concerns': []},
                novelty_assessment="N/A",
                impact_assessment="N/A",
                feasibility_assessment="N/A",
                recommendations=[],
                summary="Could not generate feedback due to an internal error."
            )

    def _create_evaluation_prompt(self, proposal: Dict[str, Any]) -> str:
        """Create a detailed prompt for the LLM to evaluate the proposal."""
        
        # Safely extract proposal details
        title = proposal.get("title", "N/A")
        idea = proposal.get("idea", {})
        research_question = idea.get("Research Question", "N/A")
        background = idea.get("Background", "N/A")
        methodology = idea.get("Methodology", "N/A")
        skill_level = proposal.get("skill_level", "N/A")
        time_frame = proposal.get("time_frame", "N/A")

        prompt = f"""
You are an expert astronomy professor providing constructive feedback on a student's research idea.
Your tone should be encouraging but also rigorous and scientifically precise.

**Student's Proposal:**
- Title: {title}
- Research Question: {research_question}
- Background: {background}
- Proposed Methodology: {methodology}
- Student's Stated Skill Level: {skill_level}
- Time Frame: {time_frame}

**Your Task:**
Evaluate the proposal based on the criteria below. Provide specific, actionable feedback. Your entire response MUST be a single JSON object.

{{
  "scientific_validity": {{
    "strengths": [
      "[List 1-2 specific scientific strengths. What core ideas are promising? Is the question well-posed?]"
    ],
    "concerns": [
      "[List 1-2 specific scientific concerns. Are there flawed assumptions? Is the goal physically plausible?]"
    ]
  }},
  "methodology": {{
    "strengths": [
      "[List 1-2 strengths of the proposed methodology. Is the approach logical? Is the choice of data/technique appropriate?]"
    ],
    "concerns": [
      "[List 1-2 concerns about the methodology. Is it too simple or too complex? Are there unaddressed biases or limitations?]"
    ]
  }},
  "novelty_assessment": "[Provide a 1-2 sentence assessment of the idea's novelty. Does it address a known gap? How does it compare to standard approaches?]",
  "impact_assessment": "[Provide a 1-2 sentence assessment of the potential impact. If successful, what would this research contribute to the field?]",
  "feasibility_assessment": "[Provide a 1-2 sentence assessment of the project's feasibility, considering the student's skill level ('{skill_level}') and the time frame ('{time_frame}'). Is the scope realistic?]",
  "recommendations": [
    "[Provide a specific, actionable recommendation for improving the scientific framing.]",
    "[Provide a specific, actionable recommendation for improving the methodology.]",
    "[Provide one other key recommendation to strengthen the overall proposal.]"
  ],
  "summary": "[Write a final, 2-3 sentence summary that synthesizes your feedback and gives the student a clear sense of the proposal's potential and key next steps.]"
}}
"""
        return prompt

    def format_feedback_for_idea_agent(self, feedback: ProposalFeedback) -> Dict[str, Any]:
        """Format feedback for consumption by the idea agent."""
        # Extract components
        sci_concerns = feedback.scientific_validity.get("concerns", []) 
        meth_concerns = feedback.methodology.get("concerns", [])
        
        # Format for the idea agent
        return {
            "scientific_validity": feedback.scientific_validity,
            "methodology": feedback.methodology,
            "novelty_assessment": feedback.novelty_assessment,
            "impact_assessment": feedback.impact_assessment,
            "feasibility_assessment": feedback.feasibility_assessment,
            "recommendations": feedback.recommendations,
            "summary": feedback.summary
        }
    
if __name__ == "__main__":
    """Run the full idea generation, reflection, and improvement pipeline."""
    # Import necessary modules
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
    idea_agent = IdeaAgent(google_key, provider="google")
    reflection_agent = AstronomyReflectionAgent(google_key, provider="google")
    
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
    feedback = reflection_agent.provide_feedback(initial_idea)
    
    # Step 5: Format and print the feedback
    formatted_feedback = reflection_agent.format_feedback_for_idea_agent(feedback)
    print("\n=== EXPERT FEEDBACK ===")
    print(json.dumps(formatted_feedback, indent=2))
    
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