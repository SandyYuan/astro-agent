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
    from idea_agent import IdeaAgent, generate_research_idea
    from subfields import ASTRONOMY_SUBFIELDS
    from reflection_agent import AstronomyReflectionAgent, ProposalFeedback
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.write("Please make sure your generator code is in a file named 'idea_agent.py' and reflection code in 'reflection_agent.py'")
    st.stop()

# Import or initialize your client
try:
    from config import google_key
    from google import genai
    client = genai.Client(api_key=google_key)
except ImportError as e:
    st.error(f"Client Import Error: {e}")
    st.write("Please make sure your API configuration is set up correctly")
    client = None

def initialize_session_state():
    """Initialize all session state variables if they don't exist"""
    if 'idea_agent' not in st.session_state:
        st.session_state.idea_agent = IdeaAgent(client) if client else None
    if 'reflection_agent' not in st.session_state:
        st.session_state.reflection_agent = AstronomyReflectionAgent(client) if client else None
    if 'current_idea' not in st.session_state:
        st.session_state.current_idea = None
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
    if 'improved_idea' not in st.session_state:
        st.session_state.improved_idea = None
    if 'app_stage' not in st.session_state:
        # Possible values: 'start', 'idea_generated', 'feedback_received', 'idea_improved'
        st.session_state.app_stage = 'start'
    if 'interests' not in st.session_state:
        st.session_state.interests = []
    if 'resources' not in st.session_state:
        st.session_state.resources = ["Public astronomical datasets"]
    if 'additional_context' not in st.session_state:
        st.session_state.additional_context = ""
    # Action triggers
    if 'trigger_generate' not in st.session_state:
        st.session_state.trigger_generate = False
    if 'trigger_feedback' not in st.session_state:
        st.session_state.trigger_feedback = False
    if 'trigger_improve' not in st.session_state:
        st.session_state.trigger_improve = False
    if 'trigger_reset' not in st.session_state:
        st.session_state.trigger_reset = False

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

def set_feedback_trigger():
    st.session_state.trigger_feedback = True

def set_improve_trigger():
    st.session_state.trigger_improve = True

def set_reset_trigger():
    st.session_state.trigger_reset = True

def main():
    st.set_page_config(
        page_title="Astronomy Research Idea Generator",
        page_icon="🔭",
        layout="wide"
    )
    
    st.title("🔭 Astronomy Research Idea Generator")
    
    # Initialize session state
    initialize_session_state()
    
    # Handle reset first if triggered
    if st.session_state.trigger_reset:
        st.session_state.current_idea = None
        st.session_state.feedback = None
        st.session_state.improved_idea = None
        st.session_state.app_stage = 'start'
        st.session_state.trigger_reset = False
    
    # Handle generate action if triggered
    if st.session_state.trigger_generate:
        with st.spinner("Generating research idea..."):
            try:
                if st.session_state.idea_agent:
                    # Use stateful agent
                    research_idea = st.session_state.idea_agent.generate_initial_idea(
                        student_interests=st.session_state.interests,
                        skill_level=st.session_state.skill_level,
                        time_frame=st.session_state.time_frame,
                        available_resources=st.session_state.resources,
                        additional_context=st.session_state.additional_context
                    )
                else:
                    # Use standalone function
                    research_idea = generate_research_idea(
                        student_interests=st.session_state.interests,
                        skill_level=st.session_state.skill_level,
                        time_frame=st.session_state.time_frame,
                        available_resources=st.session_state.resources,
                        additional_context=st.session_state.additional_context
                    )
                
                # Store the generated idea and update app stage
                st.session_state.current_idea = research_idea
                st.session_state.app_stage = 'idea_generated'
            except Exception as e:
                st.error(f"Error generating research idea: {str(e)}")
                st.exception(e)
        
        # Reset trigger
        st.session_state.trigger_generate = False
    
    # Handle feedback action if triggered
    if st.session_state.trigger_feedback and st.session_state.current_idea:
        with st.spinner("Getting expert feedback..."):
            try:
                # Get feedback using the reflection agent
                feedback = st.session_state.reflection_agent.evaluate_proposal(st.session_state.current_idea)
                
                # Store the feedback and update app stage
                st.session_state.feedback = feedback
                st.session_state.app_stage = 'feedback_received'
            except Exception as e:
                st.error(f"Error getting expert feedback: {str(e)}")
                st.exception(e)
        
        # Reset trigger
        st.session_state.trigger_feedback = False
    
    # Handle improve action if triggered
    if st.session_state.trigger_improve and st.session_state.feedback:
        with st.spinner("Improving research idea..."):
            try:
                # Improve the idea using the feedback
                improved_idea = st.session_state.idea_agent.improve_idea(st.session_state.feedback.__dict__)
                
                # Store the improved idea and update app stage
                st.session_state.improved_idea = improved_idea
                st.session_state.app_stage = 'idea_improved'
            except Exception as e:
                st.error(f"Error improving idea: {str(e)}")
                st.exception(e)
        
        # Reset trigger
        st.session_state.trigger_improve = False
    
    # Sidebar for inputs and actions
    with st.sidebar:
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
        
        # Action Buttons - these are always displayed but conditionally enabled
        st.header("Actions")
        
        # Generate button is always enabled
        st.button("Generate Research Idea", 
                 on_click=set_generate_trigger, 
                 type="primary",
                 key="btn_generate")
        
        # Feedback button enabled if we have a current idea
        feedback_disabled = st.session_state.app_stage not in ['idea_generated', 'feedback_received', 'idea_improved']
        st.button("Get Expert Feedback", 
                 on_click=set_feedback_trigger, 
                 disabled=feedback_disabled,
                 type="secondary",
                 key="btn_feedback")
        
        # Improve button enabled if we have feedback
        improve_disabled = st.session_state.app_stage not in ['feedback_received', 'idea_improved']
        st.button("Improve Research Idea", 
                 on_click=set_improve_trigger, 
                 disabled=improve_disabled,
                 type="secondary",
                 key="btn_improve")
        
        # Reset button
        st.button("Start Over", 
                 on_click=set_reset_trigger, 
                 key="btn_reset")
        
        # Debug information
        with st.expander("Debug Info"):
            st.write(f"App Stage: {st.session_state.app_stage}")
            st.write(f"Current Idea: {'Present' if st.session_state.current_idea else 'None'}")
            st.write(f"Feedback: {'Present' if st.session_state.feedback else 'None'}")
            st.write(f"Improved Idea: {'Present' if st.session_state.improved_idea else 'None'}")
            st.write(f"Interests: {st.session_state.interests}")
            st.write(f"Resources: {st.session_state.resources}")
    
    # Main content area - displays based on app stage
    if st.session_state.app_stage == 'start':
        # Show welcome message and instructions
        display_welcome_page()
    
    elif st.session_state.app_stage == 'idea_generated' or st.session_state.app_stage in ['feedback_received', 'idea_improved']:
        # Display the original idea
        st.subheader("📝 Generated Research Idea", divider="rainbow")
        display_research_idea(st.session_state.current_idea)
        
        # If we have feedback, display it
        if st.session_state.app_stage in ['feedback_received', 'idea_improved']:
            st.subheader("🔍 Expert Feedback", divider="rainbow")
            display_feedback(st.session_state.feedback)
        
        # If we have an improved idea, display it
        if st.session_state.app_stage == 'idea_improved':
            st.subheader("⭐ Improved Research Idea", divider="rainbow")
            display_research_idea(st.session_state.improved_idea)
            
            # Display comparison
            st.subheader("📊 Improvement Comparison", divider="rainbow")
            display_comparison(st.session_state.current_idea, 
                              st.session_state.improved_idea, 
                              st.session_state.feedback)

def display_welcome_page():
    """Show welcome message and instructions"""
    st.markdown("""
    ## Welcome to the Astronomy Research Idea Generator
    
    This tool helps incoming graduate students explore potential research directions in astronomy.
    
    ### How to use:
    1. Select your research interests in the sidebar
    2. Adjust your skill level and intended research timeframe
    3. Select available resources you have access to
    4. Add any additional context about yourself or interests (optional)
    5. Click "Generate Research Idea" to get a personalized research suggestion
    6. Get expert feedback on your idea
    7. Improve your idea based on the feedback
    
    ### About this tool:
    This generator uses an LLM to create contextually relevant and achievable research ideas
    based on current challenges in various astronomy subfields. The expert feedback system
    evaluates the scientific validity and methodology of your idea, and helps you improve it.
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
    version_tag = f"v{idea.get('version', '1')}" if 'version' in idea else "original"
    if st.button(f"Export {version_tag} as JSON", key=f"export_{idea.get('title', '')[:10]}_{version_tag}"):
        st.download_button(
            label="Download JSON",
            data=json.dumps(idea, indent=2),
            file_name=f"astronomy_research_idea_{version_tag}.json",
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
    st.subheader("1. Title Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Original:**")
        st.write(original_idea['title'])
    with col2:
        st.write("**Improved:**")
        st.write(improved_idea['title'])
    
    # Research Question comparison
    st.subheader("2. Research Question Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Original:**")
        original_question = original_idea['idea']['Research Question']
        st.write(original_question[:300] + "..." if len(original_question) > 300 else original_question)
    with col2:
        st.write("**Improved:**")
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
    st.subheader("5. Recommendations Implemented")
    if hasattr(feedback, 'recommendations') and feedback.recommendations:
        for i, rec in enumerate(feedback.recommendations, 1):
            st.write(f"✓ {rec}")
    else:
        st.write("No specific recommendations were provided.")

if __name__ == "__main__":
    main()