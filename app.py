import streamlit as st
import json
import asyncio
import nest_asyncio
import os

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Create a new event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Import your generator function and agents
try:
    from idea_agent import IdeaAgent, generate_research_idea, initialize_client as init_idea_client
    from subfields import ASTRONOMY_SUBFIELDS
    from reflection_agent import AstronomyReflectionAgent, ProposalFeedback, initialize_client as init_reflection_client
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.write("Please make sure your generator code is in a file named 'idea_agent.py' and reflection code in 'reflection_agent.py'")
    st.stop()

# # Import or initialize your client
# try:
#     from config import google_key
#     from google import genai
#     client = genai.Client(api_key=google_key)
# except ImportError as e:
#     st.error(f"Client Import Error: {e}")
#     st.write("Please make sure your API configuration is set up correctly")
#     client = None

# Import Google GenAI
try:
    from google import genai
except ImportError:
    st.error("Could not import Google GenerativeAI. Please install it with: pip install google-generativeai")
    st.stop()

def initialize_session_state():
    """Initialize all session state variables if they don't exist"""
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    if 'idea_agent' not in st.session_state:
        st.session_state.idea_agent = None
    if 'reflection_agent' not in st.session_state:
        st.session_state.reflection_agent = None
    if 'current_idea' not in st.session_state:
        st.session_state.current_idea = None
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
    if 'improved_idea' not in st.session_state:
        st.session_state.improved_idea = None
    if 'show_process' not in st.session_state:
        st.session_state.show_process = False
    if 'app_stage' not in st.session_state:
        # Possible values: 'start', 'completed'
        st.session_state.app_stage = 'start'
    if 'interests' not in st.session_state:
        st.session_state.interests = []
    if 'resources' not in st.session_state:
        st.session_state.resources = ["Public astronomical datasets"]
    if 'additional_context' not in st.session_state:
        st.session_state.additional_context = ""
    if 'trigger_generate' not in st.session_state:
        st.session_state.trigger_generate = False

def reset_state():
    """Reset the application state for a new idea generation"""
    st.session_state.current_idea = None
    st.session_state.feedback = None
    st.session_state.improved_idea = None
    st.session_state.show_process = False
    st.session_state.app_stage = 'start'

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

def toggle_process_view():
    st.session_state.show_process = not st.session_state.show_process

def run_full_pipeline():
    """Run the entire idea generation, feedback, and improvement pipeline"""
    # First check if we have valid agents
    if not st.session_state.idea_agent or not st.session_state.reflection_agent:
        st.error("API client not initialized. Please enter a valid API key.")
        return False

    try:
        # Step 1: Generate initial idea
        with st.spinner("Generating initial research idea..."):
            initial_idea = st.session_state.idea_agent.generate_initial_idea(
                student_interests=st.session_state.interests,
                skill_level=st.session_state.skill_level,
                time_frame=st.session_state.time_frame,
                available_resources=st.session_state.resources,
                additional_context=st.session_state.additional_context
            )
            
            if not initial_idea:
                st.error("Failed to generate initial research idea.")
                return False
                
            st.session_state.current_idea = initial_idea
        
        # Step 2: Get feedback
        with st.spinner("Getting expert feedback on the idea..."):
            feedback = st.session_state.reflection_agent.evaluate_proposal(initial_idea)
            
            if not feedback:
                st.error("Failed to get expert feedback.")
                # We can still continue with just the initial idea
                st.session_state.app_stage = 'idea_generated'
                return False
                
            st.session_state.feedback = feedback
        
        # Step 3: Improve idea
        with st.spinner("Refining research idea based on feedback..."):
            improved_idea = st.session_state.idea_agent.improve_idea(feedback.__dict__)
            
            if not improved_idea:
                st.error("Failed to refine the research idea.")
                # We still have the initial idea and feedback
                st.session_state.app_stage = 'feedback_received'
                return False
                
            st.session_state.improved_idea = improved_idea
        
        # Update app stage to completed
        st.session_state.app_stage = 'completed'
        return True
        
    except Exception as e:
        st.error(f"Error in research idea pipeline: {str(e)}")
        # Show detailed error in expandable section
        with st.expander("Error details"):
            st.exception(e)
        
        # Update app stage based on what we completed
        if hasattr(st.session_state, 'current_idea') and st.session_state.current_idea:
            if hasattr(st.session_state, 'feedback') and st.session_state.feedback:
                st.session_state.app_stage = 'feedback_received'
            else:
                st.session_state.app_stage = 'idea_generated'
                
        return False

def main():
    st.set_page_config(
        page_title="Astronomy Research Idea Generator",
        page_icon="🔭",
        layout="wide"
    )
    
    st.title("🔭 Astronomy Research Idea Generator")
    
    # Initialize session state
    initialize_session_state()
    
    # Handle generate trigger - this runs the full pipeline
    if st.session_state.trigger_generate:
        run_full_pipeline()
        st.session_state.trigger_generate = False
    
    # Sidebar for inputs and actions
    with st.sidebar:
        st.header("API Key")
        api_key = st.text_input(
            "Enter your Google AI Studio API Key",
            type="password",
            help="Get your API key from https://makersuite.google.com/app/apikey",
            key="api_key_input",
            value=st.session_state.api_key
        )
        
        # Only continue if API key is provided
        if api_key:
            st.session_state.api_key = api_key
            
            # Initialize clients with API key
            idea_client = init_idea_client(api_key)
            reflection_client = init_reflection_client(api_key)
            
            # Create agents if they don't exist
            if not st.session_state.idea_agent and idea_client:
                st.session_state.idea_agent = IdeaAgent(idea_client)
            if not st.session_state.reflection_agent and reflection_client:
                st.session_state.reflection_agent = AstronomyReflectionAgent(reflection_client)
                
            # Display Status
            st.success("API key set. Ready to generate ideas!")
            
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
            st.text_area(
                "Provide any additional information about yourself",
                value=st.session_state.additional_context,
                height=150,
                help="Include previous research experience, specific interests, career goals, or particular astronomy phenomena you're curious about.",
                key="additional_context"
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
            st.warning("Please enter your Google AI Studio API key to use this app.")
            # Stop further execution until API key is provided
            st.stop()

    # Main content area
    if st.session_state.app_stage == 'start':
        # Show welcome message and instructions
        display_welcome_page()
    
    elif st.session_state.app_stage == 'completed':
        # Display only the improved idea by default
        if not st.session_state.show_process:
            st.subheader("⭐ Refined Research Idea", divider="rainbow")
            display_research_idea(st.session_state.improved_idea)
            
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
            
            # Display the feedback
            st.subheader("🔍 Expert Feedback", divider="rainbow")
            display_feedback(st.session_state.feedback)
            
            # Display the improved idea
            st.subheader("⭐ Refined Research Idea", divider="rainbow")
            display_research_idea(st.session_state.improved_idea)
            
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
    5. Click "Generate Research Idea" to get a refined research proposal
    6. Use the "Show Development Process" button to see how the idea was improved
    
    ### About this tool:
    This tool uses an AI system to:
    1. Generate an initial research idea based on your interests and resources
    2. Evaluate that idea with expert astronomical knowledge
    3. Refine the idea based on scientific feedback
    
    You'll receive a polished research idea that's both scientifically sound and feasible for your skill level and timeframe.
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

def display_research_idea(idea):
    """Display a research idea in a formatted way"""
    if not idea or not isinstance(idea, dict):
        st.error("Invalid research idea format")
        return
        
    st.header(idea.get("title", "Research Idea"))
    
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
    
    # Display the main idea content
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
    
    # Recommendations Implemented
    st.subheader("5. Expert Recommendations Implemented")
    if hasattr(feedback, 'recommendations') and feedback.recommendations:
        for i, rec in enumerate(feedback.recommendations, 1):
            st.write(f"✓ {rec}")
    else:
        st.write("No specific recommendations were provided.")

if __name__ == "__main__":
    main()