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
    
    def generate_initial_idea(
        self,
        student_interests: List[str],
        skill_level: str,
        time_frame: str,
        available_resources: List[str]
    ) -> Dict[str, Any]:
        """
        Generates a novel research idea from scratch based on student profile.
        """
        self.student_profile = {
            "student_interests": student_interests,
            "skill_level": skill_level,
            "time_frame": time_frame,
            "available_resources": available_resources,
        }

        prompt = f"""
You are an expert astronomy research advisor tasked with generating a novel research idea for a student.

**Student's Profile:**
- Interests: {', '.join(student_interests)}
- Skill Level: {skill_level}
- Time Frame: {time_frame}
- Available Resources: {', '.join(available_resources)}

**Your Task:**
Based on the student's profile, generate a single, compelling, and feasible research idea. The idea should be novel but achievable within the student's constraints.

Your response MUST be a single JSON object with the exact following structure.

{{
  "title": "[Create a concise, descriptive title for the research project]",
  "subfields": ["{random.choice(student_interests) if student_interests else 'General Astrophysics'}"],
  "skill_level": "{skill_level}",
  "time_frame": "{time_frame}",
  "idea": {{
    "Research Question": "[Formulate a single, clear, and testable research question.]",
    "Proposed Solution": "[Provide a single, specific sentence describing the core method to answer the question. Be concrete about datasets and tools. Example: 'Analyze photometric data for quiescent galaxies from SDSS DR17 between redshift 0.1 and 0.2 using Python with Astropy to measure morphological properties.']",
    "Background": "[Provide 1-2 paragraphs of background context. Explain why this question is scientifically interesting and relevant.]",
    "Expected Outcomes": "[Describe 2-3 potential, concrete outcomes from this research.]"
  }}
}}
"""
        try:
            response_text = self.llm_client.generate(prompt)
            json_response = self.llm_client.extract_json(response_text)
            self.current_idea = json_response
            return self.current_idea
        except Exception as e:
            print(f"An error occurred while generating an idea: {e}")
            return {{ "error": "Failed to generate research idea.", "details": str(e) }}
    
    def structure_and_rephrase_idea(self, user_idea: str) -> Dict[str, Any]:
        """
        Takes a user's raw idea and structures it into a formal research proposal.
        """
        prompt = f"""
You are an expert astronomy research advisor. A student has come to you with a research idea. Your task is to take their raw input and rephrase it into a structured, coherent, and scientifically sound research proposal concept.

**DO NOT INVENT A NEW IDEA.** Your sole purpose is to clarify, structure, and formalize the student's existing idea based *only* on the information they have provided.

**Student's Raw Idea:**
"{user_idea}"

Based on the student's idea, please structure it into the following JSON format. Fill in each field by interpreting their request. If their idea is vague, make reasonable, scientifically-grounded inferences to fill out the sections.

Your response MUST be a single JSON object. Do not include any text outside the JSON object.

{{
  "title": "[Create a concise, descriptive title for the research project based on the user's idea]",
  "subfields": ["Identify the most relevant astronomy subfields (e.g., 'Exoplanet Atmospheres', 'Cosmology', 'Stellar Astrophysics')"],
  "idea": {{
    "Research Question": "[Based on the user's idea, formulate a single, clear, and testable research question.]",
    "Proposed Solution": "[Provide a single, specific sentence describing the core method to answer the question. Be concrete about datasets and tools. Example: 'Analyze photometric data for quiescent galaxies from SDSS DR17 between redshift 0.1 and 0.2 using Python with Astropy to measure morphological properties.']",
    "Background": "[Provide 1-2 paragraphs of background context. Explain why this question is scientifically interesting and relevant.]",
    "Expected Outcomes": "[Describe 2-3 potential, concrete outcomes from this research. What would be the tangible result? (e.g., a catalog of objects, a measurement of a parameter, a confirmation of a theory).]"
  }}
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
    
    def improve_idea(self, reflection_feedback: Dict[str, Any], literature_feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Improves the current research idea based on feedback."""
        if not self.current_idea:
            raise ValueError("Cannot improve an idea without a current idea.")

        # Serialize feedback for the prompt
        reflection_summary = reflection_feedback.get('summary', 'No summary provided.')
        recommendations = reflection_feedback.get('recommendations', [])
        
        # Combine all feedback into a clear set of instructions
        feedback_prompt_section = f"**Expert Professor's Feedback:**\n- Summary: {reflection_summary}\n- Recommendations:\n"
        for rec in recommendations:
            if isinstance(rec, dict):
                feedback_prompt_section += f"  - {rec.get('recommendation', json.dumps(rec))}\n"
            else:
                feedback_prompt_section += f"  - {rec}\n"

        if literature_feedback:
            lit_summary = literature_feedback.get('summary', 'No summary provided.')
            lit_suggestions = literature_feedback.get('differentiation_suggestions', [])
            feedback_prompt_section += f"\n**Literature Review Feedback:**\n- Summary: {lit_summary}\n- Suggestions for Novelty:\n"
            for sugg in lit_suggestions:
                feedback_prompt_section += f"  - {sugg}\n"

        prompt = f"""
You are an astronomy student revising your research proposal based on feedback from your professor and a literature review.

**Your Original Proposal:**
{json.dumps(self.current_idea, indent=2)}

**Feedback to Incorporate:**
{feedback_prompt_section}

**Your Task:**
Revise your original proposal to directly address all the feedback. Create an improved version that is more robust, feasible, and novel. Your response MUST be a single JSON object in the exact same format as the original proposal. Do not add any extra text. The JSON object should contain the improved version of your proposal.
"""
        try:
            response_text = self.llm_client.generate(prompt)
            improved_idea = self.llm_client.extract_json(response_text)
            self.current_idea = improved_idea # Update the agent's state
            return improved_idea
        except Exception as e:
            print(f"An error occurred while improving the idea: {e}")
            return {{"error": "Failed to improve the research idea.", "details": str(e)}}

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