"""
Simple Agent Usage Example
"""

from engine.Agent import Agent


# Example 1: Simple usage
print("="*70)
print("SIMPLE AGENT USAGE")
print("="*70)

# Create an agent from YAML config
agent = Agent("engine/test/test1.yml")

# Run with a user prompt
responses = agent.run(
    "What are the main advantages of electric vehicles?",
    clear_context=True
)

# Get the final response
final_response = agent.get_final_response()
print(f"\nFinal Response:\n{final_response}")

# Show conversation history
agent.show_context()
