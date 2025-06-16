# Astronomy Research Assistant MCP Server

This directory contains a Model Context Protocol (MCP) server that exposes the Astronomy Research Assistant functionality as tools that can be called by MCP clients.

## Overview

The MCP server wraps the core functionality of the Astronomy Research Assistant into standardized tools that can be used by any MCP-compatible client. This allows other AI agents to leverage the astronomy research capabilities programmatically.

## Available Tools

### 1. `generate_idea`
Generates a novel and structured astronomy research idea based on student profile.

**Parameters:**
- `provider` (required): LLM provider ("google", "azure", "claude")
- `api_key` (required): API key for the selected provider
- `temperature` (optional): Temperature for the LLM (default: 0.5)
- `interests` (required): Comma-separated list of student interests
- `skill_level` (required): Student's skill level (e.g., "undergraduate", "graduate")
- `resources` (required): Comma-separated list of available resources
- `time_frame` (required): Project time frame (e.g., "1 year", "6 months")

### 2. `structure_idea`
Takes a raw, unstructured user idea and formalizes it into a structured research proposal.

**Parameters:**
- `provider` (required): LLM provider
- `api_key` (required): API key for the selected provider
- `temperature` (optional): Temperature for the LLM
- `user_idea` (required): The raw user idea string to structure

### 3. `literature_review`
Performs a literature search against Semantic Scholar to assess novelty and provide context.

**Parameters:**
- `provider` (required): LLM provider
- `api_key` (required): API key for the selected provider
- `temperature` (optional): Temperature for the LLM
- `proposal_json` (required): Research proposal as JSON string or object

### 4. `expert_feedback`
Provides expert peer review feedback simulating review from an experienced professor.

**Parameters:**
- `provider` (required): LLM provider
- `api_key` (required): API key for the selected provider
- `temperature` (optional): Temperature for the LLM
- `proposal_json` (required): Research proposal as JSON string or object

### 5. `improve_idea`
Generates an improved version of a research proposal based on expert and literature feedback.

**Parameters:**
- `provider` (required): LLM provider
- `api_key` (required): API key for the selected provider
- `temperature` (optional): Temperature for the LLM
- `original_proposal_json` (required): Original research proposal as JSON
- `reflection_json` (required): Expert feedback as JSON
- `literature_json` (optional): Literature review feedback as JSON

### 6. `full_pipeline`
Executes the complete research idea refinement pipeline from raw idea to improved proposal.

**Parameters:**
- `provider` (required): LLM provider
- `api_key` (required): API key for the selected provider
- `temperature` (optional): Temperature for the LLM
- `user_idea` (required): The raw user idea to process through the full pipeline

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have API keys for your chosen LLM provider:
   - **Google**: Gemini API key
   - **Azure**: Azure OpenAI API key
   - **Claude**: Anthropic API key

## Running the Server

Start the MCP server:
```bash
python mcp_server.py
```

The server will run and listen for MCP protocol messages via stdin/stdout.

## Usage Examples

See `mcp_example.py` for detailed examples of how to call each tool. Here's a basic example:

```python
# Example tool call for generating an idea
{
    "provider": "google",
    "api_key": "your-api-key-here",
    "temperature": 0.7,
    "interests": "galaxy formation, cosmology, dark matter",
    "skill_level": "undergraduate", 
    "resources": "Python, public datasets, university computing cluster",
    "time_frame": "1 year"
}
```

## Integration with MCP Clients

This server can be integrated with various MCP clients:

### Claude Desktop
Add to your Claude Desktop configuration:
```json
{
  "mcpServers": {
    "astronomy-research": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"]
    }
  }
}
```

### VS Code MCP Extension
Configure the extension to point to this server executable.

### Custom Applications
Use any MCP client library to connect to this server and call its tools programmatically.

## Architecture

The MCP server wraps three core agent classes:

- **IdeaAgent**: Handles idea generation, structuring, and improvement
- **LiteratureAgent**: Performs literature searches via Semantic Scholar API
- **AstronomyReflectionAgent**: Provides expert feedback and peer review

Each tool is implemented as an async function decorated with `@server.call_tool()` and includes proper error handling and parameter validation.

## Error Handling

All tools include comprehensive error handling and will return informative error messages if:
- Required parameters are missing
- API keys are invalid
- LLM requests fail
- JSON parsing errors occur

## Output Format

Tools return either:
- `JSONContent`: Structured data results
- `TextContent`: Error messages or plain text responses

All successful responses include the complete structured data from the underlying agents.

## Development

To extend the server with additional tools:

1. Implement the tool function with `@server.call_tool()` decorator
2. Add parameter validation using `_validate_required_params()`
3. Add the tool definition to the `list_tools()` function
4. Update this documentation

## Troubleshooting

**Server won't start:**
- Ensure all dependencies are installed
- Check that Python version is 3.8+

**Tool calls fail:**
- Verify API keys are valid and have sufficient quota
- Check that all required parameters are provided
- Review error messages for specific issues

**Literature search fails:**
- Semantic Scholar API may be rate-limited or unavailable
- Network connectivity issues

For additional help, refer to the main project README.md or check the agent implementation files for more details on the underlying functionality. 