# AI Astronomy Idea Assistant

An AI agent that collaborate with human astronomers generate and refine research ideas through iterative feedback and analysis. We also provide an MCP interface that allows our functionalities to be incorporated into a larger agentic system. 

## Overview

This agent is a research teammate, transforming rough concepts into structured, scientifically-grounded proposals. It operates in two modes:

1.  **Idea Iteration Mode**: Engage in a stateful conversation to collaboratively refine your own research idea. The AI remembers the context of the conversation, allowing you to iteratively improve the proposal with follow-up messages.
2.  **Idea Generation Mode**: Let the AI generate a novel research idea from scratch based on your specified interests, skill level, and available resources.

In both modes, the system uses a pipeline of specialized AI agents to structure the idea, review relevant literature, provide expert feedback, and present an improved proposal.

> **Recommendation**: We recommend using a powerful, up-to-date model like Google Gemini 1.5 Pro or Claude 3.5 Sonnet as the LLM backbone for this application.

## MCP Server

We provide a **Model Context Protocol (MCP) server** that exposes all our functionality as standardized tools. This allows other AI agents and applications to programmatically access our research capabilities through the MCP protocol.

### Available MCP Tools

The MCP server provides six primary tools:

1. **`generate_idea`** - Generate novel research ideas from student profiles
2. **`structure_idea`** - Convert raw ideas into structured research proposals  
3. **`literature_review`** - Perform Semantic Scholar literature searches and novelty assessment
4. **`expert_feedback`** - Get simulated peer review feedback from an expert perspective
5. **`improve_idea`** - Enhance proposals by incorporating expert and literature feedback
6. **`full_pipeline`** - Execute the complete idea refinement workflow end-to-end

### Quick Start with MCP

1. **Install MCP dependencies:**
   ```bash
   pip install -r requirements.txt  # includes mcp library
   ```

2. **Configure API keys as environment variables:**
   ```bash
   export GEMINI_API_KEY='your-gemini-key'
   export ANTHROPIC_API_KEY='your-anthropic-key'
   export OPENAI_API_KEY='your-openai-key'
   ```

3. **Run the MCP server:**
   ```bash
   python mcp_server.py
   ```

4. **Connect MCP clients** like Claude Desktop, cursor, or custom applications.

### Integration Examples

**Claude Desktop Configuration:**
```json
{
  "mcpServers": {
    "astronomy-idea-assistant": {
      "command": "python",
      "args": ["/path/to/astro-agent/mcp_server.py"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-key",
        "ANTHROPIC_API_KEY": "your-anthropic-key",
        "OPENAI_API_KEY": "your-openai-key"
      }
    }
  }
}
```

**Example Tool Call:**
```json
{
  "tool": "generate_idea",
  "arguments": {
    "provider": "google",
    "interests": "galaxy formation, cosmology, dark matter",
    "skill_level": "undergraduate",
    "resources": "Python, public datasets, university computing cluster",
    "time_frame": "1 year"
  }
}
```

### Benefits of MCP Integration

- **Programmatic Access**: Call astronomy research tools from any MCP-compatible application
- **Agent Composition**: Integrate with larger AI agent systems and workflows
- **Standardized Interface**: Use consistent MCP protocol instead of custom APIs
- **Scalable Architecture**: Deploy as a service that multiple clients can access
- **Secure Configuration**: API keys configured at server level, not passed with each call

For detailed MCP server documentation, examples, and troubleshooting, see [`MCP_README.md`](MCP_README.md) and [`mcp_example.py`](mcp_example.py).

## Key Features

- **Conversational Memory**: In Iteration Mode, the assistant remembers the last proposal and refines it based on your feedback, creating a continuous conversational loop.
- **Dual Modes of Operation**: Choose between refining your own idea (`I have an idea`) or having the AI generate one for you (`Let AI take over`).
- **Idea Structuring & Generation**: The AI can either formalize your concept or generate a new one, complete with a research question, methodology, and expected outcomes.
- **Scientific Evaluation**: An expert AI agent reviews the proposal, providing detailed feedback on its scientific validity, methodological soundness, and feasibility.
- **Automated Literature Review**: The system searches recent scientific papers to assess the novelty of the idea and provides context from existing research.
- **Context-Aware Generation**: In Generation Mode, you can provide your skill level, interests, and available resources to receive tailored ideas.

## System Architecture

The application consists of three primary AI agents working in a pipeline:

1.  **Idea Agent**: Takes the user's raw input, structures it into a formal research concept, generates new ideas, and refines existing ideas based on feedback.
2.  **Literature Agent**: Conducts a literature search on Semantic Scholar to analyze the novelty of the structured idea.
3.  **Reflection Agent**: Evaluates the structured idea with the critical eye of an experienced astronomy professor, providing expert feedback.

## Setup Instructions

### Prerequisites

- Python 3.8+
- An API key for a supported LLM provider (Google Gemini, Anthropic Claude, or Azure OpenAI).

### Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/SandyYuan/astro-agent.git
    cd astro-agent
    ```

2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Set up your API key:
    The application will prompt you to enter your API key in the sidebar of the web interface. No local configuration files are needed.

### Running the Application

Launch the Streamlit app:
```bash
streamlit run app.py
```

## Using the Application

1.  **Configure the AI**:
    -   Open the application in your browser.
    -   In the sidebar, select your preferred LLM Provider (Google, OpenAI, or Anthropic).
    -   Enter your corresponding API key.

2.  **Choose a Mode**:
    -   **For Idea Iteration**: Click the "🧠 I have an idea" button. This is the default mode.
    -   **For Idea Generation**: Click the "💀 Let AI take over" button. Use the sidebar to configure your interests, skill level, and resources.

3.  **Interact with the Assistant**:
    -   **In Iteration Mode**: Type your initial research idea into the chat box. The assistant will provide a full analysis. You can then provide follow-up feedback (e.g., "that's interesting, but can we focus on neutron stars instead?") to refine the proposal.
    -   **In Generation Mode**: Click the "✨ Generate a New Research Idea" button to have the AI create a proposal for you based on your sidebar settings.

4.  **Receive AI Feedback**:
    -   The assistant will process the idea through its pipeline and respond with a detailed message containing:
        -   **Structured Idea**: The initial proposal.
        -   **Literature Review**: An analysis of relevant papers.
        -   **Expert Feedback**: A critique of the idea's strengths and weaknesses.
        -   **Improved Proposal**: A revised version that incorporates the feedback.

5.  **Start a New Session**:
    -   Clicking either of the mode buttons ("I have an idea" or "Let AI take over") will reset the conversation and start a new session.

## Implementation Details

### IdeaAgent

The `IdeaAgent` is the core of the application. It has several key responsibilities:
- **Structuring**: Interprets a user's conversational input and formalizes it into a research proposal.
- **Generation**: Creates new research proposals from scratch based on a user's profile.
- **Refinement**: Updates an existing proposal based on direct user feedback, enabling conversational memory.
- **Improvement**: Integrates feedback from the other agents to create a final, improved proposal.

### ReflectionAgent

The `ReflectionAgent` acts as an expert reviewer. It assesses the structured proposal for scientific validity, methodological rigor, and feasibility, providing constructive feedback to help the student identify both strengths and areas for improvement.

### LiteratureAgent

The `LiteratureAgent` provides real-world context by searching the Semantic Scholar database for recent papers relevant to the user's idea. It analyzes the search results to assess the idea's novelty and suggests ways the student can differentiate their work from existing research.

## Contributing

Contributions to improve this application are welcome. Please feel free to submit issues or pull requests.

## License

[MIT License](LICENSE)
