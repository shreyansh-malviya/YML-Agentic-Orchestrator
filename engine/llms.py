"""
LLM Interface Module
Provides response functions for different language models.
"""

from logging import config
import os
from typing import Optional, Dict, Any


def gemini_response(prompt: str, model_config=None) -> str:
    try:
        import google.generativeai as genai
        import os

        # api_key = os.getenv("GEMINI_API_KEY")  # <-- use env var
        api_key = "AIzaSyC5k8ezxQzUjTzIff1T0gFMWglpLw297P4"

        if not api_key:
            return "[Error: GEMINI_API_KEY not found]"

        genai.configure(api_key=api_key)

        model_name = model_config.get("model", "gemini-flash-latest") if model_config else "gemini-2.5-flash"
        temperature = model_config.get("temperature", 0.7) if model_config else 0.7
        max_tokens = model_config.get("max_tokens", 2048) if model_config else 2048

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )

        response = model.generate_content(prompt)
        return response.text

    except ImportError:
        return "[Error: pip install google-generativeai]"
    except Exception as e:
        return f"[Error calling Gemini: {e}]"


def openai_response(prompt: str, model_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get response from OpenAI model.
    
    Args:
        prompt: The input prompt
        model_config: Model configuration dict with temperature, max_tokens, etc.
        
    Returns:
        Response string from OpenAI
    """
    try:
        from openai import OpenAI
        
        # Configure API
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "[Error: OPENAI_API_KEY not found in environment]"
        
        client = OpenAI(api_key=api_key)
        
        # Get model configuration
        model_name = model_config.get('model', 'gpt-4') if model_config else 'gpt-4'
        temperature = model_config.get('temperature', 0.7) if model_config else 0.7
        max_tokens = model_config.get('max_tokens', 4096) if model_config else 4096
        
        # Create completion
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
        
    except ImportError:
        return "[Error: openai package not installed. Run: pip install openai]"
    except Exception as e:
        return f"[Error calling OpenAI: {str(e)}]"


def anthropic_response(prompt: str, model_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get response from Anthropic Claude model.
    
    Args:
        prompt: The input prompt
        model_config: Model configuration dict with temperature, max_tokens, etc.
        
    Returns:
        Response string from Claude
    """
    try:
        from anthropic import Anthropic
        
        # Configure API
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "[Error: ANTHROPIC_API_KEY not found in environment]"
        
        client = Anthropic(api_key=api_key)
        
        # Get model configuration
        model_name = model_config.get('model', 'claude-sonnet-4-0') if model_config else 'claude-sonnet-4-0'
        temperature = model_config.get('temperature', 0.7) if model_config else 0.7
        max_tokens = model_config.get('max_tokens', 64000) if model_config else 64000
        
        # Create message
        message = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text
        
    except ImportError:
        return "[Error: anthropic package not installed. Run: pip install anthropic]"
    except Exception as e:
        return f"[Error calling Anthropic: {str(e)}]"


def mock_response(prompt: str, model_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Mock response for testing without API keys.
    
    Args:
        prompt: The input prompt
        model_config: Model configuration dict
        
    Returns:
        Mock response string
    """
    model_name = model_config.get('model', 'mock-model') if model_config else 'mock-model'
    return f"[Mock response from {model_name}] This is a simulated response to: {prompt[:50]}..."


def get_llm_function(prompt: str, model_name: str):
    """
    Get the appropriate LLM function based on provider.
    
    Args:
        provider: Provider name (google, openai, anthropic, mock)
        
    Returns:
        LLM function
    """
    providers = {
        'gemini-2.5-flash': gemini_response,
        'gemini-2.5-pro': gemini_response,
        'mock': mock_response,
    }
    

    response_function = providers[model_name]
    config = {
        "model": model_name,
        "temperature": 0.7,
        "max_tokens": 2048
    }    
    res = response_function(prompt, config)
    return res




if __name__ == "__main__":
    # Simple test of Gemini response
    test_prompt = "What is the capital of France?"
    response = gemini_response(test_prompt)
    print(f"Prompt: {test_prompt}\nResponse: {response}")


    # import google.generativeai as genai
    # import os

    # # ⚠️ Use env variable if possible
    # # genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    # genai.configure(api_key="AIzaSyC5k8ezxQzUjTzIff1T0gFMWglpLw297P4")

    # print("Listing available models:\n")

    # for model in genai.list_models():
    #     print("MODEL:", model.name)
    #     print("  Supported methods:", model.supported_generation_methods)
    #     print("-" * 50)

