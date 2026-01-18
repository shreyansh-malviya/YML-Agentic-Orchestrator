"""
Agent Workflow Execution System
Autonomous agent execution with YAML configuration
"""

import json
import logging
import asyncio
import threading
import re
from pathlib import Path
from datetime import datetime
import concurrent.futures
from .YAMLParser import YAMLParser
from .llms import get_llm_response
from .memory import store_context, retrieve_context, clear_memory, get_memory_stats
from .mcp_manager import MCPManager

# Global logger instance
logger = None

# Global MCP manager instance
mcp_manager = None

# Global lock for thread-safe file operations (prevents race conditions in parallel workflows)
context_lock = threading.Lock()


def setup_logging():
    """Setup logging to both file and console with timestamps"""
    global logger
    
    # Create logs directory relative to this file
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
    
    # Clear JSON backup file (thread-safe)
    with context_lock:
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
    
    # Save to JSON backup file (thread-safe for parallel workflows)
    with context_lock:
        context_file = Path(__file__).parent / "context" / "raw.json"
        context_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing data
        if context_file.exists():
            try:
                with open(context_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                # If file is corrupted, reinitialize
                logger.warning("Context file corrupted, reinitializing...")
                data = {"workflow_start": datetime.now().isoformat(), "conversations": []}
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


async def parse_and_execute_tool_calls(response: str, mcp_tools: list) -> str:
    """
    Parse tool calls from LLM response and execute them.
    Looks for [TOOL_CALLS]...[/TOOL_CALLS] blocks in the response.
    
    Args:
        response: LLM response text
        mcp_tools: List of available MCP tool categories
        
    Returns:
        Updated response with tool execution results
    """
    global mcp_manager
    
    if not mcp_manager or not mcp_tools:
        return response
    
    # Find tool call blocks
    tool_block_pattern = r'\[TOOL_CALLS\](.*?)\[/TOOL_CALLS\]'
    matches = re.findall(tool_block_pattern, response, re.DOTALL)
    
    if not matches:
        return response
    
    logger.info(f"Found {len(matches)} tool call block(s)")
    
    # Parse and execute each tool call
    tool_results = []
    for block in matches:
        import ast
        
        # Find all function calls by looking for the pattern category.function(
        func_starts = []
        for match in re.finditer(r'(\w+)\.(\w+)\s*\(', block):
            func_starts.append({
                'start': match.start(),
                'category': match.group(1),
                'function': match.group(2),
                'args_start': match.end()
            })
        
        for idx, func_info in enumerate(func_starts):
            category = func_info['category']
            function_name = func_info['function']
            
            if category not in mcp_tools:
                continue
            
            try:
                # Find the matching closing parenthesis
                args_start = func_info['args_start']
                
                # Determine where args end (either at next function call or end of block)
                if idx + 1 < len(func_starts):
                    search_end = func_starts[idx + 1]['start']
                else:
                    search_end = len(block)
                
                # Extract substring and find matching parenthesis
                substring = block[args_start:search_end]
                
                # Count parentheses to find the matching close
                paren_depth = 1
                in_string = False
                string_char = None
                triple_quote = False
                escape_next = False
                args_end = None
                
                i = 0
                while i < len(substring):
                    char = substring[i]
                    
                    if escape_next:
                        escape_next = False
                        i += 1
                        continue
                    
                    if char == '\\' and in_string:
                        escape_next = True
                        i += 1
                        continue
                    
                    # Check for triple quotes
                    if i + 2 < len(substring) and substring[i:i+3] in ('"""', "'''"):
                        if not in_string:
                            in_string = True
                            triple_quote = True
                            string_char = substring[i:i+3]
                            i += 3
                            continue
                        elif triple_quote and substring[i:i+3] == string_char:
                            in_string = False
                            triple_quote = False
                            string_char = None
                            i += 3
                            continue
                    
                    # Check for single/double quotes
                    if char in ('"', "'") and not triple_quote:
                        if not in_string:
                            in_string = True
                            string_char = char
                        elif char == string_char:
                            in_string = False
                            string_char = None
                    
                    # Count parentheses only when not in string
                    if not in_string:
                        if char == '(':
                            paren_depth += 1
                        elif char == ')':
                            paren_depth -= 1
                            if paren_depth == 0:
                                args_end = i
                                break
                    
                    i += 1
                
                if args_end is None:
                    logger.warning(f"Could not find matching parenthesis for {function_name}")
                    continue
                
                args_str = substring[:args_end].strip()
                
                logger.debug(f"Extracted args for {function_name}: {args_str[:200]}...")
                
                # Parse arguments 
                # For create_file with triple-quoted strings containing docstrings, 
                # ast.literal_eval fails, so we need special handling
                try:
                    if function_name in ['create_file', 'write_file'] and '"""' in args_str:
                        # Manually parse: first arg is filename, rest is content
                        # Find the first comma that's not inside quotes
                        first_comma = -1
                        in_str = False
                        str_char = None
                        for idx, ch in enumerate(args_str):
                            if ch in ('"', "'") and (idx == 0 or args_str[idx-1] != '\\'):
                                if not in_str:
                                    in_str = True
                                    str_char = ch
                                elif ch == str_char:
                                    in_str = False
                            elif ch == ',' and not in_str:
                                first_comma = idx
                                break
                        
                        if first_comma > 0:
                            filepath_part = args_str[:first_comma].strip().strip('"').strip("'")
                            content_part = args_str[first_comma+1:].strip()
                            # Remove triple quotes from content
                            if content_part.startswith('"""') and content_part.endswith('"""'):
                                content_part = content_part[3:-3]
                            elif content_part.startswith("'''") and content_part.endswith("'''"):
                                content_part = content_part[3:-3]
                            args = {"filepath": filepath_part, "content": content_part}
                            parsed_args = None  # Skip ast.literal_eval
                        else:
                            # Fallback to ast
                            eval_str = f"({args_str},)"
                            parsed_args = ast.literal_eval(eval_str)
                    else:
                        # Use ast.literal_eval for other cases
                        if args_str:
                            eval_str = f"({args_str},)" if not args_str.endswith(',') else f"({args_str})"
                            parsed_args = ast.literal_eval(eval_str)
                        else:
                            parsed_args = ()
                    
                    # Convert parsed_args to dict if we used ast.literal_eval
                    if parsed_args is not None:
                        # Convert to dict based on function
                        if function_name in ['create_file', 'write_file']:
                            if len(parsed_args) >= 2:
                                args = {"filepath": parsed_args[0], "content": parsed_args[1]}
                            else:
                                args = {"filepath": parsed_args[0] if parsed_args else "", "content": ""}
                        elif function_name in ['create_directory', 'list_directory']:
                            args = {"dirpath": parsed_args[0] if parsed_args else "."}
                        elif function_name == 'execute_python':
                            args = {"code": parsed_args[0] if parsed_args else ""}
                        elif function_name == 'read_file':
                            args = {"filepath": parsed_args[0] if parsed_args else ""}
                        else:
                            args = {"filepath": parsed_args[0] if parsed_args else ""}
                    # else: args was already set in the manual parsing above
                
                except (ValueError, SyntaxError) as e:
                    logger.warning(f"Failed to parse args for {function_name}: {e}")
                    continue
                
                content_size = len(args.get('content', args.get('code', '')))
                logger.info(f"Executing: {category}.{function_name} (content size: {content_size} chars)")
                
                # Execute the tool
                result = await mcp_manager.execute_tool(function_name, args)
                tool_results.append(f"✓ {function_name}: {result}")
                
            except Exception as e:
                logger.error(f"Tool execution failed for {function_name}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                tool_results.append(f"✗ {function_name}: Error - {str(e)}")
    
    # Append results to response
    if tool_results:
        results_text = "\n\n[TOOL_EXECUTION_RESULTS]\n" + "\n".join(tool_results) + "\n[/TOOL_EXECUTION_RESULTS]"
        response = response + results_text
    
    return response


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


def find_agent_by_id(yaml_data, agent_id):
    """Find agent configuration by ID"""
    for agent in yaml_data["agents"]:
        if agent["id"] == agent_id:
            return agent
    return None


async def execute_single_agent(agent_data, yaml_data, context="", step_info=""):
    """
    Execute a single agent and return its response
    
    Args:
        agent_data: Agent configuration
        yaml_data: Full YAML data (for model configs)
        context: Previous context to include
        step_info: Information about current step (for logging)
    
    Returns:
        Agent's response text
    """
    global mcp_manager
    
    role = agent_data.get("role", "Agent")
    goal = agent_data.get("goal", "")
    description = agent_data.get("description", "")
    instructions = agent_data.get("instruction", "")
    model_name = agent_data.get("model", "gemini-2.5-flash")
    mcp_tools = agent_data.get("tools", [])
    
    logger.info(f"{step_info}Agent Role: {role}")
    logger.info(f"{step_info}Agent Goal: {goal}")
    logger.info(f"{step_info}Model: {model_name}")
    
    if mcp_tools:
        logger.info(f"{step_info}MCP Tools: {', '.join(mcp_tools)}")
    
    # Build prompt
    base_prompt = f"You are {role}. Your goal is: {goal}. {description} {instructions}".strip()
    
    # Add MCP tool information to prompt if available
    if mcp_manager and mcp_tools:
        tool_schemas = mcp_manager.get_tool_schemas_for_agent(mcp_tools)
        if tool_schemas:
            tools_info = "\n\nAvailable MCP Tools:\n"
            for schema in tool_schemas:
                tools_info += f"- {schema['name']}: {schema['description']}\n"
            base_prompt += tools_info
            logger.debug(f"{step_info}Added {len(tool_schemas)} MCP tool schemas to prompt")
    
    if context:
        prompt = f"{base_prompt}\n\nRelevant Previous Context:\n{context}"
        logger.debug(f"{step_info}Including context in prompt")
    else:
        prompt = base_prompt
    
    logger.debug(f"{step_info}Prompt length: {len(prompt)} chars")
    
    # Get model configuration from YAML
    model_config = yaml_data.get('models', {}).get(model_name, {
        'model': model_name,
        'temperature': 0.7,
        'max_tokens': 8096
    })
    
    # Add MCP tools to model config if available
    if mcp_manager and mcp_tools:
        tool_schemas = mcp_manager.get_tool_schemas_for_agent(mcp_tools)
        if tool_schemas:
            model_config['tools'] = tool_schemas
    
    # Save user prompt
    save_to_context("User", base_prompt)
    
    # Make LLM request
    request_start = datetime.now()
    logger.info(f"{step_info}Sending request to {model_name}...")
    
    # Run the CPU-bound LLM request in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, get_llm_response, prompt, model_name, model_config)
    
    response_end = datetime.now()
    elapsed = (response_end - request_start).total_seconds()
    logger.info(f"{step_info}Response received in {elapsed:.2f}s ({len(response)} chars)")
    
    # Parse and execute tool calls if MCP tools are available
    if mcp_manager and mcp_tools:
        logger.info(f"{step_info}Checking for tool calls...")
        # Run async tool execution
        response = await parse_and_execute_tool_calls(response, mcp_tools)
    
    # Display response
    logger.info(f"\n{step_info}{role} Response:")
    logger.info(f"{step_info}" + "-" * 60)
    logger.info(response)
    logger.info(f"{step_info}" + "-" * 60)
    
    # Save to context
    save_to_context(role, response)
    
    return response


async def execute_sequential_workflow(yaml_data):
    """Execute sequential workflow"""
    logger.info("="*80)
    logger.info("EXECUTING SEQUENTIAL WORKFLOW")
    logger.info("="*80)
    
    steps = yaml_data["workflow"]["steps"]
    logger.info(f"Total steps in workflow: {len(steps)}")
    logger.debug(f"Step sequence: {' -> '.join(steps)}")
    
    for step_idx, agent_id in enumerate(steps):
        logger.info(f"\n{'='*80}")
        logger.info(f"STEP {step_idx + 1}/{len(steps)}: Processing agent '{agent_id}'")
        logger.info(f"{'='*80}")
        
        # Find agent by ID
        agent_data = find_agent_by_id(yaml_data, agent_id)
        
        if not agent_data:
            logger.warning(f"Agent '{agent_id}' not found in configuration, skipping step")
            continue
        
        # Build context for agents after the first one
        if step_idx == 0:
            context = ""
        else:
            logger.info("Retrieving relevant context from previous steps (RAG)")
            base_prompt = f"You are {agent_data.get('role', 'Agent')}. Your goal is: {agent_data.get('goal', '')}"
            context = read_context_for_agent(base_prompt, max_memories=5)
        
        # Execute agent
        await execute_single_agent(agent_data, yaml_data, context, step_info="")


async def execute_parallel_workflow(yaml_data):
    """Execute parallel workflow with TRUE parallel execution using asyncio"""
    logger.info("="*80)
    logger.info("EXECUTING PARALLEL WORKFLOW (ASYNC)")
    logger.info("="*80)
    
    branches = yaml_data["workflow"]["branches"]
    then_agent_id = yaml_data["workflow"].get("then")
    
    logger.info(f"Total parallel branches: {len(branches)}")
    logger.debug(f"Branches: {', '.join(branches)}")
    if then_agent_id:
        logger.info(f"Consolidation agent: {then_agent_id}")
    
    # Prepare branch execution function
    async def execute_branch(branch_info):
        branch_idx, branch_name = branch_info
        logger.info(f"\n{'='*60}")
        logger.info(f"[PARALLEL] BRANCH {branch_idx + 1}/{len(branches)}: '{branch_name}'")
        logger.info(f"{'='*60}")
        
        agent_data = find_agent_by_id(yaml_data, branch_name)
        
        if not agent_data:
            logger.warning(f"[PARALLEL] Agent '{branch_name}' not found, skipping")
            return None
        
        # Execute agent (no context for parallel branches)
        step_info = f"[Branch {branch_idx + 1}] "
        return await execute_single_agent(agent_data, yaml_data, context="", step_info=step_info)
    
    # Execute all branches in parallel using asyncio.gather
    logger.info(f"\n🚀 Starting {len(branches)} parallel executions...")
    
    branch_tasks = [execute_branch((idx, branch)) for idx, branch in enumerate(branches)]
    
    # Run tasks concurrently
    results = await asyncio.gather(*branch_tasks, return_exceptions=True)
    
    # Process results
    branch_responses = []
    for idx, result in enumerate(results):
        branch_name = branches[idx]
        if isinstance(result, Exception):
            logger.error(f"✗ Branch '{branch_name}' failed: {result}")
        elif result:
            branch_responses.append(result)
            logger.info(f"✓ Branch '{branch_name}' completed")
    
    logger.info(f"\n✓ All {len(branch_responses)} parallel branches completed")
    
    # Execute consolidation agent if specified
    if then_agent_id:
        logger.info(f"\n{'='*80}")
        logger.info(f"CONSOLIDATION PHASE: Executing agent '{then_agent_id}'")
        logger.info(f"{'='*80}")
        
        agent_data = find_agent_by_id(yaml_data, then_agent_id)
        
        if agent_data:
            # Build context from all branch responses
            context = "\n\n".join([
                f"Branch Response {i+1}:\n{resp}" 
                for i, resp in enumerate(branch_responses)
            ])
            
            logger.info(f"Including {len(branch_responses)} branch responses in context")
            
            # Execute consolidation agent
            await execute_single_agent(agent_data, yaml_data, context, step_info="[CONSOLIDATION] ")


def run_agent(yaml_file):
    """Main function to run agent workflow autonomously"""
    global mcp_manager
    
    # Setup logging first
    log_file = setup_logging()
    
    workflow_start = datetime.now()
    logger.info("="*80)
    logger.info("WORKFLOW EXECUTION STARTED")
    logger.info(f"Start Time: {workflow_start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"YAML File: {yaml_file}")
    logger.info("="*80)
    
    async def async_workflow():
        global mcp_manager
        
        try:
            # Clear context for fresh start
            clear_context()
            
            # Load YAML data
            yaml_data = load_yaml_data(yaml_file)
            
            # Initialize MCP manager if tools are configured
            if 'tools' in yaml_data:
                logger.info(f"Tools config found: {yaml_data['tools']}")
                logger.info("Initializing MCP Tools Manager...")
                mcp_manager = MCPManager(yaml_data['tools'])
                await mcp_manager.initialize()
                logger.info(f"MCP Manager initialized with {len(mcp_manager.tool_schemas)} tools")
            
            logger.info("Configuration Summary:")
            logger.info(f"  - Total Agents: {len(yaml_data['agents'])}")
            logger.info(f"  - Workflow Type: {yaml_data['workflow']['type']}")
            
            # Check workflow type and execute accordingly
            workflow_type = yaml_data["workflow"]["type"]
            
            if workflow_type == "sequential":
                await execute_sequential_workflow(yaml_data)
            elif workflow_type == "parallel":
                await execute_parallel_workflow(yaml_data)
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
            logger.info(f"Context saved to: {Path(__file__).parent / 'context' / 'raw.json'}")
            
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
        finally:
            # Cleanup MCP manager
            if mcp_manager:
                await mcp_manager.shutdown()
    
    # Run the async workflow
    try:
        asyncio.run(async_workflow())
    except Exception:
        # Exception already logged in async_workflow
        raise


if __name__ == "__main__":
    # Use relative path from this file's location
    # CHANGE THIS PATH to your actual test file
    input_file = Path(__file__).parent / "examples" / "config_parallel.yml"
    
    if not input_file.exists():
        print(f"Error: Config file not found at {input_file}")
        print("Please update the path in Agent.py or create the example file")
    else:
        run_agent(str(input_file))