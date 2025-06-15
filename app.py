import streamlit as st
import json
import asyncio
import nest_asyncio
from dataclasses import asdict


# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Create a new event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from idea_agent import IdeaAgent
from subfields import ASTRONOMY_SUBFIELDS
from reflection_agent import AstronomyReflectionAgent
from literature_agent import LiteratureAgent  # Import the new LiteratureAgent

# Import Google GenAI for backward compatibility
try:
    from google import genai
except ImportError:
    genai = None


def initialize_session_state():
    """Initialize session state variables for chat."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'interests' not in st.session_state:
        st.session_state.interests = []
    
    if 'resources' not in st.session_state:
        st.session_state.resources = ["Public astronomical datasets"]
    
    if 'skill_level' not in st.session_state:
        st.session_state.skill_level = 'undergraduate'
    
    if 'time_frame' not in st.session_state:
        st.session_state.time_frame = '1 year'
    
    if 'idea_agent' not in st.session_state:
        st.session_state.idea_agent = None
    
    if 'reflection_agent' not in st.session_state:
        st.session_state.reflection_agent = None
    
    if 'literature_agent' not in st.session_state:
        st.session_state.literature_agent = None
    
    if 'provider' not in st.session_state:
        st.session_state.provider = 'google'
    
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ''
    
    if 'skip_literature_review' not in st.session_state:
        st.session_state.skip_literature_review = False


def reset_state():
    """Reset chat session state."""
    # Keep API key and provider
    api_key = st.session_state.api_key
    provider = st.session_state.provider
    
    # Reset everything else
    st.session_state.messages = []
    st.session_state.interests = []
    st.session_state.resources = ["Public astronomical datasets"]
    st.session_state.skill_level = 'undergraduate'
    st.session_state.time_frame = '1 year'
    st.session_state.skip_literature_review = False
    
    # Restore API key and provider
    st.session_state.api_key = api_key
    st.session_state.provider = provider


def update_interests():
    """Update selected interests from checkboxes"""
    st.session_state.interests = []
    for subfield in ASTRONOMY_SUBFIELDS:
        key = f"interest_{subfield.name}"
        if key in st.session_state and st.session_state[key]:
            st.session_state.interests.append(subfield.name)


def update_resources():
    """Update selected resources from checkboxes"""
    selected = []
    resource_options = [
        "Public astronomical datasets", "Telescope access (ground-based)",
        "Telescope access (space-based)", "High-performance computing",
        "Laboratory/experimental facilities", "Existing survey data", "Other"
    ]
    for resource in resource_options:
        key = f"resource_{resource}"
        if key in st.session_state and st.session_state[key]:
            selected.append(resource)
    
    if not selected:
        selected = ["Public astronomical datasets"]
    
    st.session_state.resources = selected


def add_literature_options_to_sidebar():
    """Add literature search options to the sidebar"""
    st.sidebar.header("Literature Review Options")
    
    # Option to skip literature review
    st.sidebar.checkbox(
        "Skip arXiv literature review",
        value=st.session_state.skip_literature_review,
        help="Turn this on to skip the arXiv literature review step and get feedback faster.",
        key="skip_lit_review_checkbox",
        on_change=toggle_literature_review
    )
    
    # Note about arXiv integration
    if not st.session_state.skip_literature_review:
        st.sidebar.info(
            "The literature review searches arXiv for papers published in the last 2 years "
            "that are relevant to your research idea."
        )


def toggle_literature_review():
    """Toggle the literature review option"""
    st.session_state.skip_literature_review = st.session_state.skip_lit_review_checkbox


def run_refinement_pipeline(user_idea: str):
    """
    Runs the full refinement pipeline: rephrase, literature review, and reflection.
    """
    # Ensure agents are initialized
    if not st.session_state.idea_agent:
        st.session_state.idea_agent = IdeaAgent(st.session_state.api_key, provider=st.session_state.provider)
    if not st.session_state.reflection_agent:
        st.session_state.reflection_agent = AstronomyReflectionAgent(st.session_state.api_key, provider=st.session_state.provider)
    if not st.session_state.literature_agent and not st.session_state.skip_literature_review:
        st.session_state.literature_agent = LiteratureAgent(st.session_state.api_key, provider=st.session_state.provider)

    # Prepare context from sidebar
    additional_context = (
        f"The user's skill level is '{st.session_state.skill_level}', "
        f"they have a time frame of '{st.session_state.time_frame}', "
        f"and access to the following resources: {', '.join(st.session_state.resources)}."
    )

    full_response = ""
    structured_idea_response = ""
    literature_feedback_response = ""
    reflection_response = ""

    try:
        # Step 1: Rephrase and structure the idea
        with st.spinner("Step 1: Structuring your idea..."):
            # This method will need to be created in IdeaAgent
            structured_idea = st.session_state.idea_agent.structure_and_rephrase_idea(
                user_idea=user_idea,
                student_interests=st.session_state.interests,
                skill_level=st.session_state.skill_level,
                time_frame=st.session_state.time_frame,
                available_resources=st.session_state.resources,
                additional_context=additional_context
            )
            if structured_idea:
                structured_idea_response = "### 💡 Structured Idea\n" + json.dumps(structured_idea, indent=2)
                full_response += structured_idea_response + "\n\n---\n\n"
            else:
                st.error("Could not structure the idea.")
                return "I had trouble structuring your idea. Could you try rephrasing it?"

        # Step 2: Literature Review
        if not st.session_state.skip_literature_review:
            with st.spinner("Step 2: Reviewing existing literature on arXiv..."):
                literature_feedback = st.session_state.literature_agent.run_arxiv_search(
                    research_idea=structured_idea
                )
                if literature_feedback:
                    literature_feedback_response = "### 📚 Literature Review\n" + json.dumps(asdict(literature_feedback), indent=2)
                    full_response += literature_feedback_response + "\n\n---\n\n"

        # Step 3: Expert Reflection
        with st.spinner("Step 3: Getting expert feedback..."):
            reflection = st.session_state.reflection_agent.provide_feedback(
                research_proposal=structured_idea
            )
            if reflection:
                reflection_response = "### 🤔 Expert Feedback\n" + json.dumps(asdict(reflection), indent=2)
                full_response += reflection_response

        return full_response

    except Exception as e:
        st.error(f"An error occurred during the refinement process: {e}")
        return f"Sorry, an error occurred: {e}"


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="AI Astronomy Research Assistant",
        page_icon="🔭",
        layout="wide",
    )
    
    initialize_session_state()

    st.title("AI Astronomy Research Assistant 🔭")
    st.caption("Your partner in refining research ideas")

    # --- Sidebar Setup ---
    with st.sidebar:
        st.header("Configuration")
        
        st.session_state.provider = st.radio(
            "Select LLM Provider",
            ('google', 'openai', 'anthropic'),
            index=0,
            key='provider_radio'
        )

        st.session_state.api_key = st.text_input(
            "Enter API Key",
            type="password",
            key="api_key_input",
            value=st.session_state.api_key
        )

        if st.button("Start New Chat"):
            reset_state()
            st.rerun()

        st.header("Research Context (Optional)")
        
        st.session_state.skill_level = st.select_slider(
            "Your Skill Level",
            options=['high school', 'undergraduate', 'graduate', 'postdoc'],
            value=st.session_state.skill_level,
            key='skill_level_slider'
        )
        
        st.session_state.time_frame = st.selectbox(
            "Time Frame",
            ['3 months', '6 months', '1 year', '2+ years'],
            index=2,
            key='time_frame_select'
        )

        st.subheader("Interests")
        for subfield in ASTRONOMY_SUBFIELDS:
            st.checkbox(subfield.name, key=f"interest_{subfield.name}", on_change=update_interests)
            
        st.subheader("Available Resources")
        resource_options = [
            "Public astronomical datasets", "Telescope access (ground-based)",
            "Telescope access (space-based)", "High-performance computing",
            "Laboratory/experimental facilities", "Existing survey data", "Other"
        ]
        for resource in resource_options:
            st.checkbox(resource, key=f"resource_{resource}", on_change=update_resources, value=(resource in st.session_state.resources))

        add_literature_options_to_sidebar()

    # --- Main Chat Interface ---
    if not st.session_state.api_key:
        st.info("Please enter your API key in the sidebar to begin.")
        return

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Enter your research idea or question here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Run the pipeline and display the response
            response = run_refinement_pipeline(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()