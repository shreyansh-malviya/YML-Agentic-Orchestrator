"""
Agent Workflow Execution System
Autonomous agent execution with YAML configuration
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from YAMLParser import YAMLParser
from llms import gemini_response, get_llm_function
from memory import store_context, retrieve_context, clear_memory, get_memory_stats

available_models = ["gemini-2.5-flash", "gemini-2.5-pro"]

# Global logger instance
logger = None


def setup_logging():
    """Setup logging to both file and console with timestamps"""
    global logger
    
    # Create logs directory
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"workflow_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger("AgentWorkflow")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicate logs
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler - logs everything
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler - logs INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)
    logger.addHandler(console_handler)
    
    logger.info("=" * 80)
    logger.info(f"Logging initialized - Log file: {log_file}")
    logger.info("=" * 80)
    
    return log_file


def load_yaml_data(file_path):
    """Load and parse YAML configuration file"""
    logger.info(f"Loading YAML configuration from: {file_path}")
    start_time = datetime.now()
    
    try:
        parser = YAMLParser(file_path)
        data = parser.parse()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"YAML loaded successfully in {elapsed:.2f}s")
        logger.debug(f"Configuration contains {len(data.get('agents', []))} agents")
        logger.debug(f"Workflow type: {data.get('workflow', {}).get('type', 'unknown')}")
        
        return data
    except Exception as e:
        logger.error(f"Failed to load YAML file: {e}")
        raise


def clear_context():
    """Clear/reset the context file for a fresh start"""
    logger.info("Clearing context for fresh workflow start")
    start_time = datetime.now()
    
    # Clear JSON backup file
    context_file = Path(__file__).parent / "context" / "raw.json"
    context_file.parent.mkdir(parents=True, exist_ok=True)
    
    initial_data = {
        "workflow_start": datetime.now().isoformat(),
        "conversations": []
    }
    
    with open(context_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    logger.debug(f"JSON context file reset: {context_file}")
    
    # Clear RAG memory
    clear_memory()
    logger.debug("RAG memory cleared")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Context cleared successfully in {elapsed:.3f}s")


def save_to_context(role, response):
    """Save conversation to raw.json (backup) and RAG memory (smart retrieval)"""
    logger.debug(f"Saving context for role: {role} (length: {len(response)} chars)")
    start_time = datetime.now()
    
    # Save to JSON backup file
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
    
    logger.debug(f"Saved to JSON backup: {context_file}")
    
    # Store in RAG memory for intelligent retrieval
    store_context(role, response)
    logger.debug("Saved to RAG memory")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.debug(f"Context saved in {elapsed:.3f}s")


def read_context_for_agent(agent_prompt: str, max_memories: int = 5):
    """
    Retrieve only relevant context using RAG
    
    Args:
        agent_prompt: Current agent's prompt (used for semantic search)
        max_memories: Maximum number of relevant memories to retrieve
    
    Returns:
        Formatted context string with only relevant previous conversations
    """
    logger.debug(f"Retrieving relevant context (max: {max_memories} memories)")
    start_time = datetime.now()
    
    # Use RAG to retrieve only relevant context
    relevant_context = retrieve_context(agent_prompt, k=max_memories)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    context_length = len(relevant_context) if relevant_context else 0
    logger.debug(f"Retrieved {context_length} chars of relevant context in {elapsed:.3f}s")
    
    return relevant_context


def execute_sequential_workflow(yaml_data):
    """Execute sequential workflow"""
    logger.info("="*80)
    logger.info("EXECUTING SEQUENTIAL WORKFLOW")
    logger.info("="*80)
    
    steps = yaml_data["workflow"]["steps"]
    logger.info(f"Total steps in workflow: {len(steps)}")
    logger.debug(f"Step sequence: {' -> '.join(steps)}")
    
    for step_idx, role in enumerate(steps):
        logger.info(f"\n{'='*80}")
        logger.info(f"STEP {step_idx + 1}/{len(steps)}: Processing agent '{role}'")
        logger.info(f"{'='*80}")
        
        # Find agent by ID
        agent_data = None
        for agent in yaml_data["agents"]:
            logger.debug(f"Searching for role in agent: {agent['id']}")
            if agent["id"] == role:
                agent_data = agent
                break
        
        logger.debug(f"Agent Data: {agent_data}")
        if not agent_data:
            # Agent not found, use Gemini as fallback
            logger.warning(f"Agent '{role}' not found in configuration, skipping step")
            continue
        
        # Build prompt from agent data
        role = agent_data.get("role", "Agent")
        goal = agent_data.get("goal", "")
        description = agent_data.get("description", "")
        instructions = agent_data.get("instruction", "")
        
        logger.info(f"Agent Role: {role}")
        logger.info(f"Agent Goal: {goal}")
        logger.debug(f"Agent Description: {description}")
        logger.debug(f"Agent Instructions: {instructions}")
        
        base_prompt = f"you are {role} and your motive is {goal} {description} {instructions}"
        
        # For agents after the first one, retrieve ONLY RELEVANT context using RAG
        if step_idx > 0:
            logger.info("Retrieving relevant context from previous steps (RAG)")
            # Retrieve top 3-5 most relevant previous conversations
            relevant_context = read_context_for_agent(base_prompt, max_memories=5)
            if relevant_context:
                prompt = f"{base_prompt}\n\nRelevant Previous Context:\n{relevant_context}"
                logger.info(f"Including relevant context (max 5 memories)")
            else:
                prompt = base_prompt
                logger.info("No relevant context found")
        else:
            prompt = base_prompt
            logger.info("First agent - no previous context needed")
        
        logger.debug(f"Final Prompt Length: {len(prompt)} characters")
        logger.debug(f"Full Prompt: {prompt[:200]}..." if len(prompt) > 200 else f"Full Prompt: {prompt}")
        
        # Get model configuration
        model_name = agent_data.get("model")
        logger.info(f"Model specified: {model_name}")
        model_available = model_name in available_models
        
        # Save user prompt to context
        save_to_context("User", base_prompt)
        
        # Make LLM request
        request_start = datetime.now()
        logger.info(f"Sending request to LLM at {request_start.strftime('%H:%M:%S.%f')[:-3]}")
        
        if not model_available:
            logger.warning(f"Model '{model_name}' not in available models, using Gemini fallback")
            logger.info("Request Type: Gemini API (default)")
            response = gemini_response(prompt)
        else:
            logger.info(f"Request Type: Google provider with model {model_name}")
            response = get_llm_function(prompt, model_name)
        
        response_end = datetime.now()
        elapsed = (response_end - request_start).total_seconds()
        logger.info(f"Received response at {response_end.strftime('%H:%M:%S.%f')[:-3]} (took {elapsed:.2f}s)")
        logger.info(f"Response length: {len(response)} characters")
        
        # Display response
        logger.info(f"\n{role} Response:")
        logger.info("-" * 80)
        logger.info(response)
        logger.info("-" * 80)
        
        # Save to context
        save_to_context(role, response)


def execute_parallel_workflow(yaml_data):
    """Execute parallel workflow"""
    logger.info("="*80)
    logger.info("EXECUTING PARALLEL WORKFLOW")
    logger.info("="*80)
    
    branches = yaml_data["workflow"]["branches"]
    then_agent = yaml_data["workflow"].get("then")
    
    logger.info(f"Total parallel branches: {len(branches)}")
    logger.debug(f"Branches: {', '.join(branches)}")
    if then_agent:
        logger.info(f"Consolidation agent: {then_agent}")
    
    branch_responses = []
    
    # Execute all branches
    for branch_idx, branch_name in enumerate(branches):
        logger.info(f"\n{'='*80}")
        logger.info(f"BRANCH {branch_idx + 1}/{len(branches)}: Processing agent '{branch_name}'")
        logger.info(f"{'='*80}")
        
        # Find agent by ID
        agent_data = None
        for agent in yaml_data["agents"]:
            if agent["id"] == branch_name:
                agent_data = agent
                break
        
        if not agent_data:
            # Agent not found, skip
            logger.warning(f"Agent '{branch_name}' not found in configuration, skipping branch")
            continue
        
        # Build prompt from agent data
        role = agent_data.get("role", "Agent")
        goal = agent_data.get("goal", "")
        description = agent_data.get("description", "")
        instructions = agent_data.get("instruction", "")
        
        logger.info(f"Branch Agent Role: {role}")
        logger.info(f"Branch Agent Goal: {goal}")
        logger.debug(f"Branch Agent Description: {description}")
        
        prompt = f"you are {role} and your motive is {goal} {description} {instructions}"
        logger.debug(f"Prompt Length: {len(prompt)} characters")
        
        # Get model configuration
        model_name = agent_data.get("model")
        logger.info(f"Model specified: {model_name}")
        model_available = model_name in available_models
        
        # Save user prompt
        save_to_context("User", prompt)
        
        # Make LLM request
        request_start = datetime.now()
        logger.info(f"Sending request to LLM at {request_start.strftime('%H:%M:%S.%f')[:-3]}")
        
        if not model_available:
            logger.warning(f"Model '{model_name}' not configured, using Gemini fallback")
            logger.info("Request Type: Gemini API (default)")
            response = gemini_response(prompt)
        else:
            logger.info(f"Request Type: Google provider with model {model_name}")
            response = get_llm_function(prompt, model_name)
        
        response_end = datetime.now()
        elapsed = (response_end - request_start).total_seconds()
        logger.info(f"Received response at {response_end.strftime('%H:%M:%S.%f')[:-3]} (took {elapsed:.2f}s)")
        logger.info(f"Response length: {len(response)} characters")
        
        # Display response
        logger.info(f"\n{role} Response:")
        logger.info("-" * 80)
        logger.info(response)
        logger.info("-" * 80)
        
        # Save to context
        save_to_context(role, response)
        branch_responses.append(response)
    
    # Execute 'then' agent if specified
    if then_agent:
        logger.info(f"\n{'='*80}")
        logger.info(f"CONSOLIDATION PHASE: Executing agent '{then_agent}'")
        logger.info(f"{'='*80}")
        
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
            
            logger.info(f"Consolidation Agent Role: {role}")
            logger.info(f"Consolidation Agent Goal: {goal}")
            logger.info(f"Including {len(branch_responses)} branch responses in context")
            
            # Include all branch responses in prompt
            context = "\n".join([f"Previous response {i+1}: {resp}" for i, resp in enumerate(branch_responses)])
            prompt = f"you are {role} and your motive is {goal} {description} {instructions}\n\nPrevious context:\n{context}"
            
            logger.debug(f"Consolidation Prompt Length: {len(prompt)} characters")
            
            # Get model configuration
            model_name = agent_data.get("model")
            logger.info(f"Model specified: {model_name}")
            model_available = model_name in available_models
            
            # Save user prompt
            save_to_context("User", prompt)
            
            # Make LLM request
            request_start = datetime.now()
            logger.info(f"Sending consolidation request at {request_start.strftime('%H:%M:%S.%f')[:-3]}")
            
            if not model_available:
                logger.warning(f"Model '{model_name}' not configured, using Gemini fallback")
                logger.info("Request Type: Gemini API (default)")
                response = gemini_response(prompt)
            else:
                logger.info(f"Request Type: Google provider with model {model_name}")
                response = get_llm_function(prompt, model_name)
            
            response_end = datetime.now()
            elapsed = (response_end - request_start).total_seconds()
            logger.info(f"Received consolidation response at {response_end.strftime('%H:%M:%S.%f')[:-3]} (took {elapsed:.2f}s)")
            logger.info(f"Response length: {len(response)} characters")
            
            logger.info(f"\n{role} Final Consolidation Response:")
            logger.info("-" * 80)
            logger.info(response)
            logger.info("-" * 80)
            
            save_to_context(role, response)


def run_agent(yaml_file):
    """Main function to run agent workflow autonomously"""
    # Setup logging first
    log_file = setup_logging()
    
    workflow_start = datetime.now()
    logger.info("="*80)
    logger.info("WORKFLOW EXECUTION STARTED")
    logger.info(f"Start Time: {workflow_start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"YAML File: {yaml_file}")
    logger.info("="*80)
    
    try:
        # Clear context for fresh start
        clear_context()
        
        # Load YAML data
        yaml_data = load_yaml_data(yaml_file)
        
        logger.info("Configuration Summary:")
        logger.info(f"  - Total Agents: {len(yaml_data['agents'])}")
        logger.info(f"  - Workflow Type: {yaml_data['workflow']['type']}")
        
        # Check workflow type and execute accordingly
        workflow_type = yaml_data["workflow"]["type"]
        
        if workflow_type == "sequential":
            execute_sequential_workflow(yaml_data)
        elif workflow_type == "parallel":
            execute_parallel_workflow(yaml_data)
        else:
            logger.error(f"Unknown workflow type: {workflow_type}")
            return
        
        # Workflow completed
        workflow_end = datetime.now()
        total_duration = (workflow_end - workflow_start).total_seconds()
        
        logger.info("="*80)
        logger.info("WORKFLOW EXECUTION COMPLETED SUCCESSFULLY")
        logger.info(f"End Time: {workflow_end.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total Duration: {total_duration:.2f} seconds")
        logger.info(f"Context saved to: engine/context/raw.json")
        
        # Show memory stats
        stats = get_memory_stats()
        logger.info(f"Total memories in RAG: {stats['total_memories']}")
        logger.info(f"Log file: {log_file}")
        logger.info("="*80)
        
    except Exception as e:
        workflow_end = datetime.now()
        total_duration = (workflow_end - workflow_start).total_seconds()
        
        logger.error("="*80)
        logger.error("WORKFLOW EXECUTION FAILED")
        logger.error(f"Error: {e}")
        logger.error(f"Failed after: {total_duration:.2f} seconds")
        logger.error("="*80)
        
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        
        raise


if __name__ == "__main__":
    
    # Testing 
    # Configuration
    # input_file = "D:\\D\\Projects\\YML Parser + Agentic Workflow\\engine\\test\\test1.yml"  # User will provide this
    input_file = "D:\\D\\Projects\\YML Parser + Agentic Workflow\\engine\\examples\\config_sequential.yml"  # User will provide this
    run_agent(input_file)
