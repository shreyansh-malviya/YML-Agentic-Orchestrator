"""
LLM Interface Module
Provides response functions for different language models.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def gemini_response(prompt: str, model_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get response from Google Gemini model.
    
    Args:
        prompt: The input prompt
        model_config: Model configuration dict with temperature, max_tokens, etc.
        
    Returns:
        Response string from Gemini
    """
    try:
        import google.generativeai as genai
        
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "[Error: GEMINI_API_KEY not found in environment. Set it in .env file]"
        
        genai.configure(api_key=api_key)
        
        # Get model configuration
        model_name = model_config.get("model", "gemini-2.5-flash") if model_config else "gemini-2.5-flash"
        temperature = model_config.get("temperature", 0.7) if model_config else 0.7
        max_tokens = model_config.get("max_tokens", 8096) if model_config else 8096
        
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
        return "[Error: google-generativeai package not installed. Run: pip install google-generativeai]"
    except Exception as e:
        return f"[Error calling Gemini: {str(e)}]"


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
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "[Error: OPENAI_API_KEY not found in environment. Set it in .env file]"
        
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
        
        # Get API key from environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "[Error: ANTHROPIC_API_KEY not found in environment. Set it in .env file]"
        
        client = Anthropic(api_key=api_key)
        
        # Get model configuration
        model_name = model_config.get('model', 'claude-sonnet-4-0') if model_config else 'claude-sonnet-4-0'
        temperature = model_config.get('temperature', 0.7) if model_config else 0.7
        max_tokens = model_config.get('max_tokens', 8096) if model_config else 8096
        
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


def grok_response(prompt: str, model_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get response from xAI Grok model.
    
    Args:
        prompt: The input prompt
        model_config: Model configuration dict with temperature, max_tokens, etc.
        
    Returns:
        Response string from Grok
    """
    try:
        from openai import OpenAI
        
        # Get API key from environment
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            return "[Error: XAI_API_KEY not found in environment. Set it in .env file]"
        
        # Grok uses OpenAI-compatible API
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
        
        # Get model configuration
        model_name = model_config.get('model', 'grok-beta') if model_config else 'grok-beta'
        temperature = model_config.get('temperature', 0.7) if model_config else 0.7
        max_tokens = model_config.get('max_tokens', 8096) if model_config else 8096
        
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
        return f"[Error calling Grok: {str(e)}]"


def groq_response(prompt: str, model_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get response from Groq (fast inference platform).
    
    Args:
        prompt: The input prompt
        model_config: Model configuration dict with temperature, max_tokens, etc.
        
    Returns:
        Response string from Groq
    """
    try:
        from groq import Groq
        
        # Get API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "[Error: GROQ_API_KEY not found in environment. Set it in .env file]"
        
        client = Groq(api_key=api_key)
        
        # Get model configuration
        model_name = model_config.get('model', 'llama-3.3-70b-versatile') if model_config else 'llama-3.3-70b-versatile'
        temperature = model_config.get('temperature', 0.7) if model_config else 0.7
        max_tokens = model_config.get('max_tokens', 8096) if model_config else 8096
        
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
        return "[Error: groq package not installed. Run: pip install groq]"
    except Exception as e:
        return f"[Error calling Groq: {str(e)}]"




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
    return f"[Mock response from {model_name}] This is a simulated response to: {prompt[:100]}..."


def get_llm_response(prompt: str, model_name: str, model_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get LLM response based on model name.
    Routes to appropriate provider based on model name.
    
    Args:
        prompt: The input prompt
        model_name: Name of the model to use
        model_config: Optional model configuration
        
    Returns:
        Response string from the LLM
    """
    # Default config if none provided
    if model_config is None:
        model_config = {
            "model": model_name,
            "temperature": 0.7,
            "max_tokens": 8096
        }
    
    # Route based on model name
    model_lower = model_name.lower()
    
    # Gemini models
    if 'gemini' in model_lower:
        return gemini_response(prompt, model_config)
    
    # OpenAI models
    elif 'gpt' in model_lower or 'openai' in model_lower:
        return openai_response(prompt, model_config)
    
    # Anthropic models
    elif 'claude' in model_lower or 'anthropic' in model_lower:
        return anthropic_response(prompt, model_config)
    
    # xAI Grok models
    elif 'grok' in model_lower or 'xai' in model_lower:
        return grok_response(prompt, model_config)
    
    # Groq models (fast inference)
    elif 'groq' in model_lower or 'llama' in model_lower or 'mixtral' in model_lower:
        return groq_response(prompt, model_config)
    
    # Mock for testing
    elif 'mock' in model_lower:
        return mock_response(prompt, model_config)
    
    # Default fallback to configured default model
    else:
        default_model = os.getenv('DEFAULT_MODEL', 'llama-3.3-70b-versatile')
        default_provider = os.getenv('DEFAULT_PROVIDER', 'groq')
        
        print(f"⚠ Unknown model '{model_name}', falling back to {default_model}")
        
        # Get default configuration from environment variables
        model_config = {
            "model": default_model,
            "temperature": float(os.getenv('DEFAULT_TEMPERATURE', '0.7')),
            "max_tokens": int(os.getenv('DEFAULT_MAX_TOKENS', '8096'))
        }
        
        # Route to appropriate provider based on DEFAULT_PROVIDER
        if default_provider == 'groq' or 'llama' in default_model.lower() or 'mixtral' in default_model.lower():
            return groq_response(prompt, model_config)
        elif default_provider == 'xai' or 'grok' in default_model.lower():
            return grok_response(prompt, model_config)
        elif default_provider == 'google' or 'gemini' in default_model.lower():
            return gemini_response(prompt, model_config)
        elif default_provider == 'openai' or 'gpt' in default_model.lower():
            return openai_response(prompt, model_config)
        elif default_provider == 'anthropic' or 'claude' in default_model.lower():
            return anthropic_response(prompt, model_config)
        else:
            # Final fallback to Groq
            return groq_response(prompt, model_config)


# Keep backward compatibility
def get_llm_function(prompt: str, model_name: str):
    """
    Legacy function for backward compatibility.
    Calls get_llm_response with default config.
    """
    return get_llm_response(prompt, model_name)


if __name__ == "__main__":
    # Test the LLM interface
    test_prompt = "What is 2+2?"
    
    print("Testing LLM Interface...")
    print("=" * 60)
    
    # Test mock (always works)
    print("\n1. Testing Mock Provider:")
    response = get_llm_response(test_prompt, "mock")
    print(response)
    
    # Test Gemini (if API key available)
    print("\n2. Testing Gemini:")
    response = get_llm_response(test_prompt, "gemini-2.5-flash")
    print(response[:200] if len(response) > 200 else response)
    
    print("\n" + "=" * 60)
    print("Test complete!")
    