"""
Astronomy Research Idea Assistant MCP Server

This Model Context Protocol (MCP) server provides AI-powered tools for developing
astronomy research proposals. It offers a complete pipeline from idea generation
to peer review and improvement.

Available Tools:
1. generate_idea - Generate novel research ideas from student profiles
2. structure_idea - Formalize raw ideas into structured proposals
3. literature_review - Automated literature search and novelty assessment
4. expert_feedback - Simulated peer review feedback
5. improve_idea - Enhance proposals using feedback
6. full_pipeline - Complete end-to-end development workflow

The server requires API keys for LLM providers (Google Gemini, Azure/OpenAI, or Anthropic).
Set environment variables: GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
"""

import asyncio
import json
import os
from typing import Dict, Any, List
from dataclasses import asdict

# MCP imports
import mcp.server.stdio
import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions

# Import agent classes
from idea_agent import IdeaAgent
from literature_agent import LiteratureAgent
from reflection_agent import AstronomyReflectionAgent

# Global server instance
server = Server("astronomy-idea-assistant")

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
    
    # Note: Removed debug print statements as they interfere with MCP stdio communication

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
            raise ValueError("No API keys configured. Please set environment variables: GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY")
    
    return provider, api_key

def _get_temperature(params: Dict[str, Any]) -> float:
    """Extracts temperature from parameters, with a default."""
    return params.get('temperature', 0.5)

def _parse_json_input(data: Any) -> Dict[str, Any]:
    """Parse JSON input, handling both strings and objects."""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {"description": data}
    return data

# --- MCP Tool Implementations ---

@server.call_tool()
async def generate_idea(arguments: Dict[str, Any]) -> List[types.TextContent]:
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
        
        return [types.TextContent(type="text", text=json.dumps(result))]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error generating idea: {str(e)}")]

@server.call_tool()
async def structure_idea(arguments: Dict[str, Any]) -> List[types.TextContent]:
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
        
        return [types.TextContent(type="text", text=json.dumps(result))]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error structuring idea: {str(e)}")]

@server.call_tool()
async def literature_review(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Performs comprehensive literature search and novelty assessment for a research proposal.
    
    This tool conducts an automated literature review by searching the Semantic Scholar database
    for papers related to the research proposal. It analyzes the search results to assess the
    novelty of the proposed research and provides specific suggestions for differentiation.
    
    The process includes:
    - Intelligent keyword extraction from the research proposal
    - Systematic search across multiple relevant astronomy subfields
    - Analysis of paper abstracts, citations, and publication dates
    - Assessment of research novelty and gap identification
    - Specific recommendations for research differentiation
    - Summary of key findings and related work
    
    This automated review helps researchers understand the current state of their field,
    identify potential overlaps with existing work, and find opportunities for novel
    contributions. The feedback is structured to be actionable and specific.
    
    Input Parameters:
    - proposal_json (required): The structured research proposal to review (JSON string or object)
      Should be a complete proposal with title, methodology, research question, etc.
      Can be output from 'generate_idea' or 'structure_idea' tools
    - provider (optional): LLM provider to use ("google", "azure", "claude") - defaults to "google"
    - temperature (optional): LLM temperature for analysis (0.0-1.0) - defaults to 0.5
    
    Returns:
    JSON object containing literature review results including:
    - Novelty assessment score and explanation
    - List of highly relevant papers with summaries
    - Identified research gaps and opportunities
    - Specific suggestions for research differentiation
    - Recommended modifications to improve novelty
    """
    try:
        # Validate required parameters
        _validate_required_params(arguments, ['proposal_json'])
        
        provider, api_key = _get_provider_and_key(arguments)
        temperature = _get_temperature(arguments)
        
        # Parse proposal if it's a JSON string
        proposal = _parse_json_input(arguments['proposal_json'])
        
        agent = LiteratureAgent(api_key=api_key, provider=provider, temperature=temperature)
        result = agent.run_literature_search(research_idea=proposal)
        
        return [types.TextContent(type="text", text=json.dumps(asdict(result)))]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error performing literature review: {str(e)}")]

@server.call_tool()
async def expert_feedback(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Provides comprehensive expert peer review feedback simulating evaluation by an experienced astronomy professor.
    
    This tool simulates the peer review process by providing detailed, constructive feedback
    on a research proposal from multiple expert perspectives. The feedback covers scientific
    rigor, methodology, feasibility, significance, and presentation quality.
    
    The simulated expert review includes:
    - Assessment of scientific significance and impact potential
    - Evaluation of proposed methodology and approach
    - Analysis of feasibility given stated resources and timeline
    - Identification of potential challenges and limitations
    - Suggestions for methodology improvements
    - Recommendations for strengthening the proposal
    - Overall assessment with specific scores and rankings
    
    This feedback helps researchers anticipate potential reviewer concerns, improve their
    proposals before submission, and ensure their research meets academic standards.
    The review is designed to be constructive and actionable.
    
    Input Parameters:
    - proposal_json (required): The research proposal to review (JSON string or object)
      Should be a structured proposal with methodology, timeline, resources, etc.
      Can be output from previous pipeline steps or standalone proposals
    - provider (optional): LLM provider to use ("google", "azure", "claude") - defaults to "google"
    - temperature (optional): LLM temperature for feedback generation (0.0-1.0) - defaults to 0.5
    
    Returns:
    JSON object containing structured expert feedback with:
    - Overall assessment scores and recommendations
    - Detailed comments on each aspect of the proposal
    - Specific suggestions for improvement
    - Identified strengths and weaknesses
    - Recommendations for next steps
    """
    try:
        # Validate required parameters
        _validate_required_params(arguments, ['proposal_json'])
        
        provider, api_key = _get_provider_and_key(arguments)
        temperature = _get_temperature(arguments)
        
        # Parse proposal if it's a JSON string
        proposal = _parse_json_input(arguments['proposal_json'])
        
        agent = AstronomyReflectionAgent(api_key=api_key, provider=provider, temperature=temperature)
        result = agent.provide_feedback(research_proposal=proposal)
        
        return [types.TextContent(type="text", text=json.dumps(asdict(result)))]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error generating expert feedback: {str(e)}")]

@server.call_tool()
async def improve_idea(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Generates an enhanced version of a research proposal by incorporating expert feedback and literature insights.
    
    This tool takes the results from literature review and expert feedback to create an
    improved version of the original research proposal. It intelligently incorporates
    suggestions, addresses identified weaknesses, and enhances the overall quality and
    feasibility of the research plan.
    
    The improvement process includes:
    - Integration of literature review findings and gap analysis
    - Incorporation of expert feedback and recommendations
    - Resolution of identified methodology concerns
    - Enhancement of research questions and hypotheses
    - Refinement of timelines and resource allocation
    - Strengthening of scientific justification
    - Improvement of overall presentation and clarity
    
    This creates a refined, publication-ready research proposal that addresses peer
    review concerns and leverages current knowledge in the field. The improved proposal
    maintains the core vision while enhancing scientific rigor and feasibility.
    
    Input Parameters:
    - original_proposal_json (required): The initial research proposal (JSON string or object)
      Should be the original structured proposal that needs improvement
    - reflection_json (required): Expert review feedback (JSON string or object)
      Should be output from the 'expert_feedback' tool
    - literature_json (optional): Literature review results (JSON string or object)
      Should be output from the 'literature_review' tool. Highly recommended for best results.
    - provider (optional): LLM provider to use ("google", "azure", "claude") - defaults to "google"
    - temperature (optional): LLM temperature for improvement generation (0.0-1.0) - defaults to 0.5
    
    Returns:
    JSON object containing the improved research proposal with:
    - Enhanced methodology addressing expert concerns
    - Refined research questions based on literature gaps
    - Improved timeline and resource allocation
    - Strengthened scientific justification
    - Better integration with current research landscape
    """
    try:
        # Validate required parameters
        _validate_required_params(arguments, ['original_proposal_json', 'reflection_json'])
        
        provider, api_key = _get_provider_and_key(arguments)
        temperature = _get_temperature(arguments)
        
        # Parse JSON inputs
        original_proposal = _parse_json_input(arguments['original_proposal_json'])
        expert_feedback = _parse_json_input(arguments['reflection_json'])
        literature_feedback = _parse_json_input(arguments.get('literature_json', {}))
        
        agent = IdeaAgent(api_key=api_key, provider=provider, temperature=temperature)
        result = agent.improve_idea(reflection_feedback=expert_feedback, literature_feedback=literature_feedback)
        
        return [types.TextContent(type="text", text=json.dumps(result))]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error improving idea: {str(e)}")]

@server.call_tool()
async def full_pipeline(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Executes the complete end-to-end research idea development pipeline in a single operation.
    
    This tool provides a comprehensive, automated workflow that takes either a raw user idea
    or basic parameters and produces a fully-developed, peer-reviewed research proposal.
    It combines all the individual tools in a logical sequence to deliver a complete
    research development experience.
    
    The full pipeline includes:
    1. Idea Generation or Structuring: Creates or formalizes the initial research concept
    2. Literature Review: Conducts comprehensive analysis of existing work
    3. Expert Feedback: Provides detailed peer review assessment
    4. Idea Improvement: Integrates feedback to create an enhanced proposal
    5. Final Integration: Compiles all results into a comprehensive package
    
    This end-to-end approach ensures that the final research proposal is:
    - Scientifically rigorous and well-grounded
    - Novel and differentiated from existing work
    - Methodologically sound and feasible
    - Aligned with current research standards
    - Ready for further development or submission
    
    The pipeline is especially useful for:
    - Students developing their first research proposals
    - Researchers exploring new fields or methodologies
    - Quick prototyping of research concepts
    - Comprehensive proposal development in one step
    
    Input Parameters:
    Either provide a raw idea OR student profile parameters:
    
    For idea structuring:
    - user_idea (required if no profile): Raw research idea description
    
    For idea generation:
    - interests (required if no user_idea): Student's research interests (comma-separated)
    - skill_level (required if no user_idea): Student's skill level
    - resources (required if no user_idea): Available resources (comma-separated)
    - time_frame (required if no user_idea): Project timeline
    
    Optional parameters for all modes:
    - max_papers (optional): Maximum papers for literature review (default: 20)
    - review_depth (optional): Expert review depth ("brief", "standard", "comprehensive")
    - provider (optional): LLM provider ("google", "azure", "claude") - defaults to "google"
    - temperature (optional): LLM temperature (0.0-1.0) - defaults to 0.5
    
    Returns:
    JSON object containing complete pipeline results:
    - initial_proposal: The starting research proposal
    - literature_review: Comprehensive literature analysis and novelty assessment
    - expert_feedback: Detailed peer review with scores and recommendations
    - improved_proposal: Final enhanced proposal incorporating all feedback
    - pipeline_summary: Overview of improvements and key insights
    """
    try:
        provider, api_key = _get_provider_and_key(arguments)
        temperature = _get_temperature(arguments)
        
        # Initialize agents
        idea_agent = IdeaAgent(api_key=api_key, provider=provider, temperature=temperature)
        lit_agent = LiteratureAgent(api_key=api_key, provider=provider, temperature=temperature)
        reflection_agent = AstronomyReflectionAgent(api_key=api_key, provider=provider, temperature=temperature)
        
        # Step 1: Generate or structure the initial proposal
        if 'user_idea' in arguments:
            # Structure existing idea
            structured_proposal = idea_agent.structure_and_rephrase_idea(user_idea=arguments['user_idea'])
        else:
            # Generate new idea
            _validate_required_params(arguments, ['interests', 'skill_level', 'resources', 'time_frame'])
            interests = [i.strip() for i in arguments['interests'].split(',')]
            resources = [r.strip() for r in arguments['resources'].split(',')]
            
            structured_proposal = idea_agent.generate_initial_idea(
                student_interests=interests,
                skill_level=arguments['skill_level'],
                time_frame=arguments['time_frame'],
                available_resources=resources
            )
        
        # Step 2: Literature Review
        lit_feedback = lit_agent.run_literature_search(research_idea=structured_proposal)
        
        # Step 3: Expert Feedback
        expert_feedback_result = reflection_agent.provide_feedback(research_proposal=structured_proposal)
        
        # Step 4: Improve Idea
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
        
        return [types.TextContent(type="text", text=json.dumps(final_result))]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error running full pipeline: {str(e)}")]

# --- MCP Server Setup ---

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available tools."""
    return [
        types.Tool(
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
        types.Tool(
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
        types.Tool(
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
        types.Tool(
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
        types.Tool(
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
        types.Tool(
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

async def main():
    """Main entry point for the MCP server."""
    # Load API keys on startup
    _load_api_keys()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="astronomy-idea-assistant",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 