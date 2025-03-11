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
                model="gemini-2.0-flash-thinking-exp", 
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
                model="claude-3-7-sonnet-20250219",
                max_tokens=8000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            return response.content[0].text
        
        # Fallback (should never reach here)
        raise ValueError(f"Unsupported provider: {self.provider}") 