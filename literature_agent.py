import json
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Correct import for Google GenAI
from google import genai

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
    
    def review_literature(self, idea: Dict[str, Any]) -> LiteratureFeedback:
        """
        Review recent astronomy literature to evaluate the novelty of an idea
        and suggest improvements to make it more innovative
        
        Args:
            idea: The research idea to evaluate
            
        Returns:
            LiteratureFeedback object containing analysis and suggestions
        """
        prompt = self._create_literature_review_prompt(idea)
        
        # Use the correct method for generating content with Gemini
        response = self.llm_client.models.generate_content(
            model="gemini-2.0-flash-thinking-exp", 
            contents=prompt
        )
        
        literature_review = self._parse_literature_review(response.text)
        return literature_review
    
    def _create_literature_review_prompt(self, idea: Dict[str, Any]) -> str:
        """Create a detailed prompt for literature review"""
        title = idea.get("title", "")
        research_question = idea.get("idea", {}).get("Research Question", "")
        methodology = idea.get("idea", {}).get("Methodology", "")
        subfields = ", ".join(idea.get("subfields", []))
        
        prompt = f"""
        You are an expert astronomy researcher with access to the latest scientific literature. You need to evaluate the novelty of this research proposal and suggest ways to make it more innovative while ensuring it remains scientifically grounded and feasible.
        
        RESEARCH PROPOSAL TO EVALUATE:
        
        Title: {title}
        
        Subfields: {subfields}
        
        Research Question:
        {research_question}
        
        Methodology:
        {methodology}
        
        YOUR TASK:
        
        1. LITERATURE SEARCH: Identify 3-5 recent papers (published in the last 1-2 years) that are most similar to this proposal.
        
        2. NOVELTY ASSESSMENT: Analyze how the proposal compares to existing literature. Identify aspects that are:
           - Already well-studied (potential overlap)
           - Partially explored but with gaps
           - Potentially novel contributions
        
        3. DIFFERENTIATION SUGGESTIONS: Provide specific recommendations on how the proposal could be made more novel while remaining scientifically grounded. Focus on:
           - Methodological innovations
           - Unique data combinations
           - Unexplored parameter spaces
           - Novel theoretical frameworks
        
        4. EMERGING TRENDS: Identify cutting-edge developments in this research area that could be incorporated.
        
        5. NOVELTY SCORE: Rate the current novelty of the proposal on a scale of 1-10, where:
           - 1-3: Largely replicates existing work
           - 4-6: Incremental advance over existing work
           - 7-8: Contains significant novel elements
           - 9-10: Highly innovative approach
           
        FORMAT YOUR RESPONSE AS FOLLOWS:
        
        RECENT SIMILAR PAPERS:
        1. [Title] by [Authors] ([Year]) - [Journal/ArXiv ID]
        Brief summary: [1-2 sentence summary]
        Relevance: [How this paper relates to the proposal]
        
        2. [Next paper...]
        
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
        - Ensure suggested innovations are methodologically feasible
        - Provide specific, actionable feedback, not general advice
        - Focus on making the idea novel in meaningful ways that advance scientific understanding
        - Consider both methodological and conceptual innovations
        - Keep suggestions grounded in current astronomical capabilities and theoretical frameworks
        """
        
        return prompt
    
    def _parse_literature_review(self, review_text: str) -> LiteratureFeedback:
        """Parse the literature review text into structured feedback"""
        # Extract paper information
        papers_section = self._extract_section(review_text, "RECENT SIMILAR PAPERS:", "NOVELTY ASSESSMENT:")
        papers = []
        
        # First attempt: Parse by detecting numbered items and structure
        paper_blocks = []
        current_block = []
        in_paper_section = False
        
        # Split the paper section into blocks for each paper
        for line in papers_section.split('\n'):
            line = line.strip()
            if not line:
                if current_block:  # End of a block
                    paper_blocks.append('\n'.join(current_block))
                    current_block = []
                continue
                
            # Check for a new paper entry (starts with number)
            if line and line[0].isdigit() and ('. ' in line or '.' in line):
                if current_block:  # Save previous block if it exists
                    paper_blocks.append('\n'.join(current_block))
                    current_block = []
                in_paper_section = True
            
            if in_paper_section:
                current_block.append(line)
        
        # Add the last block if it exists
        if current_block:
            paper_blocks.append('\n'.join(current_block))
        
        # Process each detected paper block
        for block in paper_blocks:
            lines = block.split('\n')
            if not lines:
                continue
                
            # Initialize with default values
            paper_info = {
                "title": "",
                "authors": "",
                "year": "",
                "journal": "",
                "summary": "",
                "relevance": ""
            }
            
            # First line should contain the paper title and possibly authors/year
            first_line = lines[0]
            
            # Check various formats the model might use
            # Format 1: "1. Title by Authors (Year) - Journal"
            if first_line and first_line[0].isdigit():
                try:
                    # Remove the number prefix
                    title_part = first_line.split(".", 1)[1].strip() if "." in first_line else first_line
                    
                    # Case 1: Standard format with "by" and parentheses
                    if " by " in title_part and "(" in title_part:
                        title_and_rest = title_part.split(" by ", 1)
                        paper_info["title"] = title_and_rest[0].strip()
                        
                        if len(title_and_rest) > 1:
                            rest = title_and_rest[1].strip()
                            # Extract author and year
                            if "(" in rest:
                                authors, year_part = rest.split("(", 1)
                                paper_info["authors"] = authors.strip()
                                
                                # Extract year and possibly journal
                                year_part = year_part.strip(")")
                                if " - " in year_part:
                                    year, journal = year_part.split(" - ", 1)
                                    paper_info["year"] = year.strip()
                                    paper_info["journal"] = journal.strip()
                                else:
                                    paper_info["year"] = year_part.strip()
                    # Case 2: Just a title with no author/year information
                    else:
                        paper_info["title"] = title_part
                        
                except Exception:
                    # If parsing fails, just use the whole line as title
                    paper_info["title"] = first_line
            
            # Extract information from subsequent lines
            for line in lines[1:]:
                line = line.strip()
                
                # Look for summary and relevance in different formats
                if "summary:" in line.lower():
                    paper_info["summary"] = line.split(":", 1)[1].strip()
                elif "relevance:" in line.lower():
                    paper_info["relevance"] = line.split(":", 1)[1].strip()
                # If line contains author or publication info not caught earlier
                elif "author" in line.lower() and not paper_info["authors"]:
                    paper_info["authors"] = line.split(":", 1)[1].strip() if ":" in line else line
                elif "journal" in line.lower() and not paper_info["journal"]:
                    paper_info["journal"] = line.split(":", 1)[1].strip() if ":" in line else line
                elif "year" in line.lower() and not paper_info["year"]:
                    paper_info["year"] = line.split(":", 1)[1].strip() if ":" in line else line
            
            # If we at least have a title, add the paper
            if paper_info["title"]:
                papers.append(paper_info)
        
        # If no papers were found using structured parsing, try a simpler approach
        if not papers and "paper" in papers_section.lower():
            # Just extract what look like paper titles - any lines that might be titles
            for line in papers_section.split('\n'):
                line = line.strip()
                if line and len(line) > 15 and not line.startswith("Brief") and not line.startswith("Relevance"):
                    # This looks like it might be a paper title
                    if line[0].isdigit() and '. ' in line:
                        title = line.split('. ', 1)[1]
                    else:
                        title = line
                    
                    papers.append({
                        "title": title,
                        "authors": "",
                        "year": "",
                        "journal": "",
                        "summary": "Details not available",
                        "relevance": "Referenced in literature review"
                    })
        
        # Fallback: If we still found no papers but the novelty assessment mentions papers
        novelty_assessment = self._extract_section(review_text, "NOVELTY ASSESSMENT:", "DIFFERENTIATION SUGGESTIONS:")
        if not papers and novelty_assessment and ("paper" in novelty_assessment.lower() or "stud" in novelty_assessment.lower() or "research" in novelty_assessment.lower()):
            # Create a placeholder entry to indicate papers exist but weren't parsed
            papers.append({
                "title": "Related work mentioned in assessment",
                "authors": "Various researchers",
                "year": "Recent",
                "journal": "Multiple sources",
                "summary": "The literature review identified relevant work but specific papers couldn't be automatically extracted.",
                "relevance": "See novelty assessment for details on how this research relates to existing literature."
            })
        
        # Extract other sections
        novelty_assessment = self._extract_section(review_text, "NOVELTY ASSESSMENT:", "DIFFERENTIATION SUGGESTIONS:")
        
        # Extract differentiation suggestions
        differentiation_section = self._extract_section(review_text, "DIFFERENTIATION SUGGESTIONS:", "EMERGING TRENDS:")
        differentiation_suggestions = []
        
        for line in differentiation_section.strip().split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or (len(line) > 1 and line[0] == '-')):
                # Remove the number or dash prefix
                suggestion = line[1:].strip() if line[0].isdigit() else line[2:].strip()
                differentiation_suggestions.append(suggestion)
        
        # Extract emerging trends
        emerging_trends = self._extract_section(review_text, "EMERGING TRENDS:", "NOVELTY SCORE:")
        
        # Extract novelty score with better error handling
        novelty_score_section = self._extract_section(review_text, "NOVELTY SCORE:", "KEY RECOMMENDATIONS")
        novelty_score = 5.0  # Default score
        
        try:
            # Look for a number in the section
            import re
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
        
        for line in recommendations_section.strip().split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or (len(line) > 1 and line[0] == '-')):
                # Remove the number or dash prefix
                rec = line[1:].strip() if line[0].isdigit() else line[2:].strip()
                recommendations.append(rec)
        
        # Extract summary
        summary = self._extract_section(review_text, "SUMMARY:", "")
        
        # Create and return feedback object
        return LiteratureFeedback(
            similar_papers=papers,
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
        for i, paper in enumerate(feedback.similar_papers, 1):
            result += f"{i}. **{paper['title']}** by {paper['authors']} ({paper['year']}) - {paper['journal']}\n"
            result += f"   Summary: {paper['summary']}\n"
            result += f"   Relevance: {paper['relevance']}\n\n"
        
        result += "## INNOVATION OPPORTUNITIES\n"
        for i, suggestion in enumerate(feedback.differentiation_suggestions, 1):
            result += f"{i}. {suggestion}\n"
        
        result += f"\n## EMERGING RESEARCH TRENDS\n{feedback.emerging_trends}\n"
        
        result += "\n## KEY RECOMMENDATIONS FOR IMPROVING NOVELTY\n"
        for i, rec in enumerate(feedback.recommended_improvements, 1):
            result += f"{i}. {rec}\n"
        
        result += f"\n## OVERALL ASSESSMENT\n{feedback.summary}\n"
        
        return result