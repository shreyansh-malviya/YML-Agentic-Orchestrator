"""
Complete Example: Using Gemini with Agent Workflow
"""

from engine.llms import gemini_response

# Example 1: Simple Gemini call
print("\n" + "="*70)
print("EXAMPLE 1: Simple Gemini Request")
print("="*70)

prompt = "What are the main benefits of renewable energy?"
config = {
    'model': 'gemini-1.5-flash',
    'temperature': 0.7,
    'max_tokens': 500
}

response = gemini_response(prompt, config)
print(f"\nPrompt: {prompt}")
print(f"\nResponse:\n{response}")

# Example 2: Using different models
print("\n" + "="*70)
print("EXAMPLE 2: Different Model Configurations")
print("="*70)

# Higher creativity (higher temperature)
creative_config = {
    'model': 'gemini-1.5-flash',
    'temperature': 0.9,
    'max_tokens': 300
}

# More focused (lower temperature)
focused_config = {
    'model': 'gemini-1.5-flash',
    'temperature': 0.2,
    'max_tokens': 300
}

prompt = "Write a tagline for a tech startup"

print("\n--- Creative Response (temp=0.9) ---")
response1 = gemini_response(prompt, creative_config)
print(f"Response: {response1}")

print("\n--- Focused Response (temp=0.2) ---")
response2 = gemini_response(prompt, focused_config)
print(f"Response: {response2}")

# Example 3: Role-based prompt (like Agent class does)
print("\n" + "="*70)
print("EXAMPLE 3: Role-Based Prompt")
print("="*70)

role = "Software Architect"
goal = "design scalable systems"
description = "Expert in cloud architecture and microservices"
instructions = """
- Focus on scalability and performance
- Consider security best practices
- Provide concrete recommendations
"""

agent_prompt = f"""You are a {role} and your goal is {goal}.

Description: {description}

Instructions:
{instructions}

Task: Design a microservices architecture for an e-commerce platform.

Please proceed with your task based on your role and goal."""

config = {
    'model': 'gemini-1.5-flash',
    'temperature': 0.7,
    'max_tokens': 1000
}

response = gemini_response(agent_prompt, config)
print(f"\nAgent Response:\n{response}")

print("\n" + "="*70)
print("Examples Complete!")
print("="*70)
print("\nNote: Set GEMINI_API_KEY in .env to use real Gemini API")
print("Without API key, you'll see error messages")
