import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import asdict

# MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    JSONContent,
)

# Import agent classes
from idea_agent import IdeaAgent
from literature_agent import LiteratureAgent, LiteratureFeedback
from reflection_agent import AstronomyReflectionAgent, ProposalFeedback
from llm_client import LLMClient

# Global server instance
server = Server("astronomy-research-assistant")

# Global API key storage
API_KEYS = {
    'google': None,
    'azure': None, 
    'claude': None
}

def _load_api_keys():
    """Load API keys from environment variables."""
    API_KEYS['google'] = os.getenv('GEMINI_API_KEY')
    API_KEYS['azure'] = os.getenv('AZURE_OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
    API_KEYS['claude'] = os.getenv('ANTHROPIC_API_KEY')
    
    # Print which keys were found (without revealing the actual keys)
    loaded_keys = [provider for provider, key in API_KEYS.items() if key is not None]
    if loaded_keys:
        print(f"Loaded API keys for providers: {', '.join(loaded_keys)}")
    else:
        print("Warning: No API keys found in environment variables")
        print("Set GEMINI_API_KEY, ANTHROPIC_API_KEY, and/or OPENAI_API_KEY environment variables")

# --- Helper Functions ---

def _validate_required_params(params: Dict[str, Any], required: List[str]) -> None:
    """Validates that required parameters are present."""
    missing = [param for param in required if param not in params or params[param] is None]
    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")

def _get_provider_and_key(params: Dict[str, Any]) -> tuple[str, str]:
    """Extracts provider and gets the corresponding API key from server config."""
    provider = params.get('provider', 'google')
    api_key = API_KEYS.get(provider)
    
    if not api_key:
        available_providers = [p for p, k in API_KEYS.items() if k is not None]
        if available_providers:
            raise ValueError(f"No API key configured for provider '{provider}'. Available providers: {', '.join(available_providers)}")
        else:
            raise ValueError(f"No API keys configured. Please set environment variables: GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY")
    
    return provider, api_key

def _get_temperature(params: Dict[str, Any]) -> float:
    """Extracts temperature from parameters, with a default."""
    return params.get('temperature', 0.5)

# --- MCP Tool Implementations ---

@server.call_tool()
async def generate_idea(arguments: Dict[str, Any]) -> List[TextContent | JSONContent]:
    """
    Generates a novel and structured astronomy research idea tailored to a student's profile.
    
    This tool creates a completely new research proposal from scratch based on the student's 
    interests, skill level, available resources, and time constraints. It uses AI to generate
    scientifically sound and feasible research ideas that are appropriate for the student's
    background and circumstances.
    
    The generated idea includes:
    - A descriptive title for the research project
    - Relevant astronomy subfields
    - A clear, testable research question
    - Specific methodology with concrete datasets and tools
    - Scientific background and motivation
    - Expected outcomes and deliverables
    
    Input Parameters:
    - interests (required): Comma-separated list of astronomy topics the student is interested in
      (e.g., "galaxy formation, cosmology, dark matter", "exoplanets, stellar evolution")
    - skill_level (required): Student's current skill level - affects complexity of suggestions
      (e.g., "undergraduate", "graduate", "postdoc", "beginner", "intermediate", "advanced")
    - resources (required): Comma-separated list of available resources and tools
      (e.g., "Python, public datasets, university computing cluster", "telescope access, IDL")
    - time_frame (required): Expected project duration
      (e.g., "1 year", "6 months", "2 years", "summer project")
    - provider (optional): LLM provider to use ("google", "azure", "claude") - defaults to "google"
    - temperature (optional): LLM temperature for creativity (0.0-1.0) - defaults to 0.5
    
    Returns:
    JSON object containing the complete structured research proposal with all fields populated.
    """
    try:
        # Validate required parameters
        _validate_required_params(arguments, [
            'interests', 'skill_level', 'resources', 'time_frame'
        ])
        
        provider, api_key = _get_provider_and_key(arguments)
        temperature = _get_temperature(arguments)
        
        agent = IdeaAgent(api_key=api_key, provider=provider, temperature=temperature)
        
        interests = [i.strip() for i in arguments['interests'].split(',')]
        resources = [r.strip() for r in arguments['resources'].split(',')]
        
        result = agent.generate_initial_idea(
            student_interests=interests,
            skill_level=arguments['skill_level'],
            time_frame=arguments['time_frame'],
            available_resources=resources
        )
        
        return [JSONContent(content=result)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error generating idea: {str(e)}")]

@server.call_tool()
async def structure_idea(arguments: Dict[str, Any]) -> List[TextContent | JSONContent]:
    """
    Transforms a raw, unstructured user idea into a formal, scientifically-grounded research proposal.
    
    This tool takes conversational input describing a research idea and converts it into a 
    structured format suitable for academic evaluation. It interprets the user's intent,
    fills in missing details with reasonable scientific assumptions, and organizes the
    information into a standardized research proposal format.
    
    The tool does NOT create new ideas - it only formalizes and structures existing ideas
    provided by the user. It's particularly useful for:
    - Converting informal descriptions into formal proposals
    - Clarifying vague research concepts
    - Adding scientific rigor to preliminary ideas
    - Preparing ideas for literature review and expert feedback
    
    The structured output includes:
    - A concise, descriptive project title
    - Relevant astronomy subfields classification
    - A clear, testable research question
    - Specific proposed methodology with datasets and tools
    - Scientific background explaining the importance
    - Expected concrete outcomes and deliverables
    
    Input Parameters:
    - user_idea (required): Raw description of the research idea in natural language
      Can be informal, conversational, or preliminary. Examples:
      "I want to study galaxy formation using machine learning"
      "Can we detect exoplanets by looking at stellar brightness variations?"
      "I'm interested in how dark matter affects galaxy clusters"
    - provider (optional): LLM provider to use ("google", "azure", "claude") - defaults to "google"
    - temperature (optional): LLM temperature for interpretation (0.0-1.0) - defaults to 0.5
    
    Returns:
    JSON object containing the structured research proposal with standardized fields.
    Use this output for subsequent literature review and expert feedback steps.
    """
    try:
        # Validate required parameters
        _validate_required_params(arguments, ['user_idea'])
        
        provider, api_key = _get_provider_and_key(arguments)
        temperature = _get_temperature(arguments)
        
        agent = IdeaAgent(api_key=api_key, provider=provider, temperature=temperature)
        result = agent.structure_and_rephrase_idea(user_idea=arguments['user_idea'])
        
        return [JSONContent(content=result)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error structuring idea: {str(e)}")]

@server.call_tool()
async def literature_review(arguments: Dict[str, Any]) -> List[TextContent | JSONContent]:
    """
    Performs comprehensive literature search and novelty assessment for a research proposal.
    
    This tool conducts an automated literature review by searching the Semantic Scholar database
    for papers related to the research proposal. It analyzes the search results to assess the
    novelty of the proposed research and provides specific suggestions for differentiation.
    
    The process includes:
    1. Extracting key terms from the research proposal
    2. Searching Semantic Scholar's academic database
    3. Analyzing retrieved papers for relevance and similarity
    4. Assessing the novelty of the proposed research (1-10 scale)
    5. Identifying gaps in existing literature
    6. Suggesting ways to differentiate the research
    7. Highlighting emerging trends in the field
    
    This tool is essential for:
    - Validating research novelty before starting a project
    - Understanding the current state of research in the field
    - Identifying opportunities for original contributions
    - Avoiding duplication of existing work
    - Finding related work to cite and build upon
    
    Input Parameters:
    - proposal_json (required): Complete structured research proposal as JSON object or string
      Should contain at minimum: title, research question, and methodology
      Typically this is the output from generate_idea or structure_idea tools
    - provider (optional): LLM provider for analysis ("google", "azure", "claude") - defaults to "google"
    - temperature (optional): LLM temperature for analysis (0.0-1.0) - defaults to 0.5
    
    Returns:
    JSON object containing:
    - similar_papers: List of relevant papers found with titles, authors, and abstracts
    - novelty_score: Numerical assessment (1-10) of research novelty
    - novelty_assessment: Detailed explanation of the novelty evaluation
    - differentiation_suggestions: Specific recommendations for making research unique
    - emerging_trends: Current trends in the research area
    - recommended_improvements: Suggestions for enhancing the proposal
    - summary: Overall assessment and recommendations
    
    Note: This tool requires internet access to query Semantic Scholar's API.
    """
    try:
        # Validate required parameters
        _validate_required_params(arguments, ['proposal_json'])
        
        provider, api_key = _get_provider_and_key(arguments)
        temperature = _get_temperature(arguments)
        
        # Parse the proposal JSON
        if isinstance(arguments['proposal_json'], str):
            proposal = json.loads(arguments['proposal_json'])
        else:
            proposal = arguments['proposal_json']
            
        agent = LiteratureAgent(api_key=api_key, provider=provider, temperature=temperature)
        result = agent.run_literature_search(research_idea=proposal)
        
        return [JSONContent(content=asdict(result))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error performing literature review: {str(e)}")]

@server.call_tool()
async def expert_feedback(arguments: Dict[str, Any]) -> List[TextContent | JSONContent]:
    """
    Provides comprehensive expert peer review feedback simulating evaluation by an experienced astronomy professor.
    
    This tool analyzes a research proposal from the perspective of an expert reviewer, providing
    the type of detailed, constructive feedback typically received during academic peer review.
    The AI acts as a senior astronomy professor with deep knowledge of research methodology,
    scientific validity, and practical feasibility considerations.
    
    The expert evaluation covers:
    - Scientific validity and theoretical soundness
    - Methodological appropriateness and rigor
    - Feasibility given available resources and timeline
    - Novelty and potential impact of the research
    - Clarity and completeness of the proposal
    - Identification of potential challenges and limitations
    - Specific recommendations for improvement
    
    The feedback is structured to help researchers:
    - Identify strengths to build upon
    - Recognize potential weaknesses before starting
    - Understand methodological considerations
    - Gauge project feasibility realistically
    - Improve proposal quality for funding applications
    - Prepare for actual peer review processes
    
    Input Parameters:
    - proposal_json (required): Complete structured research proposal as JSON object or string
      Should include: title, research question, methodology, background, expected outcomes
      May also include: skill_level, time_frame, available resources for context
      Typically this is the output from generate_idea or structure_idea tools
    - provider (optional): LLM provider for analysis ("google", "azure", "claude") - defaults to "google"
    - temperature (optional): LLM temperature for evaluation (0.0-1.0) - defaults to 0.5
    
    Returns:
    JSON object containing:
    - scientific_validity: Dict with 'strengths' and 'concerns' arrays for scientific aspects
    - methodology: Dict with 'strengths' and 'concerns' arrays for methodological aspects
    - novelty_assessment: Detailed evaluation of research novelty and originality
    - impact_assessment: Analysis of potential scientific impact and significance
    - feasibility_assessment: Evaluation of project feasibility given constraints
    - recommendations: Array of specific, actionable improvement suggestions
    - summary: Overall assessment with clear recommendation on proceeding
    
    Use this feedback in combination with literature review results for comprehensive evaluation.
    """
    try:
        # Validate required parameters
        _validate_required_params(arguments, ['proposal_json'])
        
        provider, api_key = _get_provider_and_key(arguments)
        temperature = _get_temperature(arguments)

        # Parse the proposal JSON
        if isinstance(arguments['proposal_json'], str):
            proposal = json.loads(arguments['proposal_json'])
        else:
            proposal = arguments['proposal_json']
            
        agent = AstronomyReflectionAgent(api_key=api_key, provider=provider, temperature=temperature)
        result = agent.provide_feedback(research_proposal=proposal)
        
        return [JSONContent(content=asdict(result))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error generating expert feedback: {str(e)}")]

@server.call_tool()
async def improve_idea(arguments: Dict[str, Any]) -> List[TextContent | JSONContent]:
    """
    Generates an enhanced version of a research proposal by incorporating expert feedback and literature insights.
    
    This tool takes an original research proposal and systematically improves it based on:
    - Expert peer review feedback (from expert_feedback tool)
    - Literature review insights (from literature_review tool, optional)
    - Best practices in research design and methodology
    
    The improvement process addresses:
    - Scientific validity concerns raised by expert review
    - Methodological weaknesses and gaps
    - Novelty and differentiation opportunities from literature
    - Feasibility issues and practical constraints
    - Clarity and completeness of the proposal
    
    The tool produces a refined proposal that:
    - Incorporates suggested improvements
    - Addresses identified concerns and limitations
    - Enhances methodological rigor
    - Improves scientific justification
    - Increases likelihood of success and impact
    
    This is typically the final step in the research idea development pipeline,
    producing a polished proposal ready for implementation or funding applications.
    
    Input Parameters:
    - original_proposal_json (required): The initial research proposal as JSON object or string
      This is typically output from generate_idea or structure_idea tools
    - reflection_json (required): Expert feedback as JSON object or string
      This must be output from the expert_feedback tool
    - literature_json (optional): Literature review results as JSON object or string
      If provided, should be output from the literature_review tool
      Including this enhances the improvement process with literature insights
    - provider (optional): LLM provider for improvement ("google", "azure", "claude") - defaults to "google"
    - temperature (optional): LLM temperature for revision (0.0-1.0) - defaults to 0.5
    
    Returns:
    JSON object containing the improved research proposal with the same structure as the original
    but with enhanced content addressing the feedback. All sections are refined and expanded
    based on the provided recommendations.
    
    Typical workflow:
    1. generate_idea or structure_idea → original proposal
    2. expert_feedback → expert analysis  
    3. literature_review → literature insights (optional)
    4. improve_idea → final enhanced proposal
    """
    try:
        # Validate required parameters
        _validate_required_params(arguments, [
            'original_proposal_json', 'reflection_json'
        ])
        
        provider, api_key = _get_provider_and_key(arguments)
        temperature = _get_temperature(arguments)

        # Parse JSON inputs
        if isinstance(arguments['original_proposal_json'], str):
            original_proposal = json.loads(arguments['original_proposal_json'])
        else:
            original_proposal = arguments['original_proposal_json']
            
        if isinstance(arguments['reflection_json'], str):
            reflection = json.loads(arguments['reflection_json'])
        else:
            reflection = arguments['reflection_json']
            
        literature = None
        if arguments.get('literature_json'):
            if isinstance(arguments['literature_json'], str):
                literature = json.loads(arguments['literature_json'])
            else:
                literature = arguments['literature_json']

        # This tool requires manually setting the agent's internal state
        agent = IdeaAgent(api_key=api_key, provider=provider, temperature=temperature)
        agent.current_idea = original_proposal
        
        result = agent.improve_idea(reflection_feedback=reflection, literature_feedback=literature)
        
        return [JSONContent(content=result)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error improving idea: {str(e)}")]

@server.call_tool()
async def full_pipeline(arguments: Dict[str, Any]) -> List[TextContent | JSONContent]:
    """
    Executes the complete end-to-end research idea development pipeline in a single operation.
    
    This comprehensive tool takes a raw research idea and processes it through the entire
    refinement pipeline, producing a complete analysis and final improved proposal. It
    orchestrates all the individual tools in sequence:
    
    Pipeline Steps:
    1. STRUCTURE: Convert raw idea into formal research proposal
    2. LITERATURE REVIEW: Search academic papers and assess novelty  
    3. EXPERT FEEDBACK: Generate peer review-style evaluation
    4. IMPROVEMENT: Create enhanced version incorporating all feedback
    
    This tool is ideal when you want:
    - Complete analysis without managing individual tool calls
    - Consistent processing through all evaluation stages
    - Comprehensive output including all intermediate results
    - Streamlined workflow for idea development
    
    The full pipeline ensures all components work together cohesively and provides
    the most thorough evaluation possible. It's particularly useful for:
    - Initial idea evaluation and development
    - Comprehensive research proposal preparation
    - Educational purposes to see the complete process
    - When you need all types of feedback simultaneously
    
    Input Parameters:
    - user_idea (required): Raw description of research idea in natural language
      Can be informal, preliminary, or conversational. Examples:
      "I want to use machine learning to find new exoplanets"
      "What if we could predict solar flares using AI?"
      "I'm curious about how galaxies form in the early universe"
    - provider (optional): LLM provider to use ("google", "azure", "claude") - defaults to "google"
    - temperature (optional): LLM temperature for all processing (0.0-1.0) - defaults to 0.5
    
    Returns:
    Comprehensive JSON object containing:
    - initial_proposal: The structured research proposal (from structure_idea)
    - literature_review: Complete literature analysis with novelty assessment
    - expert_feedback: Detailed peer review evaluation
    - improved_proposal: Final enhanced proposal incorporating all feedback
    
    Each section contains the full output from the corresponding individual tool,
    providing complete transparency into the development process.
    
    Note: This tool requires internet access for literature search and may take
    longer to complete than individual tools due to the comprehensive processing.
    """
    try:
        # Validate required parameters
        _validate_required_params(arguments, ['user_idea'])
        
        provider, api_key = _get_provider_and_key(arguments)
        temperature = _get_temperature(arguments)

        # 1. Structure Idea
        idea_agent = IdeaAgent(api_key=api_key, provider=provider, temperature=temperature)
        structured_proposal = idea_agent.structure_and_rephrase_idea(user_idea=arguments['user_idea'])
        
        # Hold the original proposal to be used by the improve_idea step
        idea_agent.current_idea = structured_proposal.copy()

        # 2. Literature Review
        lit_agent = LiteratureAgent(api_key=api_key, provider=provider, temperature=temperature)
        lit_feedback = lit_agent.run_literature_search(research_idea=structured_proposal)

        # 3. Expert Feedback
        reflect_agent = AstronomyReflectionAgent(api_key=api_key, provider=provider, temperature=temperature)
        expert_feedback_result = reflect_agent.provide_feedback(research_proposal=structured_proposal)

        # 4. Improve Idea
        improved_proposal = idea_agent.improve_idea(
            reflection_feedback=asdict(expert_feedback_result),
            literature_feedback=asdict(lit_feedback)
        )

        # 5. Compile final result
        final_result = {
            "initial_proposal": structured_proposal,
            "literature_review": asdict(lit_feedback),
            "expert_feedback": asdict(expert_feedback_result),
            "improved_proposal": improved_proposal
        }
        
        return [JSONContent(content=final_result)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error running full pipeline: {str(e)}")]

# --- MCP Server Setup ---

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List all available tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="generate_idea",
                description="Generates a novel, structured astronomy research idea tailored to a student's profile. Creates a completely new research proposal from scratch based on interests, skill level, available resources, and time constraints. Produces scientifically sound and feasible research ideas with detailed methodology, background, and expected outcomes. Essential for students who need research project suggestions or want to explore new research directions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "LLM provider to use for idea generation. Choose based on your preference and available API keys."
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Controls creativity vs consistency (0.0=conservative, 1.0=creative). Higher values generate more novel ideas."
                        },
                        "interests": {
                            "type": "string",
                            "description": "Comma-separated list of astronomy topics. Examples: 'galaxy formation, cosmology, dark matter' or 'exoplanets, stellar evolution, JWST observations'. Be specific about subfields of interest."
                        },
                        "skill_level": {
                            "type": "string",
                            "description": "Student's current skill level affecting project complexity. Use: 'undergraduate', 'graduate', 'postdoc', 'beginner', 'intermediate', or 'advanced'. Determines technical depth and resource requirements."
                        },
                        "resources": {
                            "type": "string",
                            "description": "Comma-separated list of available tools and resources. Examples: 'Python, public datasets, university computing cluster' or 'telescope access, IDL, supercomputer time'. Include programming languages, data access, computational resources."
                        },
                        "time_frame": {
                            "type": "string",
                            "description": "Expected project duration. Examples: '1 year', '6 months', '2 years', 'summer project', 'PhD thesis'. Affects project scope and complexity recommendations."
                        }
                    },
                    "required": ["interests", "skill_level", "resources", "time_frame"]
                }
            ),
            Tool(
                name="structure_idea",
                description="Transforms raw, informal research ideas into formal, scientifically-grounded proposals. Takes conversational input and converts it into structured academic format suitable for evaluation. Does NOT create new ideas - only formalizes existing ones. Ideal for converting preliminary thoughts into coherent research proposals ready for literature review and expert feedback. Essential preprocessing step before using other analysis tools.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "LLM provider for structuring the idea. Different providers may have varying interpretation styles."
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Controls interpretation creativity vs literal adherence (0.0=conservative, 1.0=creative). Lower values stick closer to original input."
                        },
                        "user_idea": {
                            "type": "string",
                            "description": "Raw research idea in natural language. Can be informal, conversational, or preliminary. Examples: 'I want to study galaxy formation using machine learning', 'Can we detect exoplanets by looking at stellar brightness?', 'I'm interested in how dark matter affects galaxy clusters'. No specific format required."
                        }
                    },
                    "required": ["user_idea"]
                }
            ),
            Tool(
                name="literature_review",
                description="Performs comprehensive automated literature review using Semantic Scholar database. Searches for relevant papers, assesses research novelty (1-10 scale), identifies gaps in existing literature, and provides specific differentiation suggestions. Essential for validating research originality, understanding current state of field, and avoiding duplication. Requires internet access. Critical step before starting any research project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "LLM provider for analyzing search results and generating insights. Affects analysis depth and style."
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Controls analysis creativity vs systematic approach (0.0=systematic, 1.0=creative). Lower values provide more structured analysis."
                        },
                        "proposal_json": {
                            "type": ["string", "object"],
                            "description": "Complete structured research proposal from generate_idea or structure_idea tools. Must contain title, research question, and methodology at minimum. Can be JSON string or parsed object. Higher quality input produces more accurate literature analysis."
                        }
                    },
                    "required": ["proposal_json"]
                }
            ),
            Tool(
                name="expert_feedback",
                description="Provides comprehensive expert peer review feedback simulating evaluation by experienced astronomy professor. Analyzes scientific validity, methodology, feasibility, novelty, and impact. Delivers the type of detailed, constructive feedback received in academic peer review. Helps identify strengths, weaknesses, and improvement opportunities before project implementation. Critical for proposal refinement and quality assurance.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "LLM provider for expert evaluation. Different providers may emphasize different aspects of review."
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Controls feedback style (0.0=conservative/strict, 1.0=creative/encouraging). Lower values provide more critical analysis."
                        },
                        "proposal_json": {
                            "type": ["string", "object"],
                            "description": "Complete structured research proposal from generate_idea or structure_idea tools. Should include title, research question, methodology, background, expected outcomes. May include skill_level, time_frame, resources for contextual evaluation. More complete proposals receive more detailed feedback."
                        }
                    },
                    "required": ["proposal_json"]
                }
            ),
            Tool(
                name="improve_idea",
                description="Generates enhanced research proposal by systematically incorporating expert feedback and literature insights. Final step in research development pipeline, producing polished proposal ready for implementation or funding applications. Addresses scientific validity concerns, methodological gaps, novelty opportunities, and feasibility issues. Requires expert feedback; literature review optional but recommended for best results.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "LLM provider for improvement process. Different providers may have varying improvement strategies and writing styles."
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Controls improvement creativity vs conservative revision (0.0=minimal changes, 1.0=creative enhancement). Moderate values recommended."
                        },
                        "original_proposal_json": {
                            "type": ["string", "object"],
                            "description": "Initial research proposal to improve. Typically output from generate_idea or structure_idea tools. Must be complete structured proposal with all standard fields."
                        },
                        "reflection_json": {
                            "type": ["string", "object"],
                            "description": "Expert feedback from expert_feedback tool. Required for improvement process. Must contain scientific validity assessment, methodology evaluation, and specific recommendations."
                        },
                        "literature_json": {
                            "type": ["string", "object"],
                            "description": "Optional literature review results from literature_review tool. When provided, enhances improvement with novelty insights and differentiation opportunities. Highly recommended for best results."
                        }
                    },
                    "required": ["original_proposal_json", "reflection_json"]
                }
            ),
            Tool(
                name="full_pipeline",
                description="Executes complete end-to-end research idea development pipeline in single operation. Processes raw idea through: (1) structuring into formal proposal, (2) literature search and novelty assessment, (3) expert peer review evaluation, (4) improvement incorporating all feedback. Ideal for comprehensive analysis without managing individual steps. Provides complete transparency with all intermediate results. Most thorough evaluation available but requires internet access and takes longer than individual tools.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "LLM provider for entire pipeline. Consistent provider ensures coherent analysis across all stages. Choose based on preference and API availability."
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Controls processing style for entire pipeline (0.0=conservative/systematic, 1.0=creative/exploratory). Affects all stages consistently."
                        },
                        "user_idea": {
                            "type": "string",
                            "description": "Raw research idea in natural language. Can be informal, preliminary, conversational. Examples: 'I want to use machine learning to find new exoplanets', 'What if we could predict solar flares using AI?', 'I'm curious about how galaxies form in early universe'. No specific format required - the more detail provided, the better the analysis."
                        }
                    },
                    "required": ["user_idea"]
                }
            )
        ]
    )

async def main():
    """Main entry point for the MCP server."""
    # Load API keys on startup
    _load_api_keys()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="astronomy-idea-assistant",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 