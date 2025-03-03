# 🔭 Astronomy Research Idea Generator

A Streamlit-based application that leverages AI to help astronomy students generate, evaluate, and refine research proposals.

## About

The Astronomy Research Idea Generator is designed to assist astronomy students and researchers at all skill levels in developing scientifically sound, novel, and feasible research projects. The system uses a multi-agent AI approach to:

1. Generate tailored research ideas based on student interests, skill level, and available resources
2. Review recent scientific literature to assess novelty and identify emerging trends
3. Provide expert-level feedback on scientific validity and methodology
4. Refine the initial idea to address feedback and improve quality

## Features

- **Personalized Research Idea Generation**: Creates research proposals tailored to specific interests, skill levels, and timeframes
- **ArXiv Literature Review**: Searches and analyzes recent papers to enhance novelty and relevance
- **Expert Feedback**: Provides detailed critique on scientific validity, methodology, novelty, impact, and feasibility
- **Idea Refinement**: Automatically improves the research idea based on expert feedback and literature insights
- **Interactive Web Interface**: Easy-to-use Streamlit interface for inputting preferences and viewing results
- **Comprehensive Research Proposal**: Generates structured proposals with research questions, background, methodology, expected outcomes, and more

## How It Works

The system implements a four-stage pipeline:

1. **Idea Generation**: Using the student's profile (interests, skill level, timeframe, and available resources), the Idea Agent generates an initial research proposal
2. **Literature Review**: The Literature Agent searches ArXiv for relevant papers from the past two years, evaluates novelty, and identifies emerging trends
3. **Expert Evaluation**: The Reflection Agent analyzes the proposal for scientific validity, methodological soundness, novelty, impact, and feasibility
4. **Idea Refinement**: The Idea Agent takes the feedback and literature insights to create an improved version of the research proposal

## System Architecture

The application consists of three main agent components:

- **Idea Agent**: Generates and refines astronomy research ideas
- **Literature Agent**: Conducts literature searches and evaluates proposal novelty
- **Reflection Agent**: Evaluates proposals and provides expert feedback

All agents utilize Google's Gemini AI models through the Google AI Studio API.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/astronomy-idea-generator.git
cd astronomy-idea-generator
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Get a Google AI Studio API key from [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Enter your Google AI Studio API key when prompted

3. Configure your research profile:
   - Select astronomy subfields of interest
   - Specify your skill level (beginner, intermediate, advanced)
   - Set the research timeframe
   - Select available resources
   - Add any additional context about your background or interests

4. Click "Generate Research Idea" to start the process

5. Review the refined research idea and optionally explore the development process

## Project Structure

- `app.py`: Main Streamlit application
- `idea_agent.py`: Agent that generates and improves astronomy research ideas
- `literature_agent.py`: Agent that searches ArXiv and reviews relevant literature
- `reflection_agent.py`: Agent that evaluates research proposals and provides feedback
- `subfields.py`: Database of astronomy subfields and current challenges
- `utils.py`: Utility functions

## Dependencies

- streamlit
- google-generativeai
- arxiv
- pandas
- nest_asyncio
- python-dateutil

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project uses Google's Gemini AI models
- ArXiv API for literature search capabilities
- Data on astronomy subfields compiled from various academic sources