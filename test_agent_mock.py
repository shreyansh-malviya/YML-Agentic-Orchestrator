"""
Test Agent with Mock Responses (No API Keys Required)
"""

from engine.Agent import Agent


print("="*70)
print("AGENT TEST WITH MOCK RESPONSES")
print("="*70)

# Create an agent from YAML config
agent = Agent("engine/test/test4.yml")

# Run with a user prompt
print("\nRunning workflow...")
responses = agent.run(
    "Explain the benefits of using AI in software development",
    clear_context=True
)

# Show all responses
print("\n" + "="*70)
print("ALL AGENT RESPONSES")
print("="*70)

for i, resp in enumerate(responses, 1):
    print(f"\n{i}. Agent: {resp['agent_id']}")
    print(f"   Response Preview: {resp['response'][:150]}...")

# Show full context
print("\n")
agent.show_context()
