# Astronomy Research Idea Generator

An AI-powered application that helps astronomy students generate, evaluate, and refine research ideas tailored to their interests, skill level, and available resources.

## Overview

This application uses a pipeline of specialized AI agents to create detailed, scientifically accurate astronomy research proposals. The system guides users through selecting their astronomy interests, skill level, and resources, then generates personalized research ideas that are both novel and feasible.

> **Recommendation**: We recommend using Google Gemini as the LLM backbone for this application. It offers powerful capabilities and is available for free with generous usage limits.

## Key Features

- **Personalized Research Idea Generation**: Creates astronomy research ideas tailored to the user's specific interests, skill level, time frame, and available resources
- **Scientific Evaluation**: Expert AI agent reviews the proposed idea and provides detailed feedback on scientific validity, methodology, novelty, and feasibility
- **Literature Review**: Searches recent arXiv papers to assess the novelty of the idea and identify relevant existing research
- **Idea Refinement**: Improves the initial research idea based on expert feedback and literature review
- **User Feedback Integration**: Allows users to provide feedback on the generated idea and receive a refined version
- **Comprehensive Documentation**: Provides detailed research proposals with background, methodology, expected outcomes, and more

## System Architecture

The application consists of three primary AI agents:

1. **Idea Agent**: Generates initial research ideas and refines them based on feedback
2. **Reflection Agent**: Evaluates research ideas and provides detailed expert feedback
3. **Literature Agent**: Conducts literature searches and analyzes the novelty of proposed ideas

## Setup Instructions

### Prerequisites

- Python 3.8+
- A Google Gemini API key (recommended) or other supported LLM provider

### Getting a Google Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key" and follow the instructions
4. Your API key will be displayed - save it securely for use with this application

### Installation

1. Clone this repository
```bash
git clone https://github.com/your-username/astronomy-idea-generator.git
cd astronomy-idea-generator
```

2. Install the required dependencies
```bash
pip install -r requirements.txt
```

3. Set up your API keys
   - Create a `secrets.toml` file in the `.streamlit` directory
   - Add your API keys, for example:
   ```
   GOOGLE_GEMINI_API_KEY = "your-gemini-api-key"
   ```

### Running the Application

Launch the Streamlit app:
```bash
streamlit run app.py
```

## Using the Application

1. **Select Research Parameters**:
   - Choose astronomy subfields of interest
   - Select your skill level
   - Specify your time frame
   - Choose available resources

2. **Generate Initial Idea**:
   - The system creates a detailed research proposal tailored to your specifications

3. **Review Expert Feedback**:
   - Expert analysis of scientific validity and methodology
   - Suggestions for improvement

4. **Literature Review**:
   - Analysis of recent papers in the field
   - Assessment of your idea's novelty
   - Recommendations for differentiation

5. **Improved Research Idea**:
   - The system generates a refined version that addresses feedback
   - Compare the original and improved versions

6. **User Feedback (Optional)**:
   - Provide your own feedback on the idea
   - Receive a further improved version based on your input

7. **Export Results**:
   - Download the full research proposal as JSON
   - Save the development process for reference

## Implementation Details

### IdeaAgent

The `IdeaAgent` is responsible for generating and improving research ideas. It creates detailed, structured astronomy research proposals by:

- Identifying relevant astronomy subfields based on user interests
- Selecting appropriate challenges and concepts
- Generating a comprehensive research proposal with all required sections
- Refining the proposal based on expert feedback and literature analysis

### ReflectionAgent

The `ReflectionAgent` evaluates research proposals with the expertise of an astronomy professor, providing:

- Assessment of scientific validity and accuracy
- Analysis of methodological soundness
- Evaluation of novelty and knowledge gaps
- Recommendations for improvement

### LiteratureAgent

The `LiteratureAgent` reviews recent astronomy literature by:

- Searching for relevant papers on arXiv
- Analyzing how the proposal relates to existing research
- Providing a novelty assessment
- Suggesting ways to differentiate the research
- Identifying emerging trends in the field

## Supporting LLM Providers

While we recommend Google Gemini, the application supports multiple LLM providers:

- **Google Gemini** (Recommended): Free with generous usage limits and excellent scientific reasoning
- Azure OpenAI Service
- Anthropic Claude (via API)

## Contributing

Contributions to improve the astronomy research idea generator are welcome. Please feel free to submit issues or pull requests.

## License

[MIT License](LICENSE)
