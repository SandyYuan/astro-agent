import os
import re
import json
import arxiv
import asyncio
import nest_asyncio
import datetime
import requests
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta

# Import the LLMClient wrapper
from llm_client import LLMClient

# Try to import Google's genai library for backward compatibility
try:
    from google import genai
except ImportError:
    genai = None

# Apply nest_asyncio to allow nested event loops (needed for async arxiv search)
nest_asyncio.apply()

@dataclass
class LiteratureFeedback:
    """Structured feedback from literature review"""
    similar_papers: List[Dict[str, str]]
    novelty_assessment: str
    differentiation_suggestions: List[str]
    emerging_trends: str
    novelty_score: float
    recommended_improvements: List[str]
    summary: str

class LiteratureAgent:
    """Agent that analyzes recent astronomy literature to evaluate idea novelty"""
    
    def __init__(self, api_key, provider="azure", model=None):
        """Initialize with an API key and provider"""
        self.api_key = api_key
        self.provider = provider
        self.model = model
        
        # Initialize the LLM client with the appropriate provider
        try:
            self.llm_client = LLMClient(api_key, provider)
        except ValueError as e:
            raise ValueError(f"Error initializing literature agent: {str(e)}")
        
        # ArXiv categories relevant to astronomy
        self.astronomy_categories = [
            'astro-ph.GA',  # Galaxies and cosmology
            'astro-ph.CO',  # Cosmology
            'astro-ph.EP',  # Earth and planetary science
            'astro-ph.HE',  # High-energy astrophysics
            'astro-ph.IM',  # Instrumentation and methods
            'astro-ph.SR',  # Solar and stellar astrophysics
        ]
    
    def run_arxiv_search(self, research_idea: Dict[str, Any], max_papers: int = 5) -> LiteratureFeedback:
        """
        Searches arXiv for relevant papers and generates a literature review.
        """
        if not isinstance(research_idea, dict):
            raise ValueError("research_idea must be a dictionary.")

        title = research_idea.get("title", "")
        idea_details = research_idea.get("idea", {})
        query = idea_details.get("Research Question", "") or title

        if not query:
            return self._create_basic_review([])

        # Use the research question for a more targeted search
        search_query = f'"{query}"'
        
        try:
            search = arxiv.Search(
                query=search_query,
                max_results=max_papers,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = []
            for result in search.results():
                papers.append({
                    'title': result.title,
                    'authors': ", ".join(author.name for author in result.authors),
                    'summary': result.summary,
                    'published': result.published.strftime('%Y-%m-%d'),
                    'year': result.published.year,
                    'url': result.entry_id,
                    'source': 'ArXiv'
                })
            
            return self._generate_literature_review(research_idea, papers)
        
        except Exception as e:
            print(f"An error occurred during arXiv search: {e}")
            return self._create_basic_review([])

    def _generate_literature_review(self, idea: Dict[str, Any], papers: List[Dict[str, Any]]) -> LiteratureFeedback:
        """Generate a literature review using an LLM."""
        
        papers_info = []
        for paper in papers:
            papers_info.append(
                f"- Title: {paper['title']}\n"
                f"  Authors: {paper['authors']}\n"
                f"  Year: {paper['year']}\n"
                f"  Abstract: {paper['summary'][:500]}...\n" # Truncate for prompt
            )
        
        papers_text = "\n".join(papers_info) if papers_info else "No relevant papers were found in the initial search."

        prompt = f"""
You are an expert astronomy researcher tasked with evaluating the novelty of a student's research idea based on recently published papers.

**Student's Research Idea:**
- Title: {idea.get('title', 'N/A')}
- Research Question: {idea.get('idea', {}).get('Research Question', 'N/A')}
- Proposed Methodology: {idea.get('idea', {}).get('Methodology', 'N/A')}

**Relevant Recent Papers:**
{papers_text}

**Your Task:**
Based *only* on the student's idea and the provided list of papers, provide a comprehensive analysis. If no papers were found, assess the idea based on general domain knowledge.

Your response MUST be a single JSON object with the following structure. Do not include any text outside of the JSON object.

{{
  "novelty_score": [Provide a score from 1 (not novel) to 10 (highly novel). Base this on whether similar papers exist and how much the student's idea overlaps with them.],
  "novelty_assessment": "[Provide a 2-3 sentence analysis explaining the novelty score. If similar papers exist, explain the overlap. If not, explain why the idea might be novel or hard to research.]",
  "differentiation_suggestions": [
    "[Suggest 2-3 concrete ways the student could differentiate their project from the existing literature. For example: 'Focus on a different class of objects,' 'Apply a more advanced analysis technique,' or 'Use a newer, more sensitive dataset.']"
  ],
  "emerging_trends": "[Based on the papers, briefly describe any emerging trends in this research area. If no papers, state that.]",
  "summary": "[Provide a final 1-2 sentence summary of the literature review, concluding with a clear recommendation on whether to proceed, refine, or reconsider the idea.]"
}}
"""
        try:
            response_text = self.llm_client.generate(prompt)
            # Clean the response to ensure it's valid JSON
            review_json = self.llm_client.extract_json(response_text)
            
            # Combine with paper details for the final object
            return LiteratureFeedback(
                similar_papers=papers,
                novelty_score=review_json.get("novelty_score", 0),
                novelty_assessment=review_json.get("novelty_assessment", "N/A"),
                differentiation_suggestions=review_json.get("differentiation_suggestions", []),
                emerging_trends=review_json.get("emerging_trends", "N/A"),
                summary=review_json.get("summary", "N/A"),
                recommended_improvements=[] # This field can be deprecated or kept for compatibility
            )
        except Exception as e:
            print(f"Error parsing literature review: {str(e)}")
            return self._create_basic_review(papers)

    def _create_basic_review(self, papers: List[Dict[str, Any]]) -> LiteratureFeedback:
        """Create a basic review when analysis fails"""
        if papers:
            similar_papers = [
                {
                    "title": paper.get("title", ""),
                    "relevance": "Potentially relevant to the research topic."
                }
                for paper in papers[:3]  # Only include up to 3 papers
            ]
            
            novelty_score = 7  # Default to somewhat novel
            summary = "The literature search found some potentially related papers, but a detailed analysis could not be completed. Consider reviewing these papers manually to assess novelty."
        else:
            similar_papers = []
            novelty_score = 8  # Default to more novel when no papers found
            summary = "No directly relevant papers were found in the search. This could indicate a novel research direction, but it's recommended to conduct a more thorough literature review using additional sources."
        
        return LiteratureFeedback(
            similar_papers=similar_papers,
            novelty_assessment="Could not generate an AI-powered analysis. Review the papers manually.",
            differentiation_suggestions=["Consider refining your search terms to find more relevant literature."],
            emerging_trends="Not available.",
            novelty_score=0.0,
            recommended_improvements=[],
            summary="Automated literature analysis failed."
        )
    
    def format_feedback_for_idea_agent(self, feedback: LiteratureFeedback) -> Dict[str, Any]:
        """Format feedback for consumption by the idea agent."""
        # Prepare the literature insights for the idea agent
        return {
            "similar_papers": feedback.similar_papers,
            "novelty_assessment": feedback.novelty_assessment,
            "differentiation_suggestions": feedback.differentiation_suggestions,
            "emerging_trends": feedback.emerging_trends,
            "novelty_score": feedback.novelty_score,
            "recommended_improvements": feedback.recommended_improvements
        }
    
# Commented out unused function
# def format_feedback_for_display(self, feedback: LiteratureFeedback) -> str:
#     """Format literature feedback for display to the user."""
#     result = "# LITERATURE REVIEW\n\n"
#     
#     # Add novelty score and assessment
#     result += f"## Novelty Assessment (Score: {feedback.novelty_score}/10)\n"
#     result += f"{feedback.novelty_assessment}\n\n"
#     
#     # Add similar papers
#     result += "## Similar Recent Papers\n"
#     for i, paper in enumerate(feedback.similar_papers[:3], 1):
#         title = paper.get("title", "Unknown Title")
#         authors = paper.get("authors", "Unknown Authors")
#         year = paper.get("year", "Unknown Year") 
#         relevance = paper.get("relevance", "")
#         
#         result += f"{i}. **{title}** by {authors} ({year})\n"
#         if relevance:
#             result += f"   *Relevance: {relevance}*\n"
#     
#     # Add recommendations
#     result += "\n## Key Innovation Recommendations\n"
#     for rec in feedback.recommended_improvements:
#         result += f"- {rec}\n"
#     
#     # Add emerging trends
#     result += f"\n## Emerging Research Trends\n{feedback.emerging_trends}\n"
#     
#     return result

if __name__ == '__main__':
    async def main():
        # Example Usage
        api_key = os.environ.get("GOOGLE_API_KEY") # Replace with your actual key
        if not api_key:
            raise ValueError("API key not found. Set the GOOGLE_API_KEY environment variable.")
        
        agent = LiteratureAgent(api_key, provider="google")
        
        # Example idea
        example_idea = {
            "title": "Searching for Technosignatures in the Galactic Center",
            "idea": {
                "Research Question": "Can we detect anomalous narrowband signals from the Galactic Center using existing radio survey data?"
            }
        }
        
        # Run literature review
        feedback = agent.run_arxiv_search(example_idea)
        
        # Print results
        print("\n--- Literature Review Feedback ---")
        print(json.dumps(feedback.__dict__, indent=2, default=str))

    # Run the async main function
    asyncio.run(main())