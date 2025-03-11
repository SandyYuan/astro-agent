import streamlit as st
import json
import asyncio
import nest_asyncio
import os
import time
from typing import Dict, Any, List, Optional


# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Create a new event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from idea_agent import IdeaAgent, generate_research_idea, generate_multiple_ideas
from subfields import ASTRONOMY_SUBFIELDS, AstronomySubfield
from reflection_agent import AstronomyReflectionAgent, ProposalFeedback, generate_improved_idea
from literature_agent import LiteratureAgent  # Import the new LiteratureAgent

# Import Google GenAI for backward compatibility
try:
    from google import genai
except ImportError:
    genai = None

# Import the LLMClient wrapper
from llm_client import LLMClient

# Create the standalone functions if needed
def generate_research_idea(api_key, **kwargs):
    provider = kwargs.pop('provider', 'azure')  # Get provider with default to Azure
    # Validate that provider is one of the supported options
    if provider not in ["azure", "google", "claude"]:
        raise ValueError(f"Unsupported provider: {provider}")
    agent = IdeaAgent(api_key, provider=provider)
    return agent.generate_initial_idea(**kwargs)

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'app_stage' not in st.session_state:
        st.session_state.app_stage = 'start'
    
    if 'interests' not in st.session_state:
        st.session_state.interests = []
    
    if 'resources' not in st.session_state:
        st.session_state.resources = []
    
    if 'skill_level' not in st.session_state:
        st.session_state.skill_level = 'beginner'
    
    if 'time_frame' not in st.session_state:
        st.session_state.time_frame = '1 year'
    
    if 'additional_context' not in st.session_state:
        st.session_state.additional_context = ''
    
    if 'current_idea' not in st.session_state:
        st.session_state.current_idea = None
    
    if 'improved_idea' not in st.session_state:
        st.session_state.improved_idea = None
    
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
    
    if 'literature_feedback' not in st.session_state:
        st.session_state.literature_feedback = None
    
    if 'show_process' not in st.session_state:
        st.session_state.show_process = False
    
    if 'trigger_generate' not in st.session_state:
        st.session_state.trigger_generate = False
    
    if 'idea_agent' not in st.session_state:
        st.session_state.idea_agent = None
    
    if 'reflection_agent' not in st.session_state:
        st.session_state.reflection_agent = None
    
    if 'literature_agent' not in st.session_state:
        st.session_state.literature_agent = None
    
    if 'provider' not in st.session_state:
        st.session_state.provider = 'azure'
    
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ''
    
    if 'skip_literature_review' not in st.session_state:
        st.session_state.skip_literature_review = False
        
    # New state variables for user feedback
    if 'user_feedback' not in st.session_state:
        st.session_state.user_feedback = ''
        
    if 'has_user_feedback' not in st.session_state:
        st.session_state.has_user_feedback = False
        
    if 'trigger_user_improvement' not in st.session_state:
        st.session_state.trigger_user_improvement = False
        
    if 'user_improved_idea' not in st.session_state:
        st.session_state.user_improved_idea = None

def reset_state():
    """Reset all session state variables to their initial values"""
    # Keep API key and provider
    api_key = st.session_state.api_key
    provider = st.session_state.provider
    
    # Reset everything else
    st.session_state.app_stage = 'start'
    st.session_state.interests = []
    st.session_state.resources = []
    st.session_state.skill_level = 'beginner'
    st.session_state.time_frame = '1 year'
    st.session_state.additional_context = ''
    st.session_state.current_idea = None
    st.session_state.improved_idea = None
    st.session_state.feedback = None
    st.session_state.literature_feedback = None
    st.session_state.show_process = False
    st.session_state.trigger_generate = False
    st.session_state.skip_literature_review = False
    
    # Reset user feedback variables
    st.session_state.user_feedback = ''
    st.session_state.has_user_feedback = False
    st.session_state.trigger_user_improvement = False
    st.session_state.user_improved_idea = None
    
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
    for resource in st.session_state.resource_options:
        key = f"resource_{resource}"
        if key in st.session_state and st.session_state[key]:
            selected.append(resource)
    
    # Default to public datasets if nothing selected
    if not selected:
        selected = ["Public astronomical datasets"]
    
    st.session_state.resources = selected

def set_generate_trigger():
    st.session_state.trigger_generate = True

def add_literature_options_to_sidebar():
    """Add literature search options to the sidebar"""
    st.sidebar.header("Literature Review Options")
    
    # Option to skip literature review
    st.sidebar.checkbox(
        "Skip arXiv literature review",
        value=st.session_state.skip_literature_review,
        help="Turn this on to skip the arXiv literature review step and generate ideas faster.",
        key="skip_lit_review_checkbox",
        on_change=toggle_literature_review
    )
    
    # Note about arXiv integration
    if not st.session_state.skip_literature_review:
        st.sidebar.info(
            "The literature review searches arXiv for papers published in the last 2 years "
            "that are relevant to your research idea."
        )


def update_search_api():
    """Update the search API based on radio button selection"""
    selection = st.session_state.search_api_selection
    st.session_state.search_api = selection.lower().replace(" ", "")

def toggle_process_view():
    st.session_state.show_process = not st.session_state.show_process

def toggle_literature_review():
    """Toggle the literature review option"""
    st.session_state.skip_literature_review = not st.session_state.skip_literature_review

def run_full_pipeline():
    """Run the entire idea generation, literature review, feedback, and improvement pipeline"""
    # First check if we have valid agents
    if not st.session_state.api_key:
        st.error("Please enter a valid API key in the sidebar.")
        return False
        
    # Ensure agents are initialized
    if not st.session_state.idea_agent:
        try:
            st.session_state.idea_agent = IdeaAgent(st.session_state.api_key, provider=st.session_state.provider)
        except Exception as e:
            st.error(f"Error initializing idea agent: {str(e)}")
            return False
            
    if not st.session_state.reflection_agent:
        try:
            st.session_state.reflection_agent = AstronomyReflectionAgent(st.session_state.api_key, provider=st.session_state.provider)
        except Exception as e:
            st.error(f"Error initializing reflection agent: {str(e)}")
            return False
            
    if not st.session_state.literature_agent and not st.session_state.skip_literature_review:
        try:
            st.session_state.literature_agent = LiteratureAgent(st.session_state.api_key, provider=st.session_state.provider)
        except Exception as e:
            st.error(f"Error initializing literature agent: {str(e)}")
            return False

    try:
        # Step 1: Generate initial idea with a timeout
        with st.spinner("Generating initial research idea..."):
            try:
                # Use threading-based timeout approach for Streamlit
                import threading
                import concurrent.futures
                
                # Function that will be executed with a timeout
                def generate_with_timeout(timeout_seconds=45):
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                st.session_state.idea_agent.generate_initial_idea,
                                student_interests=st.session_state.interests,
                                skill_level=st.session_state.skill_level,
                                time_frame=st.session_state.time_frame,
                                available_resources=st.session_state.resources,
                                additional_context=st.session_state.additional_context
                            )
                            # Wait for completion or timeout
                            return future.result(timeout=timeout_seconds)
                    except concurrent.futures.TimeoutError:
                        raise TimeoutError("Generation took too long. Try again or check your API key.")
                
                # Generate the idea with timeout
                initial_idea = generate_with_timeout(45)  # 45 second timeout
                
                if not initial_idea:
                    st.error("Failed to generate initial research idea.")
                    return False
                    
                st.session_state.current_idea = initial_idea
                st.session_state.app_stage = 'idea_generated'
            
            except TimeoutError as e:
                st.error(f"Timeout error: {str(e)}")
                return False
            except Exception as e:
                st.error(f"Error generating initial idea: {str(e)}")
                return False
        
        # Step 2: Literature Review (Now with real papers only)
        literature_feedback = None
        if not st.session_state.skip_literature_review and st.session_state.literature_agent:
            with st.spinner("Searching arXiv for relevant papers..."):
                try:
                    # Use threading-based timeout for literature search
                    def literature_review_with_timeout(timeout_seconds=60):
                        try:
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(
                                    st.session_state.literature_agent.review_literature,
                                    initial_idea,
                                    max_papers=5
                                )
                                # Wait for completion or timeout
                                return future.result(timeout=timeout_seconds)
                        except concurrent.futures.TimeoutError:
                            raise TimeoutError("Literature search took too long.")
                    
                    # Call with timeout
                    literature_feedback_obj = literature_review_with_timeout(60)  # 60 second timeout
                    
                    literature_feedback = st.session_state.literature_agent.format_feedback_for_idea_agent(literature_feedback_obj)
                    st.session_state.literature_feedback = literature_feedback_obj
                    st.session_state.app_stage = 'literature_reviewed'
                except TimeoutError:
                    st.warning("Literature search took too long and was skipped. Proceeding without literature review.")
                    literature_feedback = None
                except Exception as e:
                    st.warning(f"Literature review encountered an issue: {str(e)}")
                    st.info("Proceeding without literature review.")
                    literature_feedback = None
        
        # Step 3: Get feedback, now including literature insights if available
        with st.spinner("Getting expert feedback on the idea..."):
            try:
                # Use threading-based timeout for feedback generation
                def feedback_with_timeout(timeout_seconds=45):
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                st.session_state.reflection_agent.evaluate_proposal,
                                initial_idea, 
                                literature_feedback
                            )
                            # Wait for completion or timeout
                            return future.result(timeout=timeout_seconds)
                    except concurrent.futures.TimeoutError:
                        raise TimeoutError("Feedback generation took too long.")
                
                # Call with timeout
                feedback = feedback_with_timeout(45)  # 45 second timeout
                
                if not feedback:
                    st.error("Failed to get expert feedback.")
                    return False
                    
                st.session_state.feedback = feedback
                st.session_state.app_stage = 'feedback_received'
            except TimeoutError:
                st.error("Feedback generation took too long. Using a simplified evaluation.")
                # Create basic feedback
                from reflection_agent import ProposalFeedback
                basic_feedback = ProposalFeedback(
                    scientific_validity={"strengths": [], "concerns": []},
                    methodology={"strengths": [], "concerns": []},
                    novelty_assessment="No detailed novelty assessment available.",
                    impact_assessment="No detailed impact assessment available.",
                    feasibility_assessment="No detailed feasibility assessment available.",
                    recommendations=["Consider refining the methodology", "Add more detail to expected outcomes"],
                    summary="The proposal requires further development."
                )
                st.session_state.feedback = basic_feedback
                st.session_state.app_stage = 'feedback_received'
            except Exception as e:
                st.error(f"Error getting expert feedback: {str(e)}")
                return False
        
        # Step 4: Improve idea
        with st.spinner("Refining research idea based on feedback..."):
            try:
                # Use threading-based timeout for idea improvement
                def improve_with_timeout(timeout_seconds=45):
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            # Convert feedback to dictionary for idea agent
                            feedback_dict = st.session_state.reflection_agent.format_feedback_for_idea_agent(st.session_state.feedback)
                            future = executor.submit(
                                st.session_state.idea_agent.improve_idea,
                                feedback_dict
                            )
                            # Wait for completion or timeout
                            return future.result(timeout=timeout_seconds)
                    except concurrent.futures.TimeoutError:
                        raise TimeoutError("Idea improvement took too long.")
                
                # Call with timeout
                improved_idea = improve_with_timeout(45)  # 45 second timeout
                
                if not improved_idea:
                    st.error("Failed to refine the research idea.")
                    return False
                    
                st.session_state.improved_idea = improved_idea
                
                # Update app stage to completed
                st.session_state.app_stage = 'completed'
                return True
            except TimeoutError:
                st.error("Idea improvement took too long. Using the initial idea as the final result.")
                st.session_state.improved_idea = st.session_state.current_idea
                st.session_state.app_stage = 'completed'
                return True
            except Exception as e:
                st.error(f"Error improving the idea: {str(e)}")
                return False
        
    except Exception as e:
        st.error(f"Error in research idea pipeline: {str(e)}")
        # Show detailed error in expandable section
        with st.expander("Error details"):
            st.exception(e)
        
        # Update app stage based on what we completed
        if hasattr(st.session_state, 'current_idea') and st.session_state.current_idea:
            if hasattr(st.session_state, 'feedback') and st.session_state.feedback:
                st.session_state.app_stage = 'feedback_received'
            elif hasattr(st.session_state, 'literature_feedback') and st.session_state.literature_feedback:
                st.session_state.app_stage = 'literature_reviewed'
            else:
                st.session_state.app_stage = 'idea_generated'
                
        return False
    
def submit_user_feedback():
    """Handle user feedback submission and trigger idea improvement"""
    # Store the user feedback in session state
    if st.session_state.user_feedback and st.session_state.user_feedback.strip():
        # Set a flag to indicate user feedback is available
        st.session_state.has_user_feedback = True
        # Set a flag to trigger the improvement process
        st.session_state.trigger_user_improvement = True

def process_user_feedback():
    """Process user feedback and generate an improved idea with expert feedback loop"""
    if not st.session_state.has_user_feedback or not st.session_state.user_feedback:
        return
    
    # Reset the trigger
    st.session_state.trigger_user_improvement = False
    
    try:
        # Step 1: Initial improvement based on user feedback
        with st.spinner("Processing your feedback..."):
            import threading
            import concurrent.futures
            
            def improve_with_user_feedback_timeout(timeout_seconds=45):
                try:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            st.session_state.idea_agent.improve_idea_with_user_feedback,
                            st.session_state.user_feedback
                        )
                        # Wait for completion or timeout
                        return future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError("Idea improvement took too long.")
            
            # Call with timeout
            initial_user_improved_idea = improve_with_user_feedback_timeout(45)  # 45 second timeout
            
            if not initial_user_improved_idea:
                st.error("Failed to improve idea based on your feedback.")
                return
            
            # Store the initial user-improved idea
            st.session_state.current_idea = initial_user_improved_idea
        
        # Step 2: Get expert feedback on the user-improved idea
        with st.spinner("Getting expert feedback on your improved idea..."):
            # Reuse the existing feedback_with_timeout function from run_full_pipeline
            feedback = feedback_with_timeout(45)  # 45 second timeout
            
            if not feedback:
                st.error("Failed to get expert feedback on your improved idea.")
                return
                
            # Store the feedback
            st.session_state.feedback = feedback
        
        # Step 3: Final improvement based on expert feedback
        with st.spinner("Refining your idea based on expert feedback..."):
            # Reuse the existing improve_with_timeout function from run_full_pipeline
            # Convert feedback to dictionary for idea agent
            feedback_dict = st.session_state.reflection_agent.format_feedback_for_idea_agent(st.session_state.feedback)
            
            # Call with timeout
            final_improved_idea = improve_with_timeout(45)  # 45 second timeout
            
            if not final_improved_idea:
                st.error("Failed to generate final improved idea.")
                return
            
            # Store the final improved idea
            st.session_state.user_improved_idea = final_improved_idea
            st.session_state.improved_idea = final_improved_idea
            
            # Update app stage
            st.session_state.app_stage = 'completed'
            
            # Show success message
            st.success("Research idea successfully refined based on your feedback and expert evaluation!")
            
    except TimeoutError as e:
        st.error(f"Process timed out: {str(e)}")
    except Exception as e:
        st.error(f"Error improving idea: {str(e)}")
        # Show detailed error in expandable section
        with st.expander("Error details"):
            st.write(str(e))

def send_feedback():
    """Prepare the full process JSON and show an email form to send feedback with attachment"""
    # Only proceed if we have a completed idea process
    if not hasattr(st.session_state, 'improved_idea') or not st.session_state.improved_idea:
        st.sidebar.error("Generate a research idea first to include with your feedback.")
        return

    # Create the comprehensive export data
    export_data = {
        "final_idea": st.session_state.improved_idea,
        "development_process": {
            "initial_idea": st.session_state.current_idea,
            "has_user_feedback": st.session_state.has_user_feedback if hasattr(st.session_state, 'has_user_feedback') else False,
            "user_feedback": st.session_state.user_feedback if hasattr(st.session_state, 'user_feedback') else None,
        }
    }
    
    # Add expert feedback if available
    if hasattr(st.session_state, 'feedback') and st.session_state.feedback:
        # Convert feedback object to dict for JSON serialization
        if hasattr(st.session_state.feedback, '__dict__'):
            feedback_dict = st.session_state.feedback.__dict__
        else:
            feedback_dict = {}
            for attr in dir(st.session_state.feedback):
                if not attr.startswith('_') and not callable(getattr(st.session_state.feedback, attr)):
                    feedback_dict[attr] = getattr(st.session_state.feedback, attr)
        
        export_data["development_process"]["expert_feedback"] = feedback_dict
    
    # Add literature feedback if available
    if hasattr(st.session_state, 'literature_feedback') and st.session_state.literature_feedback:
        # Convert feedback object to dict for JSON serialization
        if hasattr(st.session_state.literature_feedback, '__dict__'):
            literature_dict = st.session_state.literature_feedback.__dict__
        else:
            literature_dict = {}
            for attr in dir(st.session_state.literature_feedback):
                if not attr.startswith('_') and not callable(getattr(st.session_state.literature_feedback, attr)):
                    literature_dict[attr] = getattr(st.session_state.literature_feedback, attr)
        
        export_data["development_process"]["literature_feedback"] = literature_dict
    
    # Store JSON data
    json_data = json.dumps(export_data, indent=2, default=str)
    version_tag = f"v{st.session_state.improved_idea.get('version', '1')}" if 'version' in st.session_state.improved_idea else "research_idea"
    filename = f"astronomy_full_process_{version_tag}.json"
    
    # Create a mailto link with instructions to attach the file
    st.sidebar.download_button(
        label="Step 1: Download log files",
        data=json_data,
        file_name=filename,
        mime="application/json",
        key="download_for_email"
    )
    
    # Create a direct mailto link with pre-filled subject
    idea_title = st.session_state.improved_idea.get("title", "Research Idea")
    email_subject = f"Astro-agent feedback: {idea_title}"
    email_body = "Please attach the downloaded JSON file to this email. Your feedback:"
    mailto_url = f"mailto:sihany@stanford.edu?subject={email_subject}&body={email_body}"
    
    # Use a clean link approach that will inherit Streamlit's styling
    components_js = """
    <script>
    function open_email(url) {
        window.open(url, '_blank');
    }
    </script>
    """
    st.sidebar.markdown(components_js, unsafe_allow_html=True)
    
    # Add a simple wrapper to match the styling exactly
    if "email_link_clicked" not in st.session_state:
        st.session_state.email_link_clicked = False
        
    # Use a plain button that matches the download button styling
    if st.sidebar.button("Step 2: Email Feedback", key="email_btn"):
        # This provides a button with identical styling to the download button
        st.session_state.email_link_clicked = True
        st.sidebar.markdown(f"""
        <script>
            open_email("{mailto_url}");
        </script>
        """, unsafe_allow_html=True)
    
    st.sidebar.info("Please attach the downloaded JSON file to your email before sending.")

def main():
    st.set_page_config(
        page_title="Astronomy Research Idea Generator",
        page_icon="🔭",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add minimal CSS to ensure proper spacing
    st.markdown("""
    <style>
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a title in a container with proper spacing
    with st.container():
        st.title("🔭 Astronomy Research Idea Generator")
    
    # Initialize session state
    initialize_session_state()
    
    # Handle generate trigger - this runs the full pipeline
    if st.session_state.trigger_generate:
        run_full_pipeline()
        st.session_state.trigger_generate = False
    
    # Handle user feedback trigger - this improves the idea based on user feedback
    if st.session_state.trigger_user_improvement:
        process_user_feedback()
    
    # Sidebar for inputs and actions
    with st.sidebar:
        # Only continue if API key is provided
        if st.session_state.api_key:
            st.header("Student Profile")
            
            # Astronomy interests
            st.subheader("Research Interests")
            
            # Check if ASTRONOMY_SUBFIELDS is available and not empty
            if not ASTRONOMY_SUBFIELDS:
                st.error("No astronomy subfields found. Check your idea_agent.py file.")
                st.stop()
            
            # Create checkboxes for each subfield using unique keys
            for subfield in ASTRONOMY_SUBFIELDS:
                # Check if this interest is already selected
                is_selected = subfield.name in st.session_state.interests
                st.checkbox(
                    subfield.name,
                    value=is_selected,
                    help=subfield.description,
                    key=f"interest_{subfield.name}",
                    on_change=update_interests
                )
            
            # Skill level - direct widget
            st.select_slider(
                "Skill Level",
                options=["beginner", "intermediate", "advanced"],
                value=st.session_state.get("skill_level", "beginner"),
                help="Select your current level of expertise in astronomy research",
                key="skill_level"
            )
            
            # Time frame - direct widget
            st.select_slider(
                "Research Time Frame",
                options=["3 months", "6 months", "1 year", "2 years", "3 years", "4-5 years"],
                value=st.session_state.get("time_frame", "1 year"),
                help="Expected duration of your research project (3-6 months for summer students/interns)",
                key="time_frame"
            )
            
            # Available resources
            st.subheader("Available Resources")
            resource_options = [
                "University telescope (< 1 meter)",
                "University telescope (1-3 meters)",
                "Access to large telescope time (> 3 meters)",
                "High-performance computing cluster",
                "Public astronomical datasets",
                "Spectroscopy equipment",
                "Radio astronomy facilities",
                "Collaboration with other departments",
                "Advanced programming skills"
            ]
            
            # Store options for use in the update function
            st.session_state.resource_options = resource_options
            
            # Create checkboxes for each resource using unique keys
            for resource in resource_options:
                # Check if this resource is already selected
                is_selected = resource in st.session_state.resources
                st.checkbox(
                    resource,
                    value=is_selected,
                    key=f"resource_{resource}",
                    on_change=update_resources
                )
            
            # Additional context text area - direct widget
            additional_context_input = st.text_area(
                "Provide any additional information about yourself",
                value=st.session_state.additional_context,
                height=150,
                help="Include previous research experience, specific interests, career goals, or particular astronomy phenomena you're curious about.",
                key="additional_context_input"
            )
            
            # Update session state with the current value
            st.session_state.additional_context = additional_context_input
            
            # Add literature review toggle option
            st.checkbox(
                "Skip literature review (faster generation)",
                value=st.session_state.skip_literature_review,
                help="Turn this on to skip the literature review step and generate ideas faster.",
                key="skip_lit_review_checkbox",
                on_change=toggle_literature_review
            )
            
            # Action Buttons
            st.header("Actions")
            
            # Single button to run the entire pipeline
            st.button(
                "Generate Research Idea", 
                on_click=set_generate_trigger, 
                type="primary",
                key="btn_generate"
            )
            
            # Reset button
            st.button(
                "Start Over", 
                on_click=reset_state, 
                key="btn_reset"
            )
        else:
            st.header("Model Provider")
            provider = st.selectbox(
                "Select AI Model Provider",
                options=["openai-gpt-o1", "google-gemini-2.0-thinking", "claude-3-7-sonnet"],
                index=0 if st.session_state.provider == "azure" else (1 if st.session_state.provider == "google" else 2),
                key="provider_selection"
            )
            
            # Update the provider in session state - convert display name to internal name
            if provider == "openai-gpt-o1":
                st.session_state.provider = "azure"
            elif provider == "google-gemini-2.0-thinking":
                st.session_state.provider = "google"
            elif provider == "claude-3-7-sonnet":
                st.session_state.provider = "claude"
            
            # Show appropriate API key input based on provider
            st.header("API Key")
            if provider == "openai-gpt-o1":
                api_key_label = "Enter your Azure OpenAI API Key"
                api_key_help = "Get your API key from Azure OpenAI Service"
            elif provider == "google-gemini-2.0-thinking":
                api_key_label = "Enter your Google AI Studio API Key"
                api_key_help = "Get your API key from https://makersuite.google.com/app/apikey"
            else:  # Claude
                api_key_label = "Enter your Anthropic API Key"
                api_key_help = "Get your API key from https://console.anthropic.com/keys"
            
            api_key = st.text_input(
                api_key_label,
                type="password",
                help=api_key_help,
                key="api_key_input",
                value=st.session_state.api_key
            )
            
            # Always display the Apply button
            if st.button("Apply Provider/API Key", type="primary", key="apply_key_button"):
                if api_key:  # Only update if there's actually a key
                    st.session_state.api_key = api_key
                    st.session_state.idea_agent = None
                    st.session_state.reflection_agent = None
                    st.session_state.literature_agent = None
                    st.rerun()
                else:
                    st.error("Please enter an API key first")
            
            # Only continue if API key is provided
            if api_key and st.session_state.api_key == api_key:
                if not st.session_state.idea_agent:
                    try:
                        st.session_state.idea_agent = IdeaAgent(api_key, provider=st.session_state.provider)
                    except Exception as e:
                        st.error(f"Error initializing idea agent: {str(e)}")
                    
                if not st.session_state.reflection_agent:
                    try:
                        st.session_state.reflection_agent = AstronomyReflectionAgent(api_key, provider=st.session_state.provider)
                    except Exception as e:
                        st.error(f"Error initializing reflection agent: {str(e)}")
                
                if not st.session_state.literature_agent:
                    try:
                        st.session_state.literature_agent = LiteratureAgent(api_key, provider=st.session_state.provider)
                    except Exception as e:
                        st.error(f"Error initializing literature agent: {str(e)}")
                
                # Display Status
                st.success("API key set. Ready to generate ideas!")
        
        # Add feedback section at the bottom of the sidebar
        st.markdown("---")  # Add a separator
        
        # Check if we have a completed idea process
        if hasattr(st.session_state, 'improved_idea') and st.session_state.improved_idea:
            if st.button("📝 Send Feedback with log file", key="feedback_button"):
                send_feedback()
        else:
            # Replace the green button with a transparent Streamlit-style button
            if st.button("📝 Send Feedback", key="simple_feedback_button"):
                # Open mailto link directly
                email_subject = "Astro-agent feedback"
                mailto_url = f"mailto:sihany@stanford.edu?subject={email_subject}"
                
                # Use JavaScript to open the email client
                st.markdown(f"""
                <script>
                    window.open('{mailto_url}', '_blank');
                </script>
                """, unsafe_allow_html=True)
                
                st.info("Opening your email client...")

    # Main content area
    if st.session_state.app_stage == 'start':
        # Show welcome message and instructions
        display_welcome_page()
    
    elif st.session_state.app_stage == 'browse_subfields':
        # Display the subfields browser
        st.header("Astronomy Subfields")
        st.write("Browse through different astronomy subfields and their current research challenges:")
        
        for subfield in ASTRONOMY_SUBFIELDS:
            with st.expander(subfield.name):
                st.write(subfield.description)
                st.write("**Current Challenges:**")
                for challenge in subfield.current_challenges:
                    st.write(f"- {challenge}")
                st.write("**Required Skills:**")
                st.write(", ".join(subfield.required_skills))
    
    elif st.session_state.app_stage == 'idea_generated':
        # Display the generated idea
        st.subheader("📝 Research Idea", divider="rainbow")
        display_research_idea(st.session_state.current_idea)
        
        # Add user feedback section
        st.subheader("✏️ Provide Feedback", divider="gray")
        st.text_area(
            "If you have specific suggestions or requests to improve this idea, please provide them below:",
            value=st.session_state.user_feedback,
            height=150,
            key="user_feedback",
            help="Your feedback will be used to refine the research idea further."
        )
        
        # Add button to submit feedback
        if st.button("Submit Feedback and Refine Idea", key="btn_submit_feedback", type="primary"):
            submit_user_feedback()
        
        # If we're showing the process, display the next steps
        if st.session_state.show_process:
            st.subheader("Next Steps", divider="gray")
            st.write("The following steps will be performed to improve your research idea:")
            st.write("1. ✅ Generate initial research idea")
            st.write("2. 🔄 Perform literature review (in progress)")
            st.write("3. 🔄 Get expert feedback")
            st.write("4. 🔄 Refine the idea")
    
    elif st.session_state.app_stage == 'literature_reviewed':
        # Display the generated idea
        st.subheader("📝 Research Idea", divider="rainbow")
        display_research_idea(st.session_state.current_idea)
        
        # Display literature review
        st.subheader("📚 Literature Review", divider="rainbow")
        display_literature_review(st.session_state.literature_feedback)
        
        # Add user feedback section
        st.subheader("✏️ Provide Feedback", divider="gray")
        st.text_area(
            "If you have specific suggestions or requests to improve this idea, please provide them below:",
            value=st.session_state.user_feedback,
            height=150,
            key="user_feedback",
            help="Your feedback will be used to refine the research idea further."
        )
        
        # Add button to submit feedback
        if st.button("Submit Feedback and Refine Idea", key="btn_submit_feedback_alt", type="primary"):
            submit_user_feedback()
        
        # If we're showing the process, display the next steps
        if st.session_state.show_process:
            st.subheader("Next Steps", divider="gray")
            st.write("The following steps will be performed to improve your research idea:")
            st.write("1. ✅ Generate initial research idea")
            st.write("2. ✅ Perform literature review")
            st.write("3. 🔄 Get expert feedback (in progress)")
            st.write("4. 🔄 Refine the idea")
    
    elif st.session_state.app_stage == 'feedback_received':
        # Display the generated idea
        st.subheader("📝 Initial Research Idea", divider="rainbow")
        display_research_idea(st.session_state.current_idea)
        
        # Display literature review if available
        if st.session_state.literature_feedback:
            st.subheader("📚 Literature Review", divider="rainbow")
            display_literature_review(st.session_state.literature_feedback)
        
        # Display the expert feedback
        st.subheader("🔍 Expert Feedback", divider="rainbow")
        display_feedback(st.session_state.feedback)
        
        # If we're showing the process, display the next steps
        if st.session_state.show_process:
            st.subheader("Next Steps", divider="gray")
            st.write("The following steps will be performed to improve your research idea:")
            st.write("1. ✅ Generate initial research idea")
            st.write("2. ✅ Perform literature review")
            st.write("3. ✅ Get expert feedback")
            st.write("4. 🔄 Refine the idea (in progress)")
    
    elif st.session_state.app_stage == 'completed':
        # Display only the improved idea by default
        if not st.session_state.show_process:
            st.subheader("⭐ Refined Research Idea", divider="rainbow")
            # Check if this is a user-improved idea
            is_user_improved = st.session_state.has_user_feedback and st.session_state.user_improved_idea is not None
            display_research_idea(st.session_state.improved_idea, is_user_improved=is_user_improved)
            
            # Add user feedback section
            st.subheader("✏️ Provide Additional Feedback", divider="gray")
            st.text_area(
                "If you have specific suggestions or requests to improve this idea further, please provide them below:",
                value=st.session_state.user_feedback,
                height=150,
                key="user_feedback",
                help="Your feedback will be used to refine the research idea further."
            )
            
            # Add button to submit feedback
            if st.button("Submit Feedback and Refine Idea", key="btn_submit_feedback_alt", type="primary"):
                submit_user_feedback()
            
            # Add button to toggle detailed process view
            st.button(
                "Show Development Process", 
                on_click=toggle_process_view,
                key="btn_show_process"
            )
        
        # Display the full process if requested
        else:
            # Display the original idea
            st.subheader("📝 Initial Research Idea", divider="rainbow")
            display_research_idea(st.session_state.current_idea)
            
            # Display literature review if available
            if st.session_state.literature_feedback:
                st.subheader("📚 Literature Review", divider="rainbow")
                display_literature_review(st.session_state.literature_feedback)
            
            # Display user feedback if available
            if st.session_state.has_user_feedback and st.session_state.user_feedback:
                st.subheader("💬 Your Feedback", divider="rainbow")
                st.markdown(f"**You provided the following feedback:**")
                st.markdown(f"*{st.session_state.user_feedback}*")
            
            # Display the expert feedback
            st.subheader("🔍 Expert Feedback", divider="rainbow")
            display_feedback(st.session_state.feedback)
            
            # Display the improved idea
            st.subheader("⭐ Refined Research Idea", divider="rainbow")
            # Check if this is a user-improved idea
            is_user_improved = st.session_state.has_user_feedback and st.session_state.user_improved_idea is not None
            display_research_idea(st.session_state.improved_idea, is_user_improved=is_user_improved)
            
            # Display comparison
            st.subheader("📊 Improvement Comparison", divider="rainbow")
            display_comparison(st.session_state.current_idea, 
                              st.session_state.improved_idea, 
                              st.session_state.feedback)
            
            # Add button to hide the detailed process
            st.button(
                "Hide Development Process", 
                on_click=toggle_process_view,
                key="btn_hide_process"
            )

def display_welcome_page():
    """Show welcome message and instructions"""
    st.markdown("""
    ## Welcome to the Astronomy Research Idea Generator
    
    This tool helps astronomy students explore potential research directions by generating customized research proposals.
    
    ### How to use:
    1. Select your research interests in the sidebar
    2. Adjust your skill level and intended research timeframe
    3. Select available resources you have access to
    4. Add any additional context about yourself or interests (optional)
    5. Choose whether to include literature review (improves novelty but takes longer)
    6. Click "Generate Research Idea" to get a refined research proposal
    7. Use the "Show Development Process" button to see how the idea was improved
    
    ### About this tool:
    This tool uses an AI system to:
    1. Generate an initial research idea based on your interests and resources
    2. Conduct a literature review to assess novelty and current research trends
    3. Evaluate the idea with expert astronomical knowledge
    4. Refine the idea based on scientific feedback and literature insights
    
    You'll receive a polished research idea that's both scientifically sound, novel, and feasible for your skill level and timeframe.
    """)
    
    # Display sample subfields
    st.subheader("Astronomy Subfields Available:")
    cols = st.columns(2)
    for i, subfield in enumerate(ASTRONOMY_SUBFIELDS):
        with cols[i % 2]:
            with st.expander(subfield.name):
                st.write(subfield.description)
                st.write("**Current Challenges:**")
                for challenge in subfield.current_challenges:
                    st.write(f"- {challenge}")
                st.write("**Required Skills:**")
                st.write(", ".join(subfield.required_skills))

def display_research_idea(idea, is_user_improved=False):
    """Display a research idea in a formatted way"""
    if not idea or not isinstance(idea, dict):
        st.error("Invalid research idea format")
        return
    
    # Display title
    st.header(idea.get("title", "Research Idea"))
    
    # Add user feedback badge if applicable
    if is_user_improved:
        st.markdown("🔄 **This idea has been refined based on your feedback**")
    
    # Create columns for metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Subfields:** {', '.join(idea.get('subfields', []))}")
    with col2:
        st.info(f"**Skill Level:** {idea.get('skill_level', '').capitalize()}")
    with col3:
        st.info(f"**Time Frame:** {idea.get('time_frame', '')}")
    
    # Get the idea content
    idea_content = idea.get("idea", {})
    if not idea_content:
        st.warning("No detailed content available for this idea")
        return
    
    # Display the research question prominently
    st.subheader("Research Question")
    st.write(idea_content.get("Research Question", ""))
    
    # Create tabs for the remaining sections
    tab_names = ["Background", "Methodology", "Expected Outcomes", "Challenges", "Required Skills", "Broader Connections"]
    content_keys = ["Background", "Methodology", "Expected Outcomes", "Potential Challenges", "Required Skills", "Broader Connections"]
    
    tabs = st.tabs(tab_names)
    
    for i, tab in enumerate(tabs):
        with tab:
            st.write(idea_content.get(content_keys[i], ""))
    
    # Resources section
    st.subheader("Recommended Resources")
    st.write(", ".join(idea.get("resources_needed", [])))
    
    # Add export options
    version_tag = f"v{idea.get('version', '1')}" if 'version' in idea else "research_idea"
    if st.button(f"Export as JSON", key=f"export_{idea.get('title', '')[:10]}_{version_tag}"):
        st.download_button(
            label="Download JSON",
            data=json.dumps(idea, indent=2),
            file_name=f"astronomy_{version_tag}.json",
            mime="application/json"
        )
    
    # Add button to export the full process
    if st.button(f"Export Full Process", key=f"export_process_{idea.get('title', '')[:10]}_{version_tag}"):
        # Create a comprehensive export that includes the development process
        export_data = {
            "final_idea": idea,
            "development_process": {
                "initial_idea": st.session_state.current_idea,
                "has_user_feedback": st.session_state.has_user_feedback if hasattr(st.session_state, 'has_user_feedback') else False,
                "user_feedback": st.session_state.user_feedback if hasattr(st.session_state, 'user_feedback') else None,
            }
        }
        
        # Add expert feedback if available
        if hasattr(st.session_state, 'feedback') and st.session_state.feedback:
            # Convert feedback object to dict for JSON serialization
            if hasattr(st.session_state.feedback, '__dict__'):
                feedback_dict = st.session_state.feedback.__dict__
            else:
                feedback_dict = {}
                for attr in dir(st.session_state.feedback):
                    if not attr.startswith('_') and not callable(getattr(st.session_state.feedback, attr)):
                        feedback_dict[attr] = getattr(st.session_state.feedback, attr)
            
            export_data["development_process"]["expert_feedback"] = feedback_dict
        
        # Add literature feedback if available
        if hasattr(st.session_state, 'literature_feedback') and st.session_state.literature_feedback:
            # Convert feedback object to dict for JSON serialization
            if hasattr(st.session_state.literature_feedback, '__dict__'):
                literature_dict = st.session_state.literature_feedback.__dict__
            else:
                literature_dict = {}
                for attr in dir(st.session_state.literature_feedback):
                    if not attr.startswith('_') and not callable(getattr(st.session_state.literature_feedback, attr)):
                        literature_dict[attr] = getattr(st.session_state.literature_feedback, attr)
            
            export_data["development_process"]["literature_feedback"] = literature_dict
        
        st.download_button(
            label="Download Full Process JSON",
            data=json.dumps(export_data, indent=2, default=str),
            file_name=f"astronomy_full_process_{version_tag}.json",
            mime="application/json"
        )

def display_literature_review(literature_feedback):
    """Display literature review in a structured way"""
    if not literature_feedback:
        st.error("No literature review available")
        return
    
    # Display novelty score
    if hasattr(literature_feedback, 'novelty_score'):
        score = literature_feedback.novelty_score
        st.subheader("Novelty Assessment")
        
        # Create a color gradient from red (1) to green (10)
        color = f"rgb({max(0, 255 - (score * 25))}, {min(255, score * 25)}, 0)"
        
        st.markdown(
            f"""
            <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="margin: 0; color: {color}; text-align: center;">Novelty Score: {score}/10</h3>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Display similar papers
    if hasattr(literature_feedback, 'similar_papers') and literature_feedback.similar_papers:
        st.subheader("Similar Recent Papers")
        
        for i, paper in enumerate(literature_feedback.similar_papers, 1):
            with st.expander(f"{i}. {paper.get('title', 'Untitled Paper')}"):
                if 'authors' in paper and paper['authors']:
                    st.write(f"**Authors:** {paper['authors']}")
                if 'year' in paper and paper['year']:
                    st.write(f"**Year:** {paper['year']}")
                if 'journal' in paper and paper['journal']:
                    st.write(f"**Journal:** {paper['journal']}")
                if 'relevance' in paper and paper['relevance']:
                    st.write(f"**Relevance:** {paper['relevance']}")
                if 'url' in paper and paper['url']:
                    st.write(f"**Link:** [{paper['url']}]({paper['url']})")
                if 'summary' in paper and paper['summary']:
                    st.write("**Abstract:**")
                    st.write(paper['summary'])
    else:
        st.info("No directly relevant papers were found in the search. This could indicate a novel research direction or that the search terms need refinement.")
    
    # Display novelty assessment
    if hasattr(literature_feedback, 'novelty_assessment') and literature_feedback.novelty_assessment:
        st.subheader("Novelty Analysis")
        st.write(literature_feedback.novelty_assessment)
    
    # Display differentiation suggestions
    if hasattr(literature_feedback, 'differentiation_suggestions') and literature_feedback.differentiation_suggestions:
        st.subheader("Differentiation Suggestions")
        for i, suggestion in enumerate(literature_feedback.differentiation_suggestions, 1):
            st.write(f"{i}. {suggestion}")
    
    # Display emerging trends
    if hasattr(literature_feedback, 'emerging_trends') and literature_feedback.emerging_trends:
        st.subheader("Emerging Trends")
        st.write(literature_feedback.emerging_trends)
    
    # Display recommended improvements
    if hasattr(literature_feedback, 'recommended_improvements') and literature_feedback.recommended_improvements:
        st.subheader("Recommended Improvements")
        for i, improvement in enumerate(literature_feedback.recommended_improvements, 1):
            st.write(f"{i}. {improvement}")
    
    # Display summary
    if hasattr(literature_feedback, 'summary') and literature_feedback.summary:
        st.subheader("Summary")
        st.write(literature_feedback.summary)
    
    st.caption("This literature review is based solely on real papers from academic sources. For a more comprehensive review, consider searching additional databases such as ADS, Web of Science, or Scopus.")

def display_feedback(feedback):
    """Display expert feedback in a structured way"""
    if not feedback:
        st.error("No feedback available")
        return
    
    # Scientific validity section
    st.subheader("Scientific Validity")
    col1, col2 = st.columns(2)
    
    # Extract scientific validity content
    scientific_strengths = []
    scientific_concerns = []
    
    if hasattr(feedback, 'scientific_validity'):
        if isinstance(feedback.scientific_validity, dict):
            scientific_strengths = feedback.scientific_validity.get("strengths", [])
            scientific_concerns = feedback.scientific_validity.get("concerns", [])
    
    with col1:
        st.write("**Strengths:**")
        if scientific_strengths:
            for strength in scientific_strengths:
                st.write(f"✅ {strength}")
        else:
            # If we have overall assessment but no parsed strengths, display a generic message
            if hasattr(feedback, 'summary') and feedback.summary:
                st.write("See overall assessment for details.")
            else:
                st.write("No specific strengths mentioned.")
    
    with col2:
        st.write("**Concerns:**")
        if scientific_concerns:
            for concern in scientific_concerns:
                st.write(f"⚠️ {concern}")
        elif hasattr(feedback, 'summary') and feedback.summary:
            # Extract concerns from summary if possible
            st.write("Key concerns are addressed in the overall assessment.")
            st.write("Review the assessment and recommendations for details.")
        else:
            st.write("No concerns identified.")
    
    # Methodological assessment
    st.subheader("Methodology Assessment")
    col1, col2 = st.columns(2)
    
    # Extract methodology content
    method_strengths = []
    method_concerns = []
    
    if hasattr(feedback, 'methodology'):
        if isinstance(feedback.methodology, dict):
            method_strengths = feedback.methodology.get("strengths", [])
            method_concerns = feedback.methodology.get("concerns", [])
    
    with col1:
        st.write("**Strengths:**")
        if method_strengths:
            for strength in method_strengths:
                st.write(f"✅ {strength}")
        else:
            # If we have recommendations but no parsed strengths, display a generic message
            if hasattr(feedback, 'recommendations') and feedback.recommendations:
                st.write("See recommendations for details.")
            else:
                st.write("No specific strengths mentioned.")
    
    with col2:
        st.write("**Concerns:**")
        if method_concerns:
            for concern in method_concerns:
                st.write(f"⚠️ {concern}")
        elif hasattr(feedback, 'recommendations') and feedback.recommendations:
            st.write("See recommendations for specific areas to improve.")
        else:
            st.write("No concerns identified.")
    
    # Other assessments
    has_detailed_assessment = (hasattr(feedback, 'novelty_assessment') and feedback.novelty_assessment.strip()) or \
                             (hasattr(feedback, 'impact_assessment') and feedback.impact_assessment.strip()) or \
                             (hasattr(feedback, 'feasibility_assessment') and feedback.feasibility_assessment.strip())
    
    if has_detailed_assessment or (hasattr(feedback, 'recommendations') and feedback.recommendations):
        assessment_tabs = st.tabs(["Novelty", "Impact", "Feasibility", "Recommendations"])
        
        with assessment_tabs[0]:
            if hasattr(feedback, 'novelty_assessment') and feedback.novelty_assessment.strip():
                st.write(feedback.novelty_assessment)
            else:
                st.write("No specific novelty assessment provided.")
        
        with assessment_tabs[1]:
            if hasattr(feedback, 'impact_assessment') and feedback.impact_assessment.strip():
                st.write(feedback.impact_assessment)
            else:
                st.write("No specific impact assessment provided.")
        
        with assessment_tabs[2]:
            if hasattr(feedback, 'feasibility_assessment') and feedback.feasibility_assessment.strip():
                st.write(feedback.feasibility_assessment)
            else:
                st.write("No specific feasibility assessment provided.")
        
        with assessment_tabs[3]:
            st.write("**Key Recommendations:**")
            if hasattr(feedback, 'recommendations') and feedback.recommendations:
                for i, rec in enumerate(feedback.recommendations, 1):
                    st.write(f"{i}. {rec}")
            else:
                st.write("No specific recommendations provided.")
    
    # Summary
    st.subheader("Overall Assessment")
    if hasattr(feedback, 'summary') and feedback.summary:
        st.write(feedback.summary)
    else:
        st.write("No overall assessment available.")
        
    # Add a fallback section if no structured data was found
    if not has_detailed_assessment and not (hasattr(feedback, 'summary') and feedback.summary):
        st.warning("⚠️ The feedback format was not fully structured. Check the raw feedback below:")
        with st.expander("Raw Feedback"):
            st.write(str(feedback))

def display_comparison(original_idea, improved_idea, feedback):
    """Display a comparison between original and improved ideas"""
    if not original_idea or not improved_idea or not feedback:
        st.error("Missing data for comparison")
        return
    
    # Title comparison
    st.subheader("1. Title Change")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Original:**")
        st.write(original_idea['title'])
    with col2:
        st.write("**Refined:**")
        st.write(improved_idea['title'])
    
    # Research Question comparison
    st.subheader("2. Research Question Refinement")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Original:**")
        original_question = original_idea['idea']['Research Question']
        st.write(original_question[:300] + "..." if len(original_question) > 300 else original_question)
    with col2:
        st.write("**Refined:**")
        improved_question = improved_idea['idea']['Research Question']
        st.write(improved_question[:300] + "..." if len(improved_question) > 300 else improved_question)
    
    # Scientific Improvements
    st.subheader("3. Key Scientific Improvements")
    scientific_concerns = []
    if hasattr(feedback, 'scientific_validity') and isinstance(feedback.scientific_validity, dict):
        scientific_concerns = feedback.scientific_validity.get("concerns", [])
    
    if scientific_concerns:
        for concern in scientific_concerns:
            st.write(f"🔄 **Addressed:** {concern}")
    else:
        st.write("No specific scientific concerns were identified.")
    
    # Methodological Improvements
    st.subheader("4. Methodological Improvements")
    methodological_concerns = []
    if hasattr(feedback, 'methodology') and isinstance(feedback.methodology, dict):
        methodological_concerns = feedback.methodology.get("concerns", [])
    
    if methodological_concerns:
        for concern in methodological_concerns:
            st.write(f"🔄 **Improved:** {concern}")
    else:
        st.write("No specific methodological concerns were identified.")
    
    # Novelty Improvements (new)
    st.subheader("5. Novelty Improvements")
    if hasattr(feedback, 'literature_insights') and feedback.literature_insights:
        novel_recs = feedback.literature_insights.get('recommended_improvements', [])
        if novel_recs:
            for rec in novel_recs:
                st.write(f"🔄 **Enhanced:** {rec}")
        else:
            st.write("No specific novelty recommendations were identified.")
    else:
        st.write("No literature review was conducted.")
    
    # Recommendations Implemented
    st.subheader("6. Expert Recommendations Implemented")
    if hasattr(feedback, 'recommendations') and feedback.recommendations:
        for i, rec in enumerate(feedback.recommendations, 1):
            st.write(f"✓ {rec}")
    else:
        st.write("No specific recommendations were provided.")

if __name__ == "__main__":
    main()