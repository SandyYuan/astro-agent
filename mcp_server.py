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
    Generates a novel and structured astronomy research idea in JSON format.
    Takes a user's profile including interests, skill level, available resources, and time frame as input.
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
    Takes a raw, unstructured user idea as a string and formalizes it into a
    structured, scientifically-grounded research proposal in JSON format.
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
    Accepts a research proposal in JSON format. It performs a literature search
    against the Semantic Scholar database to assess novelty and returns a
    structured feedback object in JSON format.
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
    Accepts a research proposal in JSON format. It provides expert feedback
    simulating a peer review from an experienced professor, returning the
    feedback in a structured JSON object.
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
    Generates an improved version of a research proposal. It takes the original
    JSON proposal and incorporates feedback from the expert reflection tool and
    optionally the literature review tool.
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
    Executes the full, original research idea refinement pipeline. It takes a
    raw user idea and returns a comprehensive JSON object containing the initial
    structured idea, the literature review, expert feedback, and the final
    improved proposal.
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
                description="Generates a novel and structured astronomy research idea based on student profile",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "The LLM provider to use"
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "description": "Temperature for the LLM"
                        },
                        "interests": {
                            "type": "string",
                            "description": "Comma-separated list of student interests"
                        },
                        "skill_level": {
                            "type": "string",
                            "description": "Student's skill level (e.g., 'undergraduate', 'graduate')"
                        },
                        "resources": {
                            "type": "string",
                            "description": "Comma-separated list of available resources"
                        },
                        "time_frame": {
                            "type": "string",
                            "description": "Project time frame (e.g., '1 year', '6 months')"
                        }
                    },
                    "required": ["interests", "skill_level", "resources", "time_frame"]
                }
            ),
            Tool(
                name="structure_idea",
                description="Takes a raw user idea and structures it into a formal research proposal",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "The LLM provider to use"
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "description": "Temperature for the LLM"
                        },
                        "user_idea": {
                            "type": "string",
                            "description": "The raw user idea string to structure"
                        }
                    },
                    "required": ["user_idea"]
                }
            ),
            Tool(
                name="literature_review",
                description="Performs literature search and assessment for a research proposal",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "The LLM provider to use"
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "description": "Temperature for the LLM"
                        },
                        "proposal_json": {
                            "type": ["string", "object"],
                            "description": "Research proposal as JSON string or object"
                        }
                    },
                    "required": ["proposal_json"]
                }
            ),
            Tool(
                name="expert_feedback",
                description="Provides expert peer review feedback on a research proposal",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "The LLM provider to use"
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "description": "Temperature for the LLM"
                        },
                        "proposal_json": {
                            "type": ["string", "object"],
                            "description": "Research proposal as JSON string or object"
                        }
                    },
                    "required": ["proposal_json"]
                }
            ),
            Tool(
                name="improve_idea",
                description="Improves a research proposal based on expert and literature feedback",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "The LLM provider to use"
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "description": "Temperature for the LLM"
                        },
                        "original_proposal_json": {
                            "type": ["string", "object"],
                            "description": "Original research proposal as JSON string or object"
                        },
                        "reflection_json": {
                            "type": ["string", "object"],
                            "description": "Expert feedback as JSON string or object"
                        },
                        "literature_json": {
                            "type": ["string", "object"],
                            "description": "Literature review feedback as JSON string or object (optional)"
                        }
                    },
                    "required": ["original_proposal_json", "reflection_json"]
                }
            ),
            Tool(
                name="full_pipeline",
                description="Executes the complete research idea refinement pipeline from raw idea to improved proposal",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["google", "azure", "claude"],
                            "default": "google",
                            "description": "The LLM provider to use"
                        },
                        "temperature": {
                            "type": "number",
                            "default": 0.5,
                            "description": "Temperature for the LLM"
                        },
                        "user_idea": {
                            "type": "string",
                            "description": "The raw user idea to process through the full pipeline"
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