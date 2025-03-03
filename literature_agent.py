import json
import time
import datetime
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta

# For Google GenAI
from google import genai

# Import arxiv package for API access
import arxiv

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
    
    def __init__(self, api_key):
        """Initialize with an API key"""
        self.api_key = api_key
        self.llm_client = genai.Client(api_key=self.api_key)
        
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
        """
        Review recent astronomy literature to evaluate the novelty of an idea
        and suggest improvements to make it more innovative
        
        Args:
            idea: The research idea to evaluate
            max_papers: Maximum number of papers to retrieve
            
        Returns:
            LiteratureFeedback object containing analysis and suggestions
        """
        # Extract relevant data for search
        title = idea.get("title", "")
        research_question = idea.get("idea", {}).get("Research Question", "")
        subfields = idea.get("subfields", [])
        
        # Generate search query from the idea
        search_query = self._generate_search_query(title, research_question, subfields)
        
        # Search for relevant papers
        try:
            papers = self._search_arxiv(search_query, max_papers)
        except Exception as e:
            print(f"ArXiv search failed: {str(e)}")
            # Return empty papers list if search fails - no simulated papers
            papers = []
        
        # Generate literature review based on found papers
        literature_review = self._generate_literature_review(idea, papers)
        
        return literature_review
    
    def _generate_search_query(self, title: str, research_question: str, subfields: List[str]) -> str:
        """Generate a search query based on the research idea"""
        # Extract key terms from the title and research question
        prompt = f"""
        Extract the 4-6 most important search terms from this astronomy research proposal.
        
        Title: {title}
        
        Research Question: {research_question}
        
        Subfields: {', '.join(subfields)}
        
        Return only a space-separated list of the most specific and relevant technical terms that would appear in related academic papers.
        Focus on specific methods, objects, or phenomena being studied rather than general terms.
        
        Format your response as: term1 term2 term3 term4 term5 term6
        """
        
        try:
            response = self.llm_client.models.generate_content(
                model="gemini-2.0-flash-thinking-exp", 
                contents=prompt
            )
            search_terms = response.text.strip()
            
            # Clean up the response to extract just the terms
            if ' ' in search_terms:
                terms = [term.strip() for term in search_terms.split(' ')]
            else:
                # Otherwise split by newlines or other potential separators
                terms = re.split(r'[\n\r,;]', search_terms)
                terms = [term.strip() for term in terms if term.strip()]
            
            # Filter out any non-relevant items and join with "AND" for better search
            terms = [term for term in terms if len(term) > 2 and not term.startswith(('Format', 'Return', 'Focus'))]
            
            # Add category filters for astronomy
            category_filters = []
            for subfield in subfields:
                # Map subfields to appropriate arXiv categories
                if "exoplanet" in subfield.lower() or "planetary" in subfield.lower():
                    category_filters.append("cat:astro-ph.EP")  # Earth and planetary
                elif "galaxy" in subfield.lower() or "galaxies" in subfield.lower():
                    category_filters.append("cat:astro-ph.GA")  # Galaxies
                elif "cosmology" in subfield.lower() or "universe" in subfield.lower():
                    category_filters.append("cat:astro-ph.CO")  # Cosmology
                elif "star" in subfield.lower() or "stellar" in subfield.lower() or "solar" in subfield.lower():
                    category_filters.append("cat:astro-ph.SR")  # Solar and stellar
                elif "high-energy" in subfield.lower() or "black hole" in subfield.lower():
                    category_filters.append("cat:astro-ph.HE")  # High-energy astrophysics
                elif "instrument" in subfield.lower() or "method" in subfield.lower() or "data" in subfield.lower():
                    category_filters.append("cat:astro-ph.IM")  # Instrumentation and methods
            
            # If no specific categories were matched, include all astronomy categories
            if not category_filters:
                category_filters = ["cat:astro-ph"]
            
            # Combine terms and category filters
            final_query = " AND ".join(terms + category_filters)
            
            return final_query
        
        except Exception as e:
            print(f"Error generating search query: {str(e)}")
            # Fallback to basic search using title and categories
            return f"{title} AND cat:astro-ph"
    
    def _search_arxiv(self, query: str, max_papers: int = 5) -> List[Dict[str, Any]]:
        """Search arXiv for relevant papers from the last 10 years"""
        # Calculate date from 10 years ago
        ten_years_ago = datetime.datetime.now() - relativedelta(years=10)
        
        # Create the search query
        search = arxiv.Search(
            query=query,
            max_results=20,  # Request more papers than needed to filter by date
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        # Extract papers
        papers = []
        try:
            for result in search.results():
                try:
                    # Fix datetime comparison issue by making both naive
                    # Get the publication date and remove timezone info if present
                    pub_date = result.published
                    if pub_date and hasattr(pub_date, 'tzinfo') and pub_date.tzinfo is not None:
                        # Convert to naive datetime by replacing tzinfo with None
                        pub_date = pub_date.replace(tzinfo=None)
                    
                    # Check if the paper is from the last 10 years
                    if pub_date and pub_date >= ten_years_ago:
                        # Format authors
                        author_names = [author.name for author in result.authors]
                        if len(author_names) > 3:
                            formatted_authors = f"{author_names[0]} et al."
                        else:
                            formatted_authors = ", ".join(author_names)
                        
                        # Format date
                        pub_date_str = pub_date.strftime('%Y-%m-%d') if pub_date else "Unknown"
                        pub_year = pub_date.year if pub_date else datetime.datetime.now().year
                        
                        # Get paper URL
                        paper_url = result.entry_id if result.entry_id else ""
                        if not paper_url.startswith("http"):
                            paper_url = f"https://arxiv.org/abs/{result.entry_id.split('/')[-1]}"
                        
                        # Clean abstract
                        abstract = result.summary.replace('\n', ' ').strip() if result.summary else ""
                        
                        papers.append({
                            'title': result.title.strip() if result.title else "Untitled",
                            'authors': formatted_authors,
                            'year': str(pub_year),
                            'journal': "arXiv",
                            'arxiv_id': result.entry_id.split('/')[-1] if result.entry_id else "",
                            'abstract': abstract,
                            'summary': abstract[:500] + "..." if len(abstract) > 500 else abstract,
                            'published_date': pub_date_str,
                            'url': paper_url,
                            'source': "arXiv",
                            'categories': result.categories
                        })
                        
                        # Stop once we have enough papers
                        if len(papers) >= max_papers:
                            break
                except Exception as e:
                    print(f"Error processing paper: {str(e)}")
                    continue
        except Exception as e:
            print(f"Error retrieving arXiv results: {str(e)}")
        
        return papers
    
    def _generate_literature_review(self, idea: Dict[str, Any], papers: List[Dict[str, Any]]) -> LiteratureFeedback:
        """Generate a literature review based on the found papers"""
        # Extract idea details
        title = idea.get("title", "")
        research_question = idea.get("idea", {}).get("Research Question", "")
        methodology = idea.get("idea", {}).get("Methodology", "")
        subfields = ", ".join(idea.get("subfields", []))
        
        # Format papers for prompt
        papers_text = ""
        for i, paper in enumerate(papers, 1):
            papers_text += f"""
            Paper {i}:
            Title: {paper.get('title', '')}
            Authors: {paper.get('authors', '')}
            Year: {paper.get('year', '')}
            Journal/Source: {paper.get('journal', '')}
            {"ArXiv ID: " + paper.get('arxiv_id', '') if paper.get('arxiv_id') else ""}
            Abstract: {paper.get('summary', '')}
            """
        
        # If no papers were found, indicate this
        if not papers:
            papers_text = "No directly relevant papers were found in the recent literature matching the search criteria."
        
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
        [For each relevant paper, provide a 1-2 sentence assessment of its relevance to the proposal]
        
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
        """
        
        try:
            # Get response from LLM
            response = self.llm_client.models.generate_content(
                model="gemini-2.0-flash-thinking-exp", 
                contents=prompt
            )
            
            # Add relevance to the papers based on the review
            self._add_relevance_to_papers(papers, response.text)
            
            # Parse the text response
            literature_review = self._parse_literature_review(
                response.text, 
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
            
            # Try to find a mention of this paper in the similar papers section
            for line in similar_papers_section.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line mentions the paper
                if title and len(title) > 10 and title[:15] in line.lower():
                    # Found a mention of this paper, extract the relevance
                    paper['relevance'] = line
                    # Clean up the format: "Paper Title - Relevance information"
                    if ' - ' in paper['relevance']:
                        paper['relevance'] = paper['relevance'].split(' - ', 1)[1]
                    break
            
            # If no relevance found, add a default one
            if 'relevance' not in paper:
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
        """Create a basic review when analysis fails, using only real papers"""
        # Format the papers from real results
        formatted_papers = []
        for paper in papers:
            formatted_papers.append({
                'title': paper.get('title', ''),
                'authors': paper.get('authors', ''),
                'year': paper.get('year', ''),
                'journal': paper.get('journal', ''),
                'summary': paper.get('summary', ''),
                'relevance': paper.get('relevance', 'Relevance unknown due to analysis failure.'),
                'url': paper.get('url', ''),
                'source': paper.get('source', '')
            })
        
        # Create a basic review message
        if papers:
            assessment = "We found some papers that might be related to your research proposal, but we couldn't complete a detailed analysis. Please review these papers to assess how your idea relates to existing work."
            score = 5.0  # Neutral score
        else:
            assessment = "We couldn't find any papers directly related to your research proposal in our search. This could mean your idea is novel, but please consider conducting a more comprehensive literature search to confirm."
            score = 7.0  # Slightly higher score due to potential novelty
        
        return LiteratureFeedback(
            similar_papers=formatted_papers,
            novelty_assessment=assessment,
            differentiation_suggestions=[
                "Review the related papers more closely to identify gaps",
                "Consider consulting field experts for more tailored literature recommendations",
                "Search additional databases beyond ArXiv for a more comprehensive review"
            ],
            emerging_trends="Due to analysis limitations, we couldn't identify specific emerging trends. Consider reviewing recent conference proceedings and review papers in your field.",
            novelty_score=score,
            recommended_improvements=[
                "Conduct a more comprehensive literature review",
                "Clearly articulate how your work differs from existing research",
                "Consider consulting with subject matter experts in your specific subfield"
            ],
            summary="Due to technical limitations, we could only provide a basic assessment. Please review the papers we found and consider conducting a more thorough literature review to better assess novelty and potential contributions."
        )
    
    def format_feedback_for_idea_agent(self, feedback: LiteratureFeedback) -> Dict[str, Any]:
        """Format literature feedback for the idea agent"""
        # This is now returning a dictionary for better integration with the idea agent
        return {
            "literature_review": {
                "similar_papers": feedback.similar_papers,
                "novelty_assessment": feedback.novelty_assessment,
                "differentiation_suggestions": feedback.differentiation_suggestions,
                "emerging_trends": feedback.emerging_trends,
                "novelty_score": feedback.novelty_score,
                "recommended_improvements": feedback.recommended_improvements,
                "summary": feedback.summary
            }
        }
    
    def format_feedback_for_display(self, feedback: LiteratureFeedback) -> str:
        """Format literature feedback for display in the UI"""
        result = "# LITERATURE REVIEW FEEDBACK\n\n"
        
        result += f"## NOVELTY ASSESSMENT (Score: {feedback.novelty_score}/10)\n"
        result += f"{feedback.novelty_assessment}\n\n"
        
        result += "## SIMILAR RECENT PAPERS\n"
        if feedback.similar_papers:
            for i, paper in enumerate(feedback.similar_papers, 1):
                result += f"{i}. **{paper['title']}** by {paper['authors']} ({paper['year']}) - {paper['journal']}\n"
                if paper.get('url'):
                    result += f"   URL: {paper['url']}\n"
                result += f"   Summary: {paper['summary']}\n"
                result += f"   Relevance: {paper['relevance']}\n\n"
        else:
            result += "No similar papers were found in our search of recent literature.\n\n"
        
        result += "## INNOVATION OPPORTUNITIES\n"
        for i, suggestion in enumerate(feedback.differentiation_suggestions, 1):
            result += f"{i}. {suggestion}\n"
        
        result += f"\n## EMERGING RESEARCH TRENDS\n{feedback.emerging_trends}\n"
        
        result += "\n## KEY RECOMMENDATIONS FOR IMPROVING NOVELTY\n"
        for i, rec in enumerate(feedback.recommended_improvements, 1):
            result += f"{i}. {rec}\n"
        
        result += f"\n## OVERALL ASSESSMENT\n{feedback.summary}\n"
        
        return result