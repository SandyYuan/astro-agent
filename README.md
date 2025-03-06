# 🔭 Astronomy Research Idea Generator

Generate, evaluate, and refine research proposals.

## About

The Astronomy Research Idea Generator is designed to assist astronomy students and researchers at all skill levels in developing scientifically sound, novel, and feasible research projects. The system uses a multi-agent AI approach to:

1. Generate tailored research ideas based on student interests, skill level, and available resources
2. Review recent scientific literature to assess novelty and identify emerging trends
3. Provide expert-level feedback on scientific validity and methodology
4. Refine the initial idea to address feedback and improve quality

The system supports multiple AI model providers including Azure OpenAI, Google Gemini, and Claude.

## Setup

### Required API Keys

1. **AI Model Provider API Key**:
   - For Azure OpenAI: Get an API key from the Azure OpenAI service
   - For Google Gemini: Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - For Claude: Get an API key from [Anthropic](https://console.anthropic.com/)

2. **Google Custom Search API Setup** (for literature search):
   - Create a Google Cloud project at [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the "Custom Search API" in the Google Cloud Console
   - Create API credentials to get a Google API key
   - Create a Custom Search Engine at [Google Programmable Search Engine](https://programmablesearchengine.google.com/):
     - Add astronomy-related sites like arxiv.org, adsabs.harvard.edu, nature.com, science.org
     - Get your Search Engine ID (cx)
   - Set the following environment variables:
     ```
     GOOGLE_API_KEY=your_google_api_key
     GOOGLE_CSE_ID=your_custom_search_engine_id
     ```

## Usage

1. Enter your chosen AI model provider API key when prompted

2. Configure your research profile:
   - Select astronomy subfields of interest
   - Specify your skill level (beginner, intermediate, advanced)
   - Set the research timeframe
   - Select available resources
   - Add any additional context about your background or interests

3. Click "Generate Research Idea" to start the process

4. Review the refined research idea and optionally explore the development process

## Dependencies

- streamlit
- google-genai
- anthropic
- langchain-openai
- openai
- requests
- arxiv
- nest_asyncio
- python-dotenv

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

TBD

## Acknowledgments

- This project uses multiple AI models including Azure OpenAI, Google Gemini, and Claude
- Google Custom Search API for literature search capabilities
