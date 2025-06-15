from typing import Optional, Dict, Any, List
import os

class LLMClient:
    """Wrapper for LLM clients to provide a consistent interface"""
    
    def __init__(self, api_key: str, provider: str = "azure"):
        """Initialize the LLM client with the appropriate provider
        
        Args:
            api_key: API key for the selected provider
            provider: 'azure', 'google', or 'claude'
        """
        self.api_key = api_key
        self.provider = provider
        
        if provider == "google":
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
            except ImportError:
                raise ImportError("googleai is not installed")
        elif provider == "azure":
            try:
                from langchain_openai import AzureChatOpenAI
                # Hard-coded Azure configuration
                self.client = AzureChatOpenAI(
                    azure_endpoint="https://utbd-omodels-advanced.openai.azure.com",
                    azure_deployment="o1",
                    api_version="2025-01-01-preview",
                    api_key=api_key
                )
            except ImportError:
                raise ImportError("langchain_openai is not installed")
        elif provider == "claude":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("anthropic is not installed")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def generate(self, prompt: str, temperature: float = 0.5) -> str:
        """Alias for generate_content for compatibility."""
        return self.generate_content(prompt, temperature)

    def generate_content(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate content using the configured LLM
        
        Args:
            prompt: The prompt to send to the LLM
            temperature: Temperature for generation
            
        Returns:
            Generated text response
        """
        if self.provider == "google":
            response = self.client.models.generate_content(
                model="gemini-2.5-pro-preview-06-05", 
                contents=prompt
            )
            return response.text
        elif self.provider == "azure":
            # For Azure, we can directly invoke the client
            response = self.client.invoke(prompt)
            return response.content
        elif self.provider == "claude":
            # For Claude, we need to structure the message differently
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.content[0].text
        
        # Fallback (should never reach here)
        raise ValueError(f"Unsupported provider: {self.provider}")

    def extract_json(self, text: str) -> Dict[str, Any]:
        """Extracts a JSON object from a string, cleaning it first."""
        import json
        try:
            # Find the first '{' and the last '}' to extract the JSON block
            start = text.find('{')
            end = text.rfind('}') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in the text.")
            
            json_str = text[start:end]
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Original text: {text}")
            raise ValueError("Failed to parse JSON from the model's response.") 