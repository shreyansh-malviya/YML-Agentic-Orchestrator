"""
Agent Workflow Execution System
Autonomous agent execution with YAML configuration
"""

from pathlib import Path
# from .YAMLParser import YAMLParser
# from .llms import gemini_response, get_llm_function
from YAMLParser import YAMLParser
from llms import gemini_response, get_llm_function
from memory.rag import store_memory, retrieve_memory, get_context

available_models = ["gemini-2.5-flash", "gemini-2.5-pro"]

# Configuration
input_file = "D:\\D\\Projects\\YML Parser + Agentic Workflow\\engine\\test\\test2.yml"  # User will provide this


def load_yaml_data(file_path):
    """Load and parse YAML configuration file"""
    parser = YAMLParser(file_path)
    data = parser.parse()
    return data


def save_to_context(role, response):
    """Save conversation to raw.txt in context folder AND to RAG memory"""
    # Save to text file (backup/logging)
    context_file = Path(__file__).parent / "context" / "raw.txt"
    context_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(context_file, "a", encoding="utf-8") as f:
        f.write(f"{role}: {response}\n\n")
    
    # Store in RAG memory for intelligent retrieval
    store_memory(response, role=role)


def execute_sequential_workflow(yaml_data):
    """Execute sequential workflow with RAG context"""
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
        
        # Retrieve relevant context from previous agents (only for 2nd agent onwards)
        if step_idx > 0:
            relevant_context = get_context(base_prompt, top_k=3)
            if relevant_context:
                prompt = f"{base_prompt}\n\nRelevant previous context:\n{relevant_context}"
                print(f"\n🧠 Retrieved {len(relevant_context.split('[Memory'))-1} relevant memories")
            else:
                prompt = base_prompt
        else:
            prompt = base_prompt
        
        print(f"\n{'='*70}")
        print(f"Agent: {role}")
        print(f"Role: {role}")
        print(f"Goal: {goal}")
        print(f"{'='*70}")
        print(f"\n📝 Base Prompt: {base_prompt}")
        
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
    """Execute parallel workflow with RAG context"""
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
        
        base_prompt = f"you are {role} and your motive is {goal} {description} {instructions}"
        
        # Retrieve relevant context (branches can use context from previous workflows)
        relevant_context = get_context(base_prompt, top_k=2)
        if relevant_context:
            prompt = f"{base_prompt}\n\nRelevant context:\n{relevant_context}"
            print(f"\n🧠 Retrieved {len(relevant_context.split('[Memory'))-1} relevant memories")
        else:
            prompt = base_prompt
        
        print(f"\n{'='*70}")
        print(f"Branch Agent: {branch_name}")
        print(f"Role: {role}")
        print(f"Goal: {goal}")
        print(f"{'='*70}")
        print(f"\n📝 Base Prompt: {base_prompt}")
        
        # Get model configuration
        model_name = agent_data.get("model")        
        # If no model config, use Gemini

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
            response = gemini_response(prompt, config=None)
        else:
            # Get LLM function based on provider
            # provider = model_config.get("provider", "google")
            print(f"🔧 Using google provider with model ${model_name}")
            response = get_llm_function(prompt, model_name)
            # response = llm_function(prompt, model_config)
        
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
            
            base_prompt = f"you are {role} and your motive is {goal} {description} {instructions}"
            
            # Get relevant context from RAG instead of all branch responses
            relevant_context = get_context(base_prompt, top_k=5)
            
            if relevant_context:
                prompt = f"{base_prompt}\n\nRelevant context from previous agents:\n{relevant_context}"
                print(f"\n🧠 Retrieved {len(relevant_context.split('[Memory'))-1} relevant memories for consolidation")
            else:
                prompt = base_prompt
            
            print(f"\n📝 Base Prompt: {base_prompt}")
            
            # Get model configuration
            model_name = agent_data.get("model")
            
            model_available = model_name in available_models    
            
            # If no model config, use Gemini
            save_to_context("User", prompt)
            if not model_available:                # config = {
                #     "model": "gemini-1.5-flash",
                #     "temperature": 0.7,
                #     "max_tokens": 2048
                # }
                # response = gemini_response(prompt, config)
                response = gemini_response(prompt, config=None)
            else:
                # provider = model_config.get("provider", "google")
                print(f"🔧 Using google provider with model ${model_name}")
                response = get_llm_function(prompt, model_name)
                # response = llm_function(prompt, model_config)
            
            print(f"\n✅ {role} Final Response:")
            print(response)
            print(f"\n{'='*70}")
            
            save_to_context(role, response)


def run_agent(yaml_file):
    """Main function to run agent workflow"""
    # Load YAML data
    print(f"Loading configuration from: {yaml_file}")
    yaml_data = load_yaml_data(yaml_file)
    
    print(f"\n✓ Configuration loaded successfully")
    print(f"  Agents: {len(yaml_data['agents'])}")
    print(f"  Workflow Type: {yaml_data['workflow']['type']}")
    
    # Get user prompt interactively
    print("\n" + "="*70) 
    # autonomously"""
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
    print("💾")


if __name__ == "__main__":
    run_agent(input_file)
    print("  Conversation saved to context/raw.txt")

