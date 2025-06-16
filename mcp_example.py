#!/usr/bin/env python3
"""
Example script demonstrating how to use the Astronomy Research Assistant MCP server.

This script shows how to call the various tools provided by the MCP server.
In practice, you would use an MCP client library to interact with the server.
"""

import json
import asyncio
from typing import Dict, Any


# Example usage functions
def example_generate_idea():
    """Example of how to generate a research idea."""
    return {
        "provider": "google",
        "api_key": "your-api-key-here",
        "temperature": 0.7,
        "interests": "galaxy formation, cosmology, dark matter",
        "skill_level": "undergraduate",
        "resources": "Python, public datasets, university computing cluster",
        "time_frame": "1 year"
    }


def example_structure_idea():
    """Example of how to structure a raw research idea."""
    return {
        "provider": "google", 
        "api_key": "your-api-key-here",
        "temperature": 0.5,
        "user_idea": "I want to study how galaxies form in the early universe using machine learning to analyze telescope data"
    }


def example_literature_review():
    """Example of how to perform a literature review."""
    # This would typically be the output from structure_idea or generate_idea
    proposal = {
        "title": "Machine Learning Analysis of Early Galaxy Formation",
        "subfields": ["Cosmology", "Galaxy Formation"],
        "idea": {
            "Research Question": "How can machine learning techniques improve our understanding of galaxy formation processes in the early universe?",
            "Proposed Solution": "Apply convolutional neural networks to analyze deep field images from HST and JWST to identify and classify early galaxies.",
            "Background": "Galaxy formation in the early universe is a fundamental process that shapes cosmic structure...",
            "Expected Outcomes": "A catalog of early galaxies with improved classification accuracy and insights into formation mechanisms."
        }
    }
    
    return {
        "provider": "google",
        "api_key": "your-api-key-here",
        "temperature": 0.5,
        "proposal_json": json.dumps(proposal)
    }


def example_expert_feedback():
    """Example of how to get expert feedback."""
    # Same proposal as above
    proposal = {
        "title": "Machine Learning Analysis of Early Galaxy Formation",
        "subfields": ["Cosmology", "Galaxy Formation"],
        "skill_level": "undergraduate",
        "time_frame": "1 year",
        "idea": {
            "Research Question": "How can machine learning techniques improve our understanding of galaxy formation processes in the early universe?",
            "Proposed Solution": "Apply convolutional neural networks to analyze deep field images from HST and JWST to identify and classify early galaxies.",
            "Background": "Galaxy formation in the early universe is a fundamental process that shapes cosmic structure...",
            "Expected Outcomes": "A catalog of early galaxies with improved classification accuracy and insights into formation mechanisms."
        }
    }
    
    return {
        "provider": "google",
        "api_key": "your-api-key-here", 
        "temperature": 0.5,
        "proposal_json": json.dumps(proposal)
    }


def example_improve_idea():
    """Example of how to improve an idea with feedback."""
    original_proposal = {
        "title": "Machine Learning Analysis of Early Galaxy Formation",
        "subfields": ["Cosmology", "Galaxy Formation"],
        "idea": {
            "Research Question": "How can machine learning techniques improve our understanding of galaxy formation processes in the early universe?",
            "Proposed Solution": "Apply convolutional neural networks to analyze deep field images from HST and JWST to identify and classify early galaxies.",
            "Background": "Galaxy formation in the early universe is a fundamental process...",
            "Expected Outcomes": "A catalog of early galaxies with improved classification accuracy."
        }
    }
    
    # Example expert feedback (this would come from the expert_feedback tool)
    expert_feedback = {
        "scientific_validity": {
            "strengths": ["Novel application of ML to galaxy formation", "Uses state-of-the-art telescope data"],
            "concerns": ["May need more specific methodology", "Should address data quality issues"]
        },
        "methodology": {
            "strengths": ["CNNs are appropriate for image analysis"],
            "concerns": ["Need to specify training data sources", "Validation strategy unclear"]
        },
        "novelty_assessment": "The approach is novel and could contribute significantly to the field.",
        "impact_assessment": "High potential impact if successful.",
        "feasibility_assessment": "Feasible for an undergraduate with proper guidance.",
        "recommendations": [
            "Specify the exact CNN architecture and training approach",
            "Include a validation strategy using known galaxy samples",
            "Consider data augmentation techniques for limited training data"
        ],
        "summary": "Strong concept with good potential. Needs more methodological detail and validation strategy."
    }
    
    return {
        "provider": "google",
        "api_key": "your-api-key-here",
        "temperature": 0.5,
        "original_proposal_json": json.dumps(original_proposal),
        "reflection_json": json.dumps(expert_feedback),
        # literature_json is optional
    }


def example_full_pipeline():
    """Example of running the full pipeline."""
    return {
        "provider": "google",
        "api_key": "your-api-key-here",
        "temperature": 0.5,
        "user_idea": "I want to use artificial intelligence to discover new types of stars by analyzing spectra from large sky surveys"
    }


def print_examples():
    """Print all example tool calls."""
    print("=== Astronomy Research Assistant MCP Server Examples ===\n")
    
    print("1. Generate Idea:")
    print(json.dumps(example_generate_idea(), indent=2))
    print("\n" + "="*60 + "\n")
    
    print("2. Structure Idea:")
    print(json.dumps(example_structure_idea(), indent=2))
    print("\n" + "="*60 + "\n")
    
    print("3. Literature Review:")
    print(json.dumps(example_literature_review(), indent=2))
    print("\n" + "="*60 + "\n")
    
    print("4. Expert Feedback:")
    print(json.dumps(example_expert_feedback(), indent=2))
    print("\n" + "="*60 + "\n")
    
    print("5. Improve Idea:")
    print(json.dumps(example_improve_idea(), indent=2))
    print("\n" + "="*60 + "\n")
    
    print("6. Full Pipeline:")
    print(json.dumps(example_full_pipeline(), indent=2))
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print_examples()
    
    print("\nTo run the MCP server:")
    print("python mcp_server.py")
    print("\nTo interact with the server, use an MCP client or integrate with tools like:")
    print("- Claude Desktop")
    print("- VS Code with MCP extension") 
    print("- Custom MCP client applications") 