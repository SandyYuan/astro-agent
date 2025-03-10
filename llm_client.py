from typing import Optional, Dict, Any, List
import os

class LLMClient:
    """Wrapper for LLM clients to provide a consistent interface"""
    
    def __init__(self, api_key: str, provider: str = "azure"):
        """Initialize the LLM client with the appropriate provider
        
        Args:
            api_key: API key for the selected provider
            provider: 'azure' or 'google'
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
        
        # Fallback (should never reach here)
        raise ValueError(f"Unsupported provider: {self.provider}") 