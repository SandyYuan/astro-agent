import os
import re
import json
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
    
    def __init__(self, api_key: str, provider: str = "google", temperature: float = 0.5):
        """
        Initializes the LiteratureAgent.
        
        Args:
            api_key: The API key for the language model provider.
            provider: The LLM provider (e.g., 'google', 'openai').
            temperature: The temperature for the LLM.
        """
        self.api_key = api_key
        self.provider = provider
        self.temperature = temperature
        try:
            self.llm_client = LLMClient(self.api_key, self.provider, self.temperature)
        except ValueError as e:
            raise ValueError(f"Error initializing LiteratureAgent's LLM client: {str(e)}")
    
    def simplify_query_with_llm(self, query: str) -> str:
        """Use the LLM to simplify and improve the search query."""
        try:
            # print("Simplifying query with LLM...")
            simplified_query = self.llm_client.generate(
                f"Convert this research idea into 3-5 key search terms for academic paper search: {query}"
            )
            # print(f"Simplified query: {simplified_query}")
            return simplified_query.strip()
        except Exception as e:
            # print(f"Error simplifying query with LLM: {e}. Falling back to original query.")
            return query
    
    def search_semantic_scholar(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search Semantic Scholar using their API."""
        # print(f"Searching Semantic Scholar via direct API for: {query}")
        
        # Clean and prepare the query
        # Remove quotes and clean up the query for the API
        clean_query = query.replace('"', '').replace("'", "").strip()
        
        # Semantic Scholar API endpoint
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        
        # Parameters for the search
        params = {
            'query': clean_query,
            'limit': min(limit, 100),  # API limit is 100
            'fields': 'title,abstract,authors,year,citationCount,url,paperId'
        }
        
        try:
            # print(f"Querying Semantic Scholar API with a 30-second timeout...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # print("Search complete. Processing results...")
            data = response.json()
            
            papers = []
            if 'data' in data and data['data']:
                for paper in data['data']:
                    # Only include papers with abstracts
                    if paper.get('abstract'):
                        papers.append({
                            'title': paper.get('title', 'Unknown Title'),
                            'abstract': paper.get('abstract', 'No abstract available'),
                            'authors': [author.get('name', 'Unknown') for author in paper.get('authors', [])],
                            'year': paper.get('year', 'Unknown'),
                            'citation_count': paper.get('citationCount', 0),
                            'url': paper.get('url', ''),
                            'paper_id': paper.get('paperId', '')
                        })
            
            # print(f"Found {len(papers)} papers on Semantic Scholar.")
            return papers
            
        except requests.exceptions.RequestException as e:
            # print(f"An error occurred during Semantic Scholar API request: {e}")
            return []
        except Exception as e:
            # print(f"An error occurred during Semantic Scholar search: {e}")
            return []

    def run_literature_search(self, research_idea: Dict[str, Any], max_papers: int = 10) -> LiteratureFeedback:
        """
        Searches Semantic Scholar for relevant papers and generates a literature review.
        """
        if not isinstance(research_idea, dict):
            raise ValueError("research_idea must be a dictionary.")

        title = research_idea.get("title", "")
        idea_details = research_idea.get("idea", {})
        original_query = idea_details.get("Research Question", "") or title

        if not original_query:
            return self._create_basic_review([])
        
        # Simplify the query for better API results
        search_query = self.simplify_query_with_llm(original_query)

        # Run Semantic Scholar Search
        all_papers = self.search_semantic_scholar(search_query, max_papers)
        
        # Analyze results
        if not all_papers:
            # print("No papers found from any source.")
            return LiteratureFeedback(similar_papers=[], novelty_assessment="Could not generate an AI-powered analysis. Review the papers manually.", differentiation_suggestions=["Consider refining your search terms to find more relevant literature."], emerging_trends="Not available.", novelty_score=0.0, recommended_improvements=[], summary="Automated literature analysis failed.")
        
        # print(f"Total papers found: {len(all_papers)}. Starting literature review...")
        
        # Prepare paper information for LLM
        papers_info = []
        for paper in all_papers[:max_papers]:  # Limit for prompt size
            papers_info.append(
                f"- Title: {paper['title']}\n"
                f"  Authors: {', '.join(paper['authors'])}\n"
                f"  Year: {paper['year']}\n"
                f"  Abstract: {paper['abstract'][:500]}...\n" # Truncate for prompt
            )
        
        papers_text = "\n".join(papers_info) if papers_info else "No relevant papers were found in the initial search."

        prompt = f"""
You are an expert astronomy researcher tasked with evaluating the novelty of a student's research idea based on recently published papers.

**Student's Research Idea:**
- Title: {research_idea.get('title', 'N/A')}
- Research Question: {research_idea.get('idea', {}).get('Research Question', 'N/A')}
- Proposed Methodology: {research_idea.get('idea', {}).get('Methodology', 'N/A')}

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
                similar_papers=all_papers,
                novelty_score=review_json.get("novelty_score", 0),
                novelty_assessment=review_json.get("novelty_assessment", "N/A"),
                differentiation_suggestions=review_json.get("differentiation_suggestions", []),
                emerging_trends=review_json.get("emerging_trends", "N/A"),
                summary=review_json.get("summary", "N/A"),
                recommended_improvements=[] # This field can be deprecated or kept for compatibility
            )
        except Exception as e:
            print(f"Error parsing literature review: {str(e)}")
            return self._create_basic_review(all_papers)

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
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("API key not found. Set the GOOGLE_API_KEY environment variable.")
        
        agent = LiteratureAgent(api_key, provider="google")
        
        example_idea = {
            "title": "DESI ACT cross-correlaton to constrain galaxy-halo connection",
            "idea": {
                "Research Question": "Can we constrain the galaxy-halo connection by cross-correlating DESI and ACT data?"
            }
        }
        
        feedback = agent.run_literature_search(example_idea)
        
        print("\n--- Literature Review Feedback ---")
        print(json.dumps(feedback.__dict__, indent=2, default=str))

    asyncio.run(main())