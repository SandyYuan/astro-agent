# AI Astronomy Research Assistant

An AI-powered application that helps astronomy students refine their research ideas through iterative feedback and analysis.

## Overview

This application acts as an AI-powered partner for astronomy students, transforming rough or vague research concepts into structured, scientifically-grounded proposals. Instead of generating ideas from scratch, the assistant engages in a conversation with the user to collaboratively refine their initial thoughts.

The user starts by providing an idea in a chat interface. The system then uses a pipeline of specialized AI agents to analyze the concept, review relevant literature, provide expert feedback, and present a more formalized version back to the user. This iterative process allows students to strengthen their ideas in a dynamic, conversational way.

> **Recommendation**: We recommend using a powerful, up-to-date model like Google Gemini 1.5 Pro or Claude 3.5 Sonnet as the LLM backbone for this application.

## Key Features

- **Iterative Idea Refinement**: Engage in a conversation with an AI assistant to turn your rough ideas into well-defined research proposals.
- **Idea Structuring**: The AI formalizes your concept, identifying a clear research question, methodology, and expected outcomes.
- **Scientific Evaluation**: An expert AI agent reviews your idea, providing detailed feedback on its scientific validity, methodological soundness, and feasibility.
- **Automated Literature Review**: The system searches recent arXiv papers to assess the novelty of your idea and provides context from existing research.
- **Conversational Interface**: A simple chat-based UI allows for a natural, continuous refinement loop.
- **Context-Aware Feedback**: Optionally provide your skill level, interests, and available resources to receive more tailored feedback.

## System Architecture

The application consists of three primary AI agents working in a pipeline:

1.  **Idea Agent**: Takes the user's raw input and structures it into a formal research concept.
2.  **Literature Agent**: Conducts a literature search on arXiv to analyze the novelty of the structured idea.
3.  **Reflection Agent**: Evaluates the structured idea with the critical eye of an experienced astronomy professor, providing expert feedback.

## Setup Instructions

### Prerequisites

- Python 3.8+
- An API key for a supported LLM provider (Google Gemini, Anthropic Claude, or Azure OpenAI).

### Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/your-username/astronomy-idea-refiner.git
    cd astronomy-idea-refiner
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

2.  **Start the Conversation**:
    -   Once the API key is entered, the main chat interface will appear.
    -   Type your initial research idea into the chat box at the bottom and press enter. It can be a simple question, a statement, or a rough concept.

3.  **Receive AI Feedback**:
    -   The assistant will process your idea through its three-agent pipeline.
    -   It will respond with a detailed message containing:
        -   **Structured Idea**: Your idea, rephrased into a formal proposal.
        -   **Literature Review**: An analysis of relevant papers from arXiv.
        -   **Expert Feedback**: A critique of the idea's strengths and weaknesses.

4.  **Iterate and Refine**:
    -   Continue the conversation. You can ask for clarification, suggest modifications, or provide more details to further refine the idea.
    -   Use the "Research Context" options in the sidebar at any time to help the AI provide more tailored feedback.

5.  **Start a New Chat**:
    -   Click the "Start New Chat" button in the sidebar at any time to clear the history and begin a new refinement session.

## Implementation Details

### IdeaAgent

The `IdeaAgent`'s primary role is to interpret the user's conversational input and formalize it. It identifies the core research question, proposes a plausible methodology, and structures the user's concept into a coherent proposal that can be evaluated by the other agents.

### ReflectionAgent

The `ReflectionAgent` acts as an expert reviewer. It assesses the structured proposal for scientific validity, methodological rigor, and feasibility, providing constructive feedback to help the student identify both strengths and areas for improvement.

### LiteratureAgent

The `LiteratureAgent` provides real-world context by searching arXiv for recent papers relevant to the user's idea. It analyzes the search results to assess the idea's novelty and suggests ways the student can differentiate their work from existing research.

## Supported LLM Providers

The application supports multiple LLM providers, including:

-   **Google Gemini** (e.g., `gemini-1.5-pro-latest`)
-   **Anthropic Claude** (e.g., `claude-3.5-sonnet-20240620`)
-   **Azure OpenAI Service**

## Contributing

Contributions to improve this application are welcome. Please feel free to submit issues or pull requests.

## License

[MIT License](LICENSE)
