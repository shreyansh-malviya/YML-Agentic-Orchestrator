import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv


class YAMLParser:
    """
    YAML Parser that normalizes agent workflow configurations into a standard format.
    
    Takes a YAML file path as input and returns a normalized Python dictionary with:
    - All agents having consistent structure with defaults
    - Model configurations
    - Workflow definitions
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the parser with a YAML file path.
        
        Args:
            file_path: Path to the YAML configuration file
        """
        self.file_path = file_path
        self.raw_data = None
        self.parsed_data = None
        
        # Load environment variables
        load_dotenv()
        
        # Default values from environment or hardcoded
        self.defaults = {
            'model': os.getenv('DEFAULT_MODEL', 'gemini-2.5-flash'),
            'provider': os.getenv('DEFAULT_PROVIDER', 'google'),
            'temperature': float(os.getenv('DEFAULT_TEMPERATURE', '0.7')),
            'max_tokens': int(os.getenv('DEFAULT_MAX_TOKENS', '8096')),
            'description': '',
            'tools': [],
            'instruction': '',
            'sub_agents': [],
            'role': 'Agent',
            'goal': ''
        }
    
    def load_yaml(self) -> Dict[str, Any]:
        """Load and parse the YAML file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                self.raw_data = yaml.safe_load(file)
                return self.raw_data
        except FileNotFoundError:
            raise FileNotFoundError(f"YAML file not found: {self.file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")
    
    def validate_config(self, yaml_data: Dict[str, Any]) -> None:
        """
        Validate YAML configuration structure.
        
        Args:
            yaml_data: Parsed YAML data
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Required top-level fields
        required = ['agents', 'workflow']
        for field in required:
            if field not in yaml_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate workflow type
        workflow_type = yaml_data['workflow'].get('type')
        if workflow_type not in ['sequential', 'parallel']:
            raise ValueError(f"workflow.type must be 'sequential' or 'parallel', got: {workflow_type}")
        
        # Validate agents list
        if not isinstance(yaml_data['agents'], (list, dict)):
            raise ValueError("'agents' must be a list or dictionary")
        
        # Validate sequential workflow
        if workflow_type == 'sequential':
            if 'steps' not in yaml_data['workflow']:
                raise ValueError("Sequential workflow must have 'steps' field")
        
        # Validate parallel workflow
        if workflow_type == 'parallel':
            if 'branches' not in yaml_data['workflow']:
                raise ValueError("Parallel workflow must have 'branches' field")
    
    def _get_default_model_name(self) -> str:
        """
        Get the default model name from models section or environment.
        
        Returns:
            Name of the default model to use
        """
        if self.raw_data and 'models' in self.raw_data:
            models = self.raw_data['models']
            if 'default_model' in models:
                return 'default_model'
            # If no explicit default_model, use first model in the list
            elif models:
                return list(models.keys())[0]
        
        return self.defaults['model']
    
    def _normalize_agent(self, agent_data: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
        """
        Normalize a single agent configuration with defaults.
        
        Args:
            agent_data: Raw agent data from YAML
            index: Agent index for generating default IDs
            
        Returns:
            Normalized agent dictionary
        """
        normalized = {}
        
        # ID - required field, generate if missing
        normalized['id'] = agent_data.get('id', f'agent_{index + 1}')
        
        # Role - use default if missing
        normalized['role'] = agent_data.get('role', self.defaults['role'])
        
        # Goal - use default if missing
        normalized['goal'] = agent_data.get('goal', self.defaults['goal'])
        
        # Description - optional, default to empty string
        normalized['description'] = agent_data.get('description', self.defaults['description'])
        
        # Model - check in order: agent model -> models section -> env -> default
        if 'model' in agent_data:
            model_name = agent_data['model']
            # Check if this model is defined in models section
            if self.raw_data and 'models' in self.raw_data and model_name in self.raw_data['models']:
                normalized['model'] = model_name
            else:
                # Model name specified but not in models section, use as-is
                normalized['model'] = model_name
        else:
            # No model specified, use default
            normalized['model'] = self._get_default_model_name()
        
        # Tools - optional list, default to empty
        normalized['tools'] = agent_data.get('tools', self.defaults['tools'].copy())
        
        # Instruction - optional, default to empty string
        instruction = agent_data.get('instruction', self.defaults['instruction'])
        # Clean up multiline strings
        if instruction:
            normalized['instruction'] = instruction.strip()
        else:
            normalized['instruction'] = ''
        
        # Sub-agents - optional list, default to empty
        normalized['sub_agents'] = agent_data.get('sub_agents', self.defaults['sub_agents'].copy())
        
        return normalized
    
    def _normalize_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize workflow configuration.
        
        Args:
            workflow_data: Raw workflow data from YAML
            
        Returns:
            Normalized workflow dictionary
        """
        if not workflow_data:
            return {'type': 'sequential', 'steps': []}
        
        normalized = {
            'type': workflow_data.get('type', 'sequential')
        }
        
        # Handle different workflow types
        if normalized['type'] == 'sequential':
            steps = workflow_data.get('steps', [])
            # Extract agent IDs from steps
            normalized['steps'] = []
            for step in steps:
                if isinstance(step, dict) and 'agent' in step:
                    normalized['steps'].append(step['agent'])
                elif isinstance(step, str):
                    normalized['steps'].append(step)
        
        elif normalized['type'] == 'parallel':
            # Parallel workflows have branches and optional 'then'
            normalized['branches'] = workflow_data.get('branches', [])
            if 'then' in workflow_data:
                then_data = workflow_data['then']
                if isinstance(then_data, dict) and 'agent' in then_data:
                    normalized['then'] = then_data['agent']
                else:
                    normalized['then'] = then_data
        
        return normalized
    
    def _normalize_models(self, models_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Normalize models configuration.
        
        Args:
            models_data: Raw models data from YAML
            
        Returns:
            Normalized models dictionary
        """
        if not models_data:
            # Return default model configuration
            return {
                self.defaults['model']: {
                    'provider': self.defaults['provider'],
                    'model': self.defaults['model'],
                    'temperature': self.defaults['temperature'],
                    'max_tokens': self.defaults['max_tokens']
                }
            }
        
        normalized = {}
        for model_name, model_config in models_data.items():
            normalized[model_name] = {
                'provider': model_config.get('provider', self.defaults['provider']),
                'model': model_config.get('model', model_name),
                'temperature': model_config.get('temperature', self.defaults['temperature']),
                'max_tokens': model_config.get('max_tokens', self.defaults['max_tokens'])
            }
        
        return normalized
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse and normalize the YAML configuration.
        
        Returns:
            Normalized configuration dictionary in standard format
        """
        # Load the YAML file
        self.load_yaml()
        
        if not self.raw_data:
            raise ValueError("No data loaded from YAML file")
        
        # Validate the configuration
        self.validate_config(self.raw_data)
        
        # Initialize the normalized structure with basic fields
        self.parsed_data = {
            'agents': [],
            'workflow': {},
            'models': {}
        }
        
        # Add default MCP tools configuration if not present
        if 'tools' not in self.raw_data:
            self.parsed_data['tools'] = {
                'github': {
                    'server': 'python',
                    'args': ['engine/mcp_servers/simple_github_mcp_server.py'],
                    'env': {}
                },
                'calculator': {
                    'server': 'python',
                    'args': ['engine/mcp_servers/simple_calculator_mcp_server.py'],
                    'env': {}
                },
                'filesystem': {
                    'server': 'python',
                    'args': ['engine/mcp_servers/simple_mcp_server.py'],
                    'env': {}
                }
            }
        
        # Copy any other top-level fields (like 'tools' or 'mcp_tools')
        for key, value in self.raw_data.items():
            if key not in ['agents', 'workflow', 'models']:
                self.parsed_data[key] = value
        
        # Parse agents
        agents_data = self.raw_data.get('agents', [])
        
        # Handle both list format and dict format for agents
        if isinstance(agents_data, list):
            for idx, agent in enumerate(agents_data):
                normalized_agent = self._normalize_agent(agent, idx)
                self.parsed_data['agents'].append(normalized_agent)
        elif isinstance(agents_data, dict):
            # If agents is a dict, treat each key as an agent
            for idx, (agent_id, agent_data) in enumerate(agents_data.items()):
                if isinstance(agent_data, dict):
                    agent_data['id'] = agent_id
                    normalized_agent = self._normalize_agent(agent_data, idx)
                    self.parsed_data['agents'].append(normalized_agent)
        
        # Parse workflow
        workflow_data = self.raw_data.get('workflow', {})
        self.parsed_data['workflow'] = self._normalize_workflow(workflow_data)
        
        # Parse models
        models_data = self.raw_data.get('models', None)
        self.parsed_data['models'] = self._normalize_models(models_data)
        
        return self.parsed_data
    
    def get_parsed_data(self) -> Optional[Dict[str, Any]]:
        """
        Get the parsed data. Returns None if parse() hasn't been called yet.
        
        Returns:
            Parsed configuration dictionary or None
        """
        return self.parsed_data
    
    def __repr__(self) -> str:
        return f"YAMLParser(file_path='{self.file_path}')"