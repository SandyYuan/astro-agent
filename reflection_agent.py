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
    
    def evaluate_proposal(self, proposal: Dict[str, Any], literature_feedback: Optional[Dict[str, Any]] = None) -> ProposalFeedback:
        """Evaluate a proposal and return structured feedback."""
        # Create a detailed prompt for the LLM
        prompt = self._create_evaluation_prompt(proposal, literature_feedback)
        
        # Get response from LLM
        response = self._get_llm_evaluation(prompt)
        
        # Parse the response into structured feedback
        feedback = self._parse_feedback(response)

        # Add literature insights if available
        if literature_feedback:
            feedback.literature_insights = literature_feedback.get("literature_review")
        
        return feedback
    
    def _create_evaluation_prompt(self, proposal: Dict[str, Any], literature_feedback: Optional[Dict[str, Any]] = None) -> str:
        """Create a detailed prompt for the LLM to evaluate the proposal."""
        title = proposal.get("title", "")
        research_question = proposal.get("idea", {}).get("Research Question", "")
        background = proposal.get("idea", {}).get("Background", "")
        methodology = proposal.get("idea", {}).get("Methodology", "")
        skill_level = proposal.get("skill_level", "")
        time_frame = proposal.get("time_frame", "")
        
        # Base prompt
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
        """
        
        # Add literature feedback if available
        if literature_feedback and "literature_review" in literature_feedback:
            lit_review = literature_feedback["literature_review"]
            
            # Extract key components from literature feedback
            similar_papers = lit_review.get("similar_papers", [])
            novelty_assessment = lit_review.get("novelty_assessment", "")
            novelty_score = lit_review.get("novelty_score", 5.0)
            recommendations = lit_review.get("recommended_improvements", [])
            emerging_trends = lit_review.get("emerging_trends", "")
            
            # Format similar papers
            papers_text = ""
            for i, paper in enumerate(similar_papers[:3], 1):  # Limit to top 3 papers
                title = paper.get("title", "Unknown Title")
                authors = paper.get("authors", "Unknown Authors")
                year = paper.get("year", "Unknown Year")
                journal = paper.get("journal", "Unknown Journal")
                relevance = paper.get("relevance", "")
                
                papers_text += f"{i}. {title} by {authors} ({year}) - {journal}\n"
                if relevance:
                    papers_text += f"   Relevance: {relevance}\n"
            
            # Format recommendations
            recs_text = "\n".join([f"- {rec}" for rec in recommendations[:3]])  # Limit to top 3
            
            # Add literature section to prompt
            prompt += f"""
            
            LITERATURE REVIEW FINDINGS:
            
            Similar Recent Papers:
            {papers_text}
            
            Novelty Assessment (Score: {novelty_score}/10):
            {novelty_assessment}
            
            Key Innovation Recommendations:
            {recs_text}
            
            Emerging Research Trends:
            {emerging_trends}
            """
        
        # Add evaluation instructions
        prompt += """
        
        EVALUATION INSTRUCTIONS:
        
        Step by step, evaluate this proposal according to these criteria:
        
        1. SCIENTIFIC VALIDITY AND ACCURACY
        - Is the problem statement clear and specific?
        - Are there direct, established connections between methods and claimed measurements?
        - Is the approach based on correct physical and astronomical principles?
        - Are there any incorrect assumptions or scientific inaccuracies?
        - Are the instruments/surveys/data sources capable of measuring what's claimed?
        
        2. METHODOLOGICAL SOUNDNESS
        - Does the methodology directly address the stated problem?
        - Is there a clear logical chain from methods to results?
        - Are the proposed techniques appropriate for the research question?
        - Are there statistical or data quality issues not addressed?
        - Is the signal-to-noise ratio sufficient for the measurements?
        - Is the methodology concise and well-structured (3-4 paragraphs with clear logical flow)?
        - Does the methodology avoid excessive technical details that obscure the overall approach?
        
        3. NOVELTY AND KNOWLEDGE GAP
        - **Synthesize the 'LITERATURE REVIEW FINDINGS' provided above** with your own expertise.
        - Based on both, assess if the proposal addresses a genuine, significant gap in current understanding.
        - How does it advance beyond the specific literateure cited and the broader field?
        - Evaluate the originality of the approach and research question.
        - **Your 'NOVELTY ASSESSMENT' output below should reflect this synthesis.**
                
        4. IMPACT AND SIGNIFICANCE
        - How important is the problem being addressed?
        - How would results from this project advance astronomical understanding?
        - Is the research question important to the field?
        
        5. FEASIBILITY AND RESOURCE ALIGNMENT
        - Is this project feasible for a {skill_level} student in {time_frame}?
        - Are required resources and skills appropriately matched?
        
        RESPONSE FORMAT:
        
        YOU MUST FOLLOW THIS EXACT FORMAT WITH THESE EXACT SECTION HEADINGS. DO NOT DEVIATE FROM THIS FORMAT.
        
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
            return self.llm_client.generate_content(prompt)
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
    
    def format_feedback_for_idea_agent(self, feedback: ProposalFeedback) -> Dict[str, Any]:
        """Format feedback for consumption by the idea agent."""
        # Extract components
        sci_concerns = feedback.scientific_validity.get("concerns", []) 
        meth_concerns = feedback.methodology.get("concerns", [])
        
        # Format for the idea agent
        return {
            "scientific_validity": feedback.scientific_validity,
            "methodology": feedback.methodology,
            "recommendations": feedback.recommendations,
            "summary": feedback.summary,
            "literature_insights": feedback.literature_insights
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