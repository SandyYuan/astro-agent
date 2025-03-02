from google import genai

def create_client(api_key):
    """Create a new Google GenAI client with the given API key."""
    if not api_key:
        raise ValueError("API key cannot be empty")
    return genai.Client(api_key=api_key)