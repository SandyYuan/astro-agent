# 🔭 Astronomy Research Idea Generator

Generate, evaluate, and refine research proposals.

## About

The Astronomy Research Idea Generator is designed to assist astronomy students and researchers at all skill levels in developing scientifically sound, novel, and feasible research projects. The system uses a multi-agent AI approach to:

1. Generate tailored research ideas based on student interests, skill level, and available resources
2. Review recent scientific literature to assess novelty and identify emerging trends
3. Provide expert-level feedback on scientific validity and methodology
4. Refine the initial idea to address feedback and improve quality

Currently, all agents utilize Google's Gemini AI models through the Google AI Studio API. I plan to make it work with other models too. 

## Usage

1. Get a Google AI Studio API key from [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

2. Go to [https://astro-agent.streamlit.app](https://astro-agent.streamlit.app). Enter your Google AI Studio API key when prompted

3. Configure your research profile:
   - Select astronomy subfields of interest
   - Specify your skill level (beginner, intermediate, advanced)
   - Set the research timeframe
   - Select available resources
   - Add any additional context about your background or interests

4. Click "Generate Research Idea" to start the process

5. Review the refined research idea and optionally explore the development process

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

TBD

## Acknowledgments

- This project uses Google's Gemini AI models
- ArXiv API for literature search capabilities
