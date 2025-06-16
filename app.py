import streamlit as st
import json
import asyncio
import nest_asyncio
from dataclasses import asdict, is_dataclass
from typing import Dict, Any, Optional


# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Create a new event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from idea_agent import IdeaAgent
from subfields import ASTRONOMY_SUBFIELDS
from reflection_agent import AstronomyReflectionAgent, ProposalFeedback
from literature_agent import LiteratureAgent, LiteratureFeedback

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
    
    if 'temperature' not in st.session_state:
        st.session_state.temperature = 0.5
    
    if 'skip_literature_review' not in st.session_state:
        st.session_state.skip_literature_review = False
        
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = 'iteration' # 'iteration' or 'generation'
        
    # Add state variables for the pipeline outputs
    if 'structured_idea' not in st.session_state:
        st.session_state.structured_idea = None
    if 'literature_feedback' not in st.session_state:
        st.session_state.literature_feedback = None
    if 'reflection' not in st.session_state:
        st.session_state.reflection = None
    if 'improved_idea' not in st.session_state:
        st.session_state.improved_idea = None


def reset_state(mode='iteration'):
    """Reset chat session state."""
    # Keep API key and provider
    api_key = st.session_state.api_key
    provider = st.session_state.provider
    temperature = st.session_state.temperature
    
    # Reset everything else
    st.session_state.messages = []
    st.session_state.interests = []
    st.session_state.resources = ["Public astronomical datasets"]
    st.session_state.skill_level = 'undergraduate'
    st.session_state.time_frame = '1 year'
    st.session_state.skip_literature_review = False
    st.session_state.app_mode = mode
    
    # Clear pipeline outputs
    st.session_state.structured_idea = None
    st.session_state.literature_feedback = None
    st.session_state.reflection = None
    st.session_state.improved_idea = None
    
    # Restore API key and provider
    st.session_state.api_key = api_key
    st.session_state.provider = provider
    st.session_state.temperature = temperature


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


def initialize_or_update_agents():
    """
    Initializes or updates agents if their configuration (provider, temperature) has changed.
    This ensures that changes made in the UI are applied to the agents.
    """
    provider = st.session_state.provider
    api_key = st.session_state.api_key
    temperature = st.session_state.temperature

    # List of agent configurations
    agent_configs = [
        {'name': 'idea_agent', 'class': IdeaAgent},
        {'name': 'reflection_agent', 'class': AstronomyReflectionAgent},
        {'name': 'literature_agent', 'class': LiteratureAgent, 'skip_key': 'skip_literature_review'}
    ]

    for config in agent_configs:
        agent_name = config['name']
        agent_class = config['class']
        skip_key = config.get('skip_key')

        # Skip literature agent if the checkbox is checked
        if skip_key and st.session_state.get(skip_key, False):
            st.session_state[agent_name] = None
            continue

        current_agent = st.session_state.get(agent_name)

        # Check if agent needs to be re-initialized
        if (not current_agent or
            current_agent.provider != provider or
            current_agent.temperature != temperature or
            current_agent.api_key != api_key):
            
            st.session_state[agent_name] = agent_class(
                api_key=api_key, 
                provider=provider, 
                temperature=temperature
            )


def run_refinement_pipeline(user_idea: str) -> tuple[Optional[Dict], Optional[LiteratureFeedback], Optional[ProposalFeedback], Optional[Dict]]:
    """
    Runs the full refinement pipeline and returns the structured data.
    """
    initialize_or_update_agents()

    structured_idea, literature_feedback, reflection, improved_idea = None, None, None, None

    try:
        # If there's an improved idea from a previous turn, refine it. Otherwise, start fresh.
        if st.session_state.improved_idea:
            with st.spinner("Step 1: Refining idea based on your feedback..."):
                structured_idea = st.session_state.idea_agent.refine_with_feedback(
                    previous_idea=st.session_state.improved_idea,
                    user_feedback=user_idea
                )
        else:
            with st.spinner("Step 1: Structuring your idea..."):
                structured_idea = st.session_state.idea_agent.structure_and_rephrase_idea(
                    user_idea=user_idea
                )
        
        # Store the current idea
        st.session_state.structured_idea = structured_idea
        if not structured_idea or "error" in structured_idea:
            st.error("Could not structure or refine the idea.")
            return None, None, None, None

        if not st.session_state.skip_literature_review:
            with st.spinner("Performing literature search..."):
                try:
                    literature_feedback = st.session_state.literature_agent.run_literature_search(
                        structured_idea
                    )
                    st.session_state.literature_feedback = literature_feedback
                except Exception as e:
                    st.error(f"An error occurred during the literature search: {e}")
                    return None, None, None, None

        with st.spinner("Step 3: Getting expert feedback..."):
            reflection = st.session_state.reflection_agent.provide_feedback(
                research_proposal=structured_idea
            )
            st.session_state.reflection = reflection
        
        with st.spinner("Step 4: Generating improved proposal..."):
            if reflection:
                improved_idea = st.session_state.idea_agent.improve_idea(
                    reflection_feedback=asdict(reflection),
                    literature_feedback=asdict(literature_feedback) if literature_feedback else None
                )
                st.session_state.improved_idea = improved_idea


        return structured_idea, literature_feedback, reflection, improved_idea

    except Exception as e:
        st.error(f"An error occurred during the refinement process: {e}")
        return None, None, None, None


def run_generation_pipeline() -> tuple[Optional[Dict], Optional[LiteratureFeedback], Optional[ProposalFeedback], Optional[Dict]]:
    """
    Runs the full idea generation pipeline from scratch.
    """
    initialize_or_update_agents()

    structured_idea, literature_feedback, reflection, improved_idea = None, None, None, None

    try:
        with st.spinner("Step 1: Generating a new research idea..."):
            structured_idea = st.session_state.idea_agent.generate_initial_idea(
                student_interests=st.session_state.interests,
                skill_level=st.session_state.skill_level,
                time_frame=st.session_state.time_frame,
                available_resources=st.session_state.resources,
            )
            if not structured_idea or "error" in structured_idea:
                st.error("Could not generate an idea. Try adjusting the context in the sidebar.")
                return None, None, None, None

        if not st.session_state.skip_literature_review:
            with st.spinner("Performing literature search..."):
                try:
                    literature_feedback = st.session_state.literature_agent.run_literature_search(
                        structured_idea
                    )
                    st.session_state.literature_feedback = literature_feedback
                except Exception as e:
                    st.error(f"An error occurred during the literature search: {e}")
                    return None, None, None, None

        with st.spinner("Step 3: Getting expert feedback..."):
            reflection = st.session_state.reflection_agent.provide_feedback(
                research_proposal=structured_idea
            )
            
        with st.spinner("Step 4: Generating improved proposal..."):
            if reflection:
                improved_idea = st.session_state.idea_agent.improve_idea(
                    reflection_feedback=asdict(reflection),
                    literature_feedback=asdict(literature_feedback) if literature_feedback else None
                )

        return structured_idea, literature_feedback, reflection, improved_idea

    except Exception as e:
        st.error(f"An error occurred during the generation process: {e}")
        return None, None, None, None


def display_structured_idea(idea: Dict[str, Any]):
    st.markdown("### 💡 Structured Idea")
    with st.container(border=True):
        st.markdown(f"**Title:** {idea.get('title', 'N/A')}")
        
        idea_details = idea.get('idea', {})
        st.markdown(f"**Research Question:** {idea_details.get('Research Question', 'N/A')}")
        st.markdown(f"**Proposed Solution:** {idea_details.get('Proposed Solution', 'N/A')}")

        with st.expander("View Background & Expected Outcomes"):
            st.markdown(f"**Background:** {idea_details.get('Background', 'N/A')}")
            st.markdown(f"**Expected Outcomes:** {idea_details.get('Expected Outcomes', 'N/A')}")


def display_improved_proposal(idea: Dict[str, Any]):
    if not idea or "error" in idea:
        return
        
    st.markdown("### 🚀 Improved Proposal")
    with st.container(border=True):
        st.markdown(f"**Title:** {idea.get('title', 'N/A')}")
        
        idea_details = idea.get('idea', {})
        st.markdown(f"**Research Question:** {idea_details.get('Research Question', 'N/A')}")
        st.markdown(f"**Proposed Solution:** {idea_details.get('Proposed Solution', 'N/A')}")

        with st.expander("View details"):
            st.markdown(f"**Background:** {idea_details.get('Background', 'N/A')}")
            st.markdown(f"**Expected Outcomes:** {idea_details.get('Expected Outcomes', 'N/A')}")


def display_literature_review(feedback: LiteratureFeedback):
    if not feedback:
        return
    st.markdown("### 📚 Literature Review")
    with st.expander("View Literature Analysis", expanded=True):
        score = feedback.novelty_score or 0
        st.metric("Novelty Score (out of 10)", f"{score:.1f}")
        st.markdown(f"**Assessment:** {feedback.novelty_assessment}")

        tabs = st.tabs(["Similar Papers", "Differentiation Suggestions", "Summary"])
        with tabs[0]:
            if feedback.similar_papers:
                for paper in feedback.similar_papers:
                    title = paper.get('title', 'N/A')
                    url = paper.get('url', '#')
                    year = paper.get('year', 'N/A')
                    authors_str = paper.get('authors', '')
                    
                    author_display = "Unknown Author"
                    if authors_str:
                        author_list = [author.strip() for author in authors_str.split(',')]
                        if author_list:
                            first_author = author_list[0]
                            if len(author_list) > 1:
                                author_display = f"{first_author} et al."
                            else:
                                author_display = first_author
                    
                    st.markdown(f"- **[{title}]({url})** ({author_display} {year})")
            else:
                st.info("No directly similar papers were found, which may indicate a highly novel area!")
        with tabs[1]:
            for suggestion in feedback.differentiation_suggestions:
                st.markdown(f"- {suggestion}")
        with tabs[2]:
            st.markdown(feedback.summary)


def display_expert_feedback(feedback: ProposalFeedback):
    if not feedback:
        return
    st.markdown("### 🤔 Expert Feedback")
    with st.expander("View Expert Feedback", expanded=True):
        st.markdown(f"**Summary:** {feedback.summary}")
        st.markdown("**Key Recommendations:**")
        for rec in feedback.recommendations:
            if isinstance(rec, dict):
                # Handle case where recommendation is a dict, e.g., {'recommendation': 'text'}
                st.markdown(f"- {rec.get('recommendation', json.dumps(rec))}")
            else:
                # Handle case where it's a simple string
                st.markdown(f"- {rec}")
        
        tabs = st.tabs(["Scientific Validity", "Methodology", "Feasibility & Impact"])
        with tabs[0]:
            st.markdown("**Strengths:**")
            for strength in feedback.scientific_validity.get('strengths', []):
                st.markdown(f"- {strength}")
            st.markdown("**Concerns:**")
            for concern in feedback.scientific_validity.get('concerns', []):
                st.markdown(f"- {concern}")
        with tabs[1]:
            st.markdown("**Strengths:**")
            for strength in feedback.methodology.get('strengths', []):
                st.markdown(f"- {strength}")
            st.markdown("**Concerns:**")
            for concern in feedback.methodology.get('concerns', []):
                st.markdown(f"- {concern}")
        with tabs[2]:
            st.markdown(f"**Impact:** {feedback.impact_assessment}")
            st.markdown(f"**Feasibility:** {feedback.feasibility_assessment}")


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

        def update_temperature():
            slider_value = st.session_state.temp_slider
            provider = st.session_state.provider
            if provider == 'google':
                # Scale 0.0-1.0 to 0.0-1.0 for the API
                st.session_state.temperature = slider_value
            else:
                st.session_state.temperature = slider_value

        # Find the initial slider value that corresponds to the current temperature
        current_temp = st.session_state.temperature
        provider = st.session_state.provider

        # Adjust temperature if it's out of range for the new provider
        if provider != 'google' and current_temp > 1.0:
            st.session_state.temperature = 1.0
            current_temp = 1.0
        
        initial_slider_value = current_temp

        st.slider(
            "Creativity (Temperature)",
            min_value=0.0,
            max_value=1.0,
            value=initial_slider_value,
            step=0.1,
            key='temp_slider',
            on_change=update_temperature,
            help="Controls the randomness of the output. Higher values are more creative."
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧠 I have an idea"):
                reset_state(mode='iteration')
                st.rerun()
        with col2:
            if st.button("💀 Let AI take over"):
                reset_state(mode='generation')
                st.rerun()

        if st.session_state.app_mode == 'generation':
            st.header("Research Context (For AI Generation)")
            
            st.session_state.skill_level = st.selectbox(
                "Your Skill Level",
                options=['high school', 'undergraduate', 'graduate', 'postdoc'],
                index=['high school', 'undergraduate', 'graduate', 'postdoc'].index(st.session_state.skill_level),
                key='skill_level_dropdown'
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

    if st.session_state.app_mode == 'iteration':
        # --- Main Chat Interface ---
        st.info("You are in Idea Iteration mode. Enter your thoughts below to begin the refinement process.")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # This is a simplification; for a real app, you'd want to re-render the rich display
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("enter your idea, question, or just some thoughts here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                structured_idea, literature_feedback, reflection, improved_idea = run_refinement_pipeline(prompt)
                
                if structured_idea:
                    display_structured_idea(structured_idea)
                    st.markdown("---")
                    display_literature_review(literature_feedback)
                    display_expert_feedback(reflection)
                    st.markdown("---")
                    display_improved_proposal(improved_idea)
                    
                    # Store a clean confirmation message in history instead of raw data
                    confirmation_message = "Here's the analysis of your idea. You can provide feedback in the chat to refine it further."
                    st.session_state.messages.append({"role": "assistant", "content": confirmation_message})
                else:
                    error_message = "I'm sorry, I encountered an error and couldn't process your request. Please try rephrasing your idea or check the application logs."
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
    
    elif st.session_state.app_mode == 'generation':
        st.info("You are in **Idea Generation** mode. Use the sidebar to set your research context and click the button below.")
        
        if st.button("✨ Generate a New Research Idea", use_container_width=True):
            with st.chat_message("assistant"):
                structured_idea, literature_feedback, reflection, improved_idea = run_generation_pipeline()
                
                if structured_idea:
                    display_structured_idea(structured_idea)
                    st.markdown("---")
                    display_literature_review(literature_feedback)
                    display_expert_feedback(reflection)
                    st.markdown("---")
                    display_improved_proposal(improved_idea)
                    
                    # Store a clean confirmation message in history instead of raw data
                    history_content = "Here is the generated idea and analysis. You can now switch to 'I have an idea' mode to start refining it."
                    st.session_state.messages.append({"role": "assistant", "content": history_content})
                else:
                    error_message = "I'm sorry, I encountered an error and couldn't generate an idea. Please try adjusting the context in the sidebar or try again."
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})


if __name__ == "__main__":
    main()