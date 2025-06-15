# Plan: Refactoring to an AI-Powered Idea Iterator

This document outlines the plan to shift the project's philosophy from an "AI Idea Generator" to an "AI Idea Iterator." The core change is moving from a system that creates ideas for the user to a system that collaborates with the user to refine and iterate on *their* ideas.

## Core Philosophy Change: Generator vs. Iterator

*   **Old Philosophy:** The user is a passive recipient. They provide high-level interests, and the AI does the creative work of generating and evaluating a research idea from scratch.
*   **New Philosophy:** The user is the driver of creativity. They bring an initial concept (which can be vague or detailed), and the AI acts as a sophisticated partner to help them rephrase, challenge, and strengthen it with scientific context and literature review.

The new user flow will be:
1.  User provides an initial research idea in a chat interface.
2.  The AI pipeline activates:
    *   **Rephrase & Structure:** The `IdeaAgent` reinterprets the user's input into a structured, clearer research concept.
    *   **Literature Review:** The `LiteratureAgent` analyzes the concept against recent research to identify novelty and provide context.
    *   **Expert Feedback:** The `ReflectionAgent` critiques the idea's potential and methodology.
3.  The AI presents a refined version of the idea, along with the literature and expert analysis, back to the user in the chat.
4.  The user can then provide more input, ask questions, or suggest modifications, continuing the iterative loop.

---

## Phase 1: UI and Core Logic Transformation (`app.py`)

This phase focuses on restructuring the Streamlit application to support a chat-based workflow.

### 1.1. Rework the Main UI
**File to Edit:** `app.py`

*   **Reasoning:** The current UI is a multi-page, form-based wizard. To support an iterative conversation, we need to replace this with a persistent chat interface.
*   **Changes:**
    *   Remove the `st.session_state.app_stage` logic that controls the multi-step form.
    *   The main screen will be simplified. After the user provides their API key in the sidebar, the central UI will primarily feature a chat history display and a user input box (`st.chat_input`).
    *   The existing multi-choice options (Interests, Skills, etc.) will be kept in the sidebar. They will no longer be required inputs but will serve as optional context that can be passed to the agents with each user message.

### 1.2. Implement Chat State Management
**File to Edit:** `app.py`

*   **Reasoning:** We need to store the history of the conversation between the user and the AI. Streamlit's session state is perfect for this.
*   **Changes:**
    *   Initialize `st.session_state.messages` as a list to store the chat history. Each item in the list will have a `role` ("user" or "assistant") and `content`.
    *   On startup, render the existing messages from the session state.
    *   When the user submits a message via `st.chat_input`, append it to `st.session_state.messages` and re-render the UI.

### 1.3. Re-Orchestrate the Agent Pipeline
**File to Edit:** `app.py`

*   **Reasoning:** The `run_full_pipeline` function currently runs a linear, one-shot process. We need to adapt this to run inside the chat loop every time the user sends a message.
*   **Changes:**
    *   Create a new function, let's call it `run_refinement_pipeline(user_idea)`, that takes the user's input as an argument.
    *   This function will call the agents in the new sequence: `IdeaAgent` (to rephrase), `LiteratureAgent`, and `ReflectionAgent`.
    *   The outputs from all agents will be compiled into a single, comprehensive markdown response.
    *   This response will be appended to `st.session_state.messages` with the "assistant" role and displayed in the chat.

---

## Phase 2: Agent Prompt and Logic Modification

This phase adapts the existing agents to their new roles in the refinement process.

### 2.1. Refocus the `IdeaAgent`
**File to Edit:** `idea_agent.py`

*   **Reasoning:** The `IdeaAgent` is no longer generating ideas from scratch. Its new purpose is to take a user's potentially rough idea and structure it as a coherent, testable research concept.
*   **Changes:**
    *   Rename the primary method from `generate_initial_idea` to something more appropriate, like `structure_and_rephrase_idea`.
    *   **Crucially, rewrite the underlying prompt.** The new prompt will instruct the AI to act as a research assistant that does the following:
        *   "Given the following user's research idea, rephrase and structure it into a formal research proposal concept."
        *   "Identify a clear research question, a potential methodology, and expected outcomes based on the user's input."
        *   "Do not invent a new idea; your role is to clarify and formalize the user's existing one."

### 2.2. Adapt `LiteratureAgent` and `ReflectionAgent`
**Files to Edit:** `literature_agent.py`, `reflection_agent.py`

*   **Reasoning:** These agents are already well-suited for their roles, but their prompts need to be slightly tweaked to reflect that they are analyzing a user-provided idea, not a purely AI-generated one.
*   **Changes:**
    *   **`LiteratureAgent`:** The prompt should be adjusted to emphasize finding papers that are "relevant to the following research concept provided by a student" and to "assess its novelty and suggest how it could be differentiated."
    *   **`ReflectionAgent`:** The prompt should be updated to frame the task as "evaluating the following student-proposed idea for its scientific validity, methodology, and feasibility."

---

## Phase 3: Model and Configuration Updates

This phase ensures the application is using the latest, most capable models as requested.

### 3.1. Update Model Names
**File to Edit:** `llm_client.py` (and potentially `config_o1.yml`)

*   **Reasoning:** To leverage the best capabilities for scientific reasoning, we will update the models to the newer versions you specified. I will use the latest available production-ready versions that match your request.
*   **Changes:**
    *   In `llm_client.py`, locate the model name mappings.
    *   Update the Google Gemini model to `gemini-1.5-pro-latest`.
    *   Update the Anthropic Claude model to `claude-3.5-sonnet-20240620`.
    *   The OpenAI models will be left as they are, per your instruction.
    *   I will verify if these changes are also needed in `config_o1.yml` and apply them there if necessary.

---

## Phase 4: Final Polish

### 4.1. Update Documentation
**File to Edit:** `README.md`

*   **Reasoning:** The project's documentation must reflect its new core philosophy and functionality.
*   **Changes:**
    *   Rewrite the "Overview" and "Key Features" sections to describe the new "Idea Iterator" workflow.
    *   Update the "Using the Application" section to explain the new chat-based interface.
    *   Change the title from "Astronomy Research Idea Generator" to something more fitting, like "AI Astronomy Research Assistant" or "Astronomy Idea Refiner."

This plan provides a clear path to refactoring the application while maximizing the reuse of existing components. It shifts the focus from AI-as-a-creator to AI-as-a-collaborator, resulting in a more powerful and interactive tool for students. 