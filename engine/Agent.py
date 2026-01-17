"""
Agent Workflow Execution System
Autonomous agent execution with YAML configuration
"""

import json
from pathlib import Path
from datetime import datetime
# from .YAMLParser import YAMLParser
# from .llms import gemini_response, get_llm_function
from YAMLParser import YAMLParser
from llms import gemini_response, get_llm_function

available_models = ["gemini-2.5-flash", "gemini-2.5-pro"]

# Configuration
input_file = "D:\\D\\Projects\\YML Parser + Agentic Workflow\\engine\\test\\test1.yml"  # User will provide this


def load_yaml_data(file_path):
    """Load and parse YAML configuration file"""
    parser = YAMLParser(file_path)
    data = parser.parse()
    return data


def clear_context():
    """Clear/reset the context file for a fresh start"""
    context_file = Path(__file__).parent / "context" / "raw.json"
    context_file.parent.mkdir(parents=True, exist_ok=True)
    
    initial_data = {
        "workflow_start": datetime.now().isoformat(),
        "conversations": []
    }
    
    with open(context_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    print("🗑️  Context file cleared for fresh start")


def save_to_context(role, response):
    """Save conversation to raw.json in context folder"""
    context_file = Path(__file__).parent / "context" / "raw.json"
    context_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing data
    if context_file.exists():
        with open(context_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"workflow_start": datetime.now().isoformat(), "conversations": []}
    
    # Append new conversation
    data["conversations"].append({
        "timestamp": datetime.now().isoformat(),
        "role": role,
        "response": response
    })
    
    # Write back to file
    with open(context_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def read_context():
    """Read all previous conversations from context file"""
    context_file = Path(__file__).parent / "context" / "raw.json"
    
    if not context_file.exists():
        return ""
    
    try:
        with open(context_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        conversations = data.get("conversations", [])
        if not conversations:
            return ""
        
        # Format conversations as context string
        context_parts = []
        for conv in conversations:
            role = conv.get("role", "Unknown")
            response = conv.get("response", "")
            context_parts.append(f"{role}: {response}")
        
        return "\n\n".join(context_parts)
    except Exception as e:
        print(f"⚠ Error reading context: {e}")
        return ""


def execute_sequential_workflow(yaml_data):
    """Execute sequential workflow"""
    print(f"hereee: {yaml_data}")
    print("\n" + "="*70)
    print("EXECUTING SEQUENTIAL WORKFLOW")
    print("="*70)
    
    steps = yaml_data["workflow"]["steps"]
    
    for step_idx, role in enumerate(steps):
        print("we got a role to process:", role)
        # Find agent by ID
        agent_data = None
        for agent in yaml_data["agents"]:
            print("searching for role in agent:", agent["id"])
            if agent["id"] == role:
                agent_data = agent
                break
        
        print("Agent Data:", agent_data)
        if not agent_data:
            # Agent not found, use Gemini as fallback
            print(f"\n⚠ Agent '{role}' not found, skipping...")
            continue
        
        # Build prompt from agent data
        role = agent_data.get("role", "Agent")
        goal = agent_data.get("goal", "")
        description = agent_data.get("description", "")
        instructions = agent_data.get("instruction", "")
        
        base_prompt = f"you are {role} and your motive is {goal} {description} {instructions}"
        
        # For agents after the first one, add context from previous agents
        if step_idx > 0:
            previous_context = read_context()
            if previous_context:
                prompt = f"{base_prompt}\n\nPrevious Context:\n{previous_context}"
                print(f"\n📚 Including context from {step_idx} previous agent(s)")
            else:
                prompt = base_prompt
        else:
            prompt = base_prompt
            print("\n🆕 First agent - no previous context")
        
        print(f"\n{'='*70}")
        print(f"Agent: {role}")
        print(f"Role: {role}")
        print(f"Goal: {goal}")
        print(f"{'='*70}")
        print(f"\n📝 Prompt: {prompt}")
        
        # Get model configuration
        model_name = agent_data.get("model")
        print(agent_data)
        print(model_name)
        model_available = model_name in available_models    
        
        # If no model config, use Gemini
        save_to_context("User", prompt)
        if not model_available:
            print(f"⚠ Model '{model_name}' not configured, using Gemini...")
            # config = {
            #     "model": "gemini-1.5-flash",
            #     "temperature": 0.7,
            #     "max_tokens": 2048
            # }
            # response = gemini_response(prompt, config)
            response = gemini_response(prompt)
        else:
            # Get LLM function based on provider
            print(f"🔧 Using google provider with model {model_name}")
            response = get_llm_function(prompt, model_name)
        
        # Display response
        print(f"\n✅ {role} Response:")
        print(response)
        print(f"\n{'='*70}")
        
        # Save to context
        save_to_context(role, response)


def execute_parallel_workflow(yaml_data):
    """Execute parallel workflow"""
    print("\n" + "="*70)
    print("EXECUTING PARALLEL WORKFLOW")
    print("="*70)
    
    branches = yaml_data["workflow"]["branches"]
    then_agent = yaml_data["workflow"].get("then")
    
    branch_responses = []
    
    # Execute all branches
    for branch_name in branches:
        # Find agent by ID
        agent_data = None
        for agent in yaml_data["agents"]:
            if agent["id"] == branch_name:
                agent_data = agent
                break
        
        if not agent_data:
            # Agent not found, skip
            print(f"\n⚠ Agent '{branch_name}' not found, skipping...")
            continue
        
        # Build prompt from agent data
        role = agent_data.get("role", "Agent")
        goal = agent_data.get("goal", "")
        description = agent_data.get("description", "")
        instructions = agent_data.get("instruction", "")
        
        prompt = f"you are {role} and your motive is {goal} {description} {instructions}"
        
        print(f"\n{'='*70}")
        print(f"Branch Agent: {branch_name}")
        print(f"Role: {role}")
        print(f"Goal: {goal}")
        print(f"{'='*70}")
        print(f"\n📝 Prompt: {prompt}")
        
        # Get model configuration
        model_name = agent_data.get("model")
        model_available = model_name in available_models
        
        # If no model config, use Gemini
        save_to_context("User", prompt)
        if not model_available:
            print(f"⚠ Model '{model_name}' not configured, using Gemini...")
            response = gemini_response(prompt)
        else:
            # Get LLM function based on provider
            print(f"🔧 Using google provider with model {model_name}")
            response = get_llm_function(prompt, model_name)
        
        # Display response
        print(f"\n✅ {role} Response:")
        print(response)
        print(f"\n{'='*70}")
        
        # Save to context
        save_to_context(role, response)
        branch_responses.append(response)
    
    # Execute 'then' agent if specified
    if then_agent:
        print(f"\n{'='*70}")
        print(f"Executing consolidation agent: {then_agent}")
        print(f"{'='*70}")
        
        # Find then agent
        agent_data = None
        for agent in yaml_data["agents"]:
            if agent["id"] == then_agent:
                agent_data = agent
                break
        
        if agent_data:
            role = agent_data.get("role", "Agent")
            goal = agent_data.get("goal", "")
            description = agent_data.get("description", "")
            instructions = agent_data.get("instruction", "")
            
            # Include all branch responses in prompt
            context = "\n".join([f"Previous response {i+1}: {resp}" for i, resp in enumerate(branch_responses)])
            prompt = f"you are {role} and your motive is {goal} {description} {instructions}\n\nPrevious context:\n{context}"
            
            print(f"\n📝 Prompt: {prompt}")
            
            # Get model configuration
            model_name = agent_data.get("model")
            model_available = model_name in available_models
            
            # If no model config, use Gemini
            save_to_context("User", prompt)
            if not model_available:
                print(f"⚠ Model '{model_name}' not configured, using Gemini...")
                response = gemini_response(prompt)
            else:
                print(f"🔧 Using google provider with model {model_name}")
                response = get_llm_function(prompt, model_name)
            
            print(f"\n✅ {role} Final Response:")
            print(response)
            print(f"\n{'='*70}")
            
            save_to_context(role, response)


def run_agent(yaml_file):
    """Main function to run agent workflow autonomously"""
    # Clear context for fresh start
    clear_context()
    
    # Load YAML data
    print(f"🔄 Loading configuration from: {yaml_file}")
    yaml_data = load_yaml_data(yaml_file)
    
    print(f"\n✓ Configuration loaded successfully")
    print(f"  📋 Agents: {len(yaml_data['agents'])}")
    print(f"  🔀 Workflow Type: {yaml_data['workflow']['type']}")
    
    # Check workflow type and execute accordingly
    workflow_type = yaml_data["workflow"]["type"]
    
    if workflow_type == "sequential":
        execute_sequential_workflow(yaml_data)
    elif workflow_type == "parallel":
        execute_parallel_workflow(yaml_data)
    else:
        print(f"✗ Unknown workflow type: {workflow_type}")
        return
    
    print("\n" + "="*70)
    print("✅ Workflow execution completed!")
    print("💾 Conversation saved to context/raw.json")
    print("="*70)


if __name__ == "__main__":
    run_agent(input_file)

