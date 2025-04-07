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
    
    def review_literature(self, idea: Dict[str, Any], max_papers: int = 5) -> LiteratureFeedback:
        """Review literature for a research idea"""
        # Extract key information
        title = idea.get("title", "")
        
        # Use the title directly as the search query
        search_query = f"{title} astronomy"
        print(f"\n=== USING SIMPLIFIED SEARCH ===")
        print(f"Search query: {search_query}")
        
        # Search for papers using Google Custom Search
        try:
            papers = self._search_google_scholar(search_query, max_papers)
        except Exception as e:
            print(f"Google Scholar search failed: {str(e)}")
            papers = []
        
        # Generate literature review (even if no papers found - the LLM will handle this case)
        return self._generate_literature_review(idea, papers)
    
    def _search_google_scholar(self, search_query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for academic papers using Google Custom Search API, focusing on ArXiv papers"""
        print("\n=== GOOGLE SCHOLAR SEARCH ===")
        print(f"Search query: {search_query}")
        
        # Google CSE API endpoint - using hardcoded values
        api_key = 'AIzaSyDmX4sfJd9aiNjhhNTyWz7uIVxWlj2qDow'
        cse_id = 'd325c376fba944623'
        
        # Add arxiv.org to the search query to prioritize ArXiv papers
        arxiv_search_query = f"{search_query} site:arxiv.org"
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": arxiv_search_query,
            "num": min(max_results, 20),  # API limit is 10 results per query
        }
        
        try:
            response = requests.get(url, params=params)
            results = response.json()
            
            papers = []
            if "items" in results:
                for item in results["items"]:
                    # Extract paper information
                    link = item.get("link", "")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    
                    # Only process ArXiv papers
                    if "arxiv.org" not in link:
                        continue
                    
                    # Extract ArXiv ID from URL - handle multiple formats
                    arxiv_id = None
                    
                    # Format 1: https://arxiv.org/abs/2105.13368
                    abs_match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', link)
                    if abs_match:
                        arxiv_id = abs_match.group(1)
                    
                    # Format 2: https://arxiv.org/pdf/2212.08748
                    pdf_match = re.search(r'arxiv\.org/pdf/(\d+\.\d+)', link)
                    if not arxiv_id and pdf_match:
                        arxiv_id = pdf_match.group(1)
                    
                    # Format 3: https://ar5iv.labs.arxiv.org/html/1402.4814
                    html_match = re.search(r'arxiv\.org/html/(\d+\.\d+)', link)
                    if not arxiv_id and html_match:
                        arxiv_id = html_match.group(1)
                    
                    # Format 4: ar5iv.labs.arxiv.org/html/1402.4814
                    ar5iv_match = re.search(r'ar5iv\.labs\.arxiv\.org/html/(\d+\.\d+)', link)
                    if not arxiv_id and ar5iv_match:
                        arxiv_id = ar5iv_match.group(1)
                    
                    # Skip if we couldn't extract an ArXiv ID
                    if not arxiv_id:
                        print(f"Could not extract ArXiv ID from: {link}")
                        continue
                        
                    print(f"Found ArXiv ID: {arxiv_id} from {link}")
                    
                    # Fetch paper details from ArXiv API
                    try:
                        abstract, paper_title, authors = self._fetch_arxiv_abstract(arxiv_id)
                        
                        # Skip if we couldn't get the abstract
                        if not abstract:
                            print(f"Could not fetch abstract for ArXiv ID: {arxiv_id}")
                            continue
                            
                        # Use the API title if available, otherwise use the search result title
                        if paper_title and len(paper_title) > 10:
                            title = paper_title
                            
                        # Get year from ArXiv ID (first 2 digits after the dot represent the year)
                        year_match = re.search(r'\.(\d\d)', arxiv_id)
                        year = datetime.datetime.now().year
                        if year_match:
                            year_prefix = '20'  # Assuming all papers are from 2000s or 2100s
                            year = int(f"{year_prefix}{year_match.group(1)}")
                        
                        paper = {
                            'title': title,
                            'authors': authors,
                            'summary': abstract,
                            'published': f"{year}",
                            'year': year,
                            'url': f"https://arxiv.org/abs/{arxiv_id}",  # Use canonical URL
                            'source': 'ArXiv',
                            'arxiv_id': arxiv_id
                        }
                        papers.append(paper)
                        
                    except Exception as e:
                        print(f"Error processing ArXiv paper {arxiv_id}: {str(e)}")
                        continue
            
            # Print found papers
            if papers:
                print(f"\nFound {len(papers)} ArXiv papers")
                for paper in papers:
                    print(f"- {paper['title']}")
                    print(f"  (ArXiv ID: {paper['arxiv_id']})")
            else:
                print("No ArXiv papers found")
                
            return papers
        except Exception as e:
            print(f"Error searching Google: {str(e)}")
            return []
    
    def _fetch_arxiv_abstract(self, arxiv_id: str) -> Tuple[str, str, str]:
        """Fetch abstract, title and authors from ArXiv API for a given paper ID"""
        try:
            # ArXiv API endpoint
            url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return "", "", ""
                
            # Parse XML response
            xml_content = response.text
            
            # Extract abstract
            abstract_match = re.search(r'<summary>(.*?)</summary>', xml_content, re.DOTALL)
            abstract = ""
            if abstract_match:
                abstract = abstract_match.group(1).strip()
                # Clean up the abstract
                abstract = re.sub(r'\s+', ' ', abstract)
            
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', xml_content, re.DOTALL)
            title = ""
            if title_match:
                title = title_match.group(1).strip()
                # Remove "Title:" prefix if present
                if title.lower().startswith("title:"):
                    title = title[6:].strip()
            
            # Extract authors
            authors = []
            author_matches = re.finditer(r'<author>.*?<name>(.*?)</name>.*?</author>', xml_content, re.DOTALL)
            for match in author_matches:
                authors.append(match.group(1).strip())
            
            # Format authors
            authors_str = ""
            if authors:
                if len(authors) == 1:
                    authors_str = authors[0]
                elif len(authors) == 2:
                    authors_str = f"{authors[0]} and {authors[1]}"
                else:
                    authors_str = f"{authors[0]} et al."
            
            return abstract, title, authors_str
            
        except Exception as e:
            print(f"Error fetching ArXiv abstract for {arxiv_id}: {str(e)}")
            return "", "", ""
    
    def _extract_journal(self, url: str) -> str:
        """Extract journal name from URL"""
        # This method is no longer needed
        return "ArXiv"
    
    def _generate_literature_review(self, idea: Dict[str, Any], papers: List[Dict[str, Any]]) -> LiteratureFeedback:
        """Generate a literature review based on the found papers"""
        # Extract idea details
        title = idea.get("title", "")
        
        # Extract research question and methodology from the idea dictionary
        # First try direct access, then try nested access
        research_question = idea.get("research_question", "")
        if not research_question and "idea" in idea and isinstance(idea["idea"], dict):
            research_question = idea["idea"].get("Research Question", "")
        
        methodology = idea.get("methodology", "")
        if not methodology and "idea" in idea and isinstance(idea["idea"], dict):
            methodology = idea["idea"].get("Methodology", "")
        
        subfields = ", ".join(idea.get("subfields", []))
        
        # Format papers for prompt
        papers_text = ""
        if papers:
            for i, paper in enumerate(papers, 1):
                papers_text += f"""
                Paper {i}:
                Title: {paper.get('title', '')}
                Authors: {paper.get('authors', '')}
                Year: {paper.get('year', '')}
                Abstract: {paper.get('summary', '')}
                """
        else:
            # If no papers were found, indicate this
            papers_text = "No relevant papers were found in the search. This could indicate a novel research area or that the search terms need refinement."
        
        # Create prompt for literature review
        prompt = f"""
        You are an expert astronomy researcher with access to the latest scientific literature. You need to evaluate the novelty of this research proposal based on the provided papers from the last 10 years and suggest ways to make it more innovative while ensuring it remains scientifically grounded and feasible.
        
        RESEARCH PROPOSAL TO EVALUATE:
        
        Title: {title}
        
        Subfields: {subfields}
        
        Research Question:
        {research_question}
        
        Methodology:
        {methodology}
        
        RECENT LITERATURE (published in the last 10 years):
        
        {papers_text}
        
        YOUR TASK:
        
        1. LITERATURE ANALYSIS: Analyze how the proposal relates to the provided papers. Identify aspects that are:
           - Already well-studied in recent literature (potential overlap)
           - Partially explored but with gaps
           - Potentially novel contributions not addressed in the papers
        
        2. DIFFERENTIATION SUGGESTIONS: Provide specific recommendations on how the proposal could be made more novel while remaining scientifically grounded. Focus on:
           - Methodological innovations
           - Unique data combinations
           - Unexplored parameter spaces
           - Novel theoretical frameworks
        
        3. EMERGING TRENDS: Based on the papers and your expertise, identify cutting-edge developments in this research area that could be incorporated.
        
        4. NOVELTY SCORE: Rate the current novelty of the proposal on a scale of 1-10, where:
           - 1-3: Largely replicates existing work
           - 4-6: Incremental advance over existing work
           - 7-8: Contains significant novel elements
           - 9-10: Highly innovative approach
           
        FORMAT YOUR RESPONSE AS FOLLOWS:
        
        SIMILAR RECENT PAPERS:
        {'' if papers else '[Note: No directly relevant papers were found in the search, which may indicate this is a novel research direction or that the search terms need refinement.]'}
        {'' if not papers else 'For each relevant paper, provide a clear assessment of its relevance to the proposal using this format:'}
        
        {'' if not papers else '1. PAPER TITLE: [Provide a 2-3 sentence assessment of how this paper relates to the proposal, including similarities and differences]'}
        {'' if not papers else '2. PAPER TITLE: [Provide a 2-3 sentence assessment of how this paper relates to the proposal, including similarities and differences]'}
        {'' if not papers else '... and so on for each paper'}
        
        NOVELTY ASSESSMENT:
        [Detailed paragraph analyzing the proposal's novelty against existing literature]
        
        DIFFERENTIATION SUGGESTIONS:
        1. [Specific suggestion to make the idea more novel]
        2. [Another suggestion...]
        3. [Another suggestion...]
        [1-2 sentences explaining why each suggestion would enhance novelty while maintaining scientific validity]
        
        EMERGING TRENDS:
        [Paragraph on emerging trends in this research area that could be incorporated]
        
        NOVELTY SCORE: [Number 1-10]
        [Brief justification for the score]
        
        KEY RECOMMENDATIONS FOR IMPROVING NOVELTY:
        1. [Clear, actionable recommendation]
        2. [Another recommendation...]
        3. [Another recommendation...]
        
        SUMMARY:
        [Final 3-4 sentence assessment summarizing novelty status and the most promising directions for innovation]
        
        IMPORTANT GUIDELINES:
        - Be scientifically accurate and realistic in your assessment
        - If no papers were found, be honest about the limitations of the search and potential implications
        - Ensure suggested innovations are methodologically feasible
        - Provide specific, actionable feedback, not general advice
        - Focus on making the idea novel in meaningful ways that advance scientific understanding
        - Consider both methodological and conceptual innovations
        - Keep suggestions grounded in current astronomical capabilities and theoretical frameworks
        - For each paper, clearly state its title before providing the relevance assessment
        """
        
        try:
            # Get response from LLM
            review_text = self.llm_client.generate_content(prompt)
            
            # Add relevance to the papers based on the review
            if papers:
                self._add_relevance_to_papers(papers, review_text)
            
            # Parse the text response
            literature_review = self._parse_literature_review(
                review_text, 
                papers
            )
            
            return literature_review
        
        except Exception as e:
            print(f"Error generating literature review: {str(e)}")
            # Create a basic review when analysis fails
            return self._create_basic_review(papers)
    
    def _add_relevance_to_papers(self, papers: List[Dict[str, Any]], review_text: str) -> None:
        """Add relevance assessments to the papers based on the review text"""
        # Extract the "SIMILAR RECENT PAPERS" section
        similar_papers_section = self._extract_section(review_text, "SIMILAR RECENT PAPERS:", "NOVELTY ASSESSMENT:")
        
        # Process each paper to find its relevance assessment
        for paper in papers:
            title = paper.get('title', '').lower()
            if not title:
                paper['relevance'] = "Relevance to the research proposal not specifically assessed."
                continue
                
            # Try to find a mention of this paper in the similar papers section
            found_relevance = False
            
            # Split the section into paragraphs for better matching
            paragraphs = [p.strip() for p in similar_papers_section.split('\n\n') if p.strip()]
            
            for paragraph in paragraphs:
                # Check if this paragraph mentions the paper title (using a more flexible approach)
                # Look for significant words from the title rather than exact matches
                significant_words = [word for word in title.split() if len(word) > 4]
                
                # If we have significant words to match
                if significant_words:
                    # Count how many significant words appear in the paragraph
                    matches = sum(1 for word in significant_words if word in paragraph.lower())
                    
                    # If more than half of the significant words match, consider this a match
                    if matches >= max(1, len(significant_words) // 2):
                        # Extract the relevance information - everything after the title mention
                        # First try to find the title in the paragraph
                        title_words = title.split()
                        if len(title_words) >= 3:
                            # Try to find a sequence of 3+ words from the title
                            for i in range(len(title_words) - 2):
                                title_fragment = ' '.join(title_words[i:i+3]).lower()
                                if title_fragment in paragraph.lower():
                                    # Find where this fragment ends in the paragraph
                                    fragment_pos = paragraph.lower().find(title_fragment) + len(title_fragment)
                                    # Extract everything after this as the relevance
                                    relevance_text = paragraph[fragment_pos:].strip()
                                    if relevance_text:
                                        # Clean up the relevance text
                                        if relevance_text.startswith('-'):
                                            relevance_text = relevance_text[1:].strip()
                                        if relevance_text.startswith(':'):
                                            relevance_text = relevance_text[1:].strip()
                                        paper['relevance'] = relevance_text
                                        found_relevance = True
                                        break
                        
                        # If we couldn't extract relevance based on title fragment, use the whole paragraph
                        if not found_relevance:
                            paper['relevance'] = paragraph
                            found_relevance = True
                        break
            
            # If no relevance found, add a default one
            if not found_relevance:
                paper['relevance'] = "Relevance to the research proposal not specifically assessed."
    
    def _parse_literature_review(self, review_text: str, papers: List[Dict[str, Any]]) -> LiteratureFeedback:
        """Parse the literature review text into structured feedback"""
        # Extract novelty assessment
        novelty_assessment = self._extract_section(review_text, "NOVELTY ASSESSMENT:", "DIFFERENTIATION SUGGESTIONS:")
        
        # Extract differentiation suggestions
        differentiation_section = self._extract_section(review_text, "DIFFERENTIATION SUGGESTIONS:", "EMERGING TRENDS:")
        differentiation_suggestions = []
        
        for line in differentiation_section.strip().split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or (len(line) > 1 and line[0] == '-')):
                # Remove the number or dash prefix
                suggestion = line[1:].strip() if line[0].isdigit() else line[2:].strip()
                if suggestion and len(suggestion) > 10:  # Ensure it's meaningful
                    differentiation_suggestions.append(suggestion)
        
        # Extract emerging trends
        emerging_trends = self._extract_section(review_text, "EMERGING TRENDS:", "NOVELTY SCORE:")
        
        # Extract novelty score
        novelty_score_section = self._extract_section(review_text, "NOVELTY SCORE:", "KEY RECOMMENDATIONS")
        novelty_score = 5.0  # Default score
        
        try:
            # Look for a number in the section
            score_match = re.search(r'\b([0-9]|10)(\.[0-9])?\b', novelty_score_section)
            if score_match:
                novelty_score = float(score_match.group(0))
            else:
                # If no decimal number found, look for numbers like "7/10"
                score_match = re.search(r'\b([0-9]|10)/10\b', novelty_score_section)
                if score_match:
                    score_value = score_match.group(0).split('/')[0]
                    novelty_score = float(score_value)
        except (ValueError, IndexError):
            pass  # Keep default score on error
        
        # Extract recommendations
        recommendations_section = self._extract_section(review_text, "KEY RECOMMENDATIONS FOR IMPROVING NOVELTY:", "SUMMARY:")
        recommendations = []
        
        for line in recommendations_section.strip().split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or (len(line) > 1 and line[0] == '-')):
                # Remove the number or dash prefix
                rec = line[1:].strip() if line[0].isdigit() else line[2:].strip()
                if rec and len(rec) > 10:  # Ensure it's meaningful
                    recommendations.append(rec)
        
        # Extract summary
        summary = self._extract_section(review_text, "SUMMARY:", "")
        
        # Create formatted paper list for feedback
        similar_papers = []
        for paper in papers:
            similar_papers.append({
                'title': paper.get('title', ''),
                'authors': paper.get('authors', ''),
                'year': paper.get('year', ''),
                'journal': paper.get('journal', ''),
                'summary': paper.get('summary', ''),
                'relevance': paper.get('relevance', 'Relevance to the research proposal not specifically assessed.'),
                'url': paper.get('url', ''),
                'source': paper.get('source', '')
            })
        
        # Create and return feedback object
        return LiteratureFeedback(
            similar_papers=similar_papers,
            novelty_assessment=novelty_assessment,
            differentiation_suggestions=differentiation_suggestions,
            emerging_trends=emerging_trends,
            novelty_score=novelty_score,
            recommended_improvements=recommendations,
            summary=summary
        )
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract text between two markers with improved robustness"""
        try:
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
        except Exception:
            # Return empty string on any error
            return ""
    
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
            novelty_assessment="A detailed novelty assessment could not be generated. Please review the literature manually.",
            differentiation_suggestions=[
                "Consider exploring more recent datasets or observational techniques",
                "Look for interdisciplinary approaches that combine methods from different subfields",
                "Focus on a specific aspect of the problem that may be underexplored"
            ],
            emerging_trends="Emerging trends could not be automatically identified. Consider consulting recent review papers in this field.",
            novelty_score=novelty_score,
            recommended_improvements=[
                "Conduct a more thorough literature review using additional databases",
                "Consult with domain experts in this specific research area",
                "Consider how your methodology differs from standard approaches"
            ],
            summary=summary
        )
    
    def format_feedback_for_idea_agent(self, feedback: LiteratureFeedback) -> Dict[str, Any]:
        """Format feedback for consumption by the idea agent."""
        # Prepare the literature insights for the idea agent
        return {
            "literature_review": feedback.to_dict() if hasattr(feedback, "to_dict") else feedback.__dict__
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