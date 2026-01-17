# YAML Parser for Agent Workflows

A robust YAML parser that normalizes agent workflow configurations into a consistent Python dictionary format with intelligent defaults handling.

## Features

✅ **Consistent Format**: Normalizes all agent configurations to a standard format regardless of how they're defined in YAML  
✅ **Smart Defaults**: Automatically fills missing fields with sensible defaults  
✅ **Environment Variables**: Loads defaults from `.env` file for easy customization  
✅ **Multiple Workflow Types**: Supports sequential and parallel workflow definitions  
✅ **Model Management**: Handles model configurations with provider and parameter settings  
✅ **Flexible Input**: Accepts agents as lists or dictionaries with proper parsing  

## Installation

```bash
pip install pyyaml python-dotenv
```

## Environment Configuration

Create a `.env` file in your project root:

```env
DEFAULT_MODEL=gemini
DEFAULT_PROVIDER=google
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=8096
```

## Usage

### Basic Example

```python
from engine.YAMLParser import YAMLParser

# Create parser with YAML file path
parser = YAMLParser("path/to/config.yml")

# Parse and get normalized configuration
config = parser.parse()

# Access the data
agents = config['agents']           # List of normalized agents
workflow = config['workflow']       # Workflow definition
models = config['models']           # Model configurations
```

### Access Agent Data

```python
for agent in config['agents']:
    print(f"ID: {agent['id']}")
    print(f"Role: {agent['role']}")
    print(f"Goal: {agent['goal']}")
    print(f"Model: {agent['model']}")
    print(f"Tools: {agent['tools']}")
    print(f"Sub-agents: {agent['sub_agents']}")
```

## Output Format

All agents are normalized to the following structure:

```python
{
    "agents": [
        {
            "id": "agent_name",              # Required - agent identifier
            "role": "Agent Role",            # Default: "Agent" if not provided
            "goal": "Agent's goal",          # Default: "" if not provided
            "description": "Description",    # Default: "" if not provided
            "model": "model_name",           # Default: from env or "gemini"
            "tools": ["tool1", "tool2"],     # Default: [] if not provided
            "instruction": "Instructions",   # Default: "" if not provided
            "sub_agents": ["sub_agent1"]     # Default: [] if not provided
        }
    ],
    "workflow": {
        "type": "sequential|parallel",
        "steps": ["agent_id1", "agent_id2"],  # For sequential
        # OR
        "branches": ["agent_id1", "agent_id2"],  # For parallel
        "then": "agent_id"                      # Optional post-processing
    },
    "models": {
        "model_name": {
            "provider": "google|openai|anthropic",
            "model": "model_identifier",
            "temperature": 0.7,
            "max_tokens": 8096
        }
    }
}
```

## Default Value Resolution

The parser uses the following priority for filling missing values:

1. **Role**: If missing → `"Agent"` (from defaults)
2. **Goal**: If missing → `""` (empty string)
3. **Description**: If missing → `""` (empty string)
4. **Model**: 
   - If specified in agent → use that model name
   - If exists in models section → use as defined in models
   - Otherwise → use environment variable `DEFAULT_MODEL` or `"gemini"`
5. **Tools**: If missing → `[]` (empty list)
6. **Instruction**: If missing → `""` (empty string)
7. **Sub-agents**: If missing → `[]` (empty list)

## Supported YAML Formats

### Sequential Workflow

```yaml
agents:
  - id: researcher
    role: Research Assistant
    goal: Find key insights
    
  - id: writer
    role: Content Writer
    goal: Write summary

workflow:
  type: sequential
  steps:
    - agent: researcher
    - agent: writer
```

### Parallel Workflow

```yaml
agents:
  - id: frontend
    role: Frontend Developer
    goal: Build UI
    
  - id: backend
    role: Backend Developer
    goal: Build API
    
  - id: reviewer
    role: Tech Lead
    goal: Review work

workflow:
  type: parallel
  branches:
    - frontend
    - backend
  then:
    agent: reviewer
```

### With Model Definitions

```yaml
agents:
  - id: coordinator
    model: claude_sonnet
    role: Coordinator
    
  - id: worker
    model: default_model

models:
  default_model:
    provider: openai
    model: gpt-4
    temperature: 0.3
    max_tokens: 4096
  claude_sonnet:
    provider: anthropic
    model: claude-sonnet-4-0
    temperature: 0.2
    max_tokens: 64000
```

## Test Files

The repository includes test YAML files demonstrating various configurations:

- **test1.yml**: Simple sequential workflow (2 agents, no model defined)
- **test2.yml**: Parallel workflow with branches and post-processing
- **test3.yml**: Sequential workflow with tools specification
- **test4.yml**: Agents without role/goal fields (uses defaults)
- **config_sequential.yml**: Full configuration with models section
- **config_parallel.yml**: Parallel workflow with detailed configuration

Run tests:

```bash
python test_parser.py
```

## Key Features Explained

### Automatic ID Generation
If an agent doesn't have an `id` field, it will be auto-generated as `agent_1`, `agent_2`, etc.

### Default Role
Unlike other fields that default to empty strings, the `role` field defaults to `"Agent"` if not provided. This ensures every agent has a meaningful role.

### Model Resolution
The parser intelligently handles model specifications:
- Uses model names defined in the `models` section if available
- Falls back to environment variables
- Provides sensible defaults

### Sub-agent Handling
Agents can specify sub-agents they delegate work to:
```python
agent = {
    "id": "coordinator",
    "sub_agents": ["worker1", "worker2"]
}
```

## Error Handling

The parser provides clear error messages:

```python
try:
    parser = YAMLParser("invalid_file.yml")
    config = parser.parse()
except FileNotFoundError:
    print("YAML file not found")
except ValueError as e:
    print(f"Error parsing YAML: {e}")
```

## Integration with Agent Framework

Use parsed configuration with your agent execution framework:

```python
from engine.YAMLParser import YAMLParser
from your_agent_framework import AgentFramework

parser = YAMLParser("config.yml")
config = parser.parse()

# Initialize agents
framework = AgentFramework(config)
result = framework.execute()
```

## Customization

### Change Default Model

Update `.env`:
```env
DEFAULT_MODEL=gpt-4
DEFAULT_PROVIDER=openai
```

### Change Temperature or Max Tokens

```env
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=4096
```

All future parses will use these defaults if fields aren't specified in the YAML.
