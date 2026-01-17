"""
Advanced usage examples for YAMLParser class.
Shows how to integrate with real agent workflows.
"""

import json
from engine.YAMLParser import YAMLParser


def example_1_basic_parsing():
    """Example 1: Basic parsing and accessing agent information"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Parsing")
    print("="*70)
    
    parser = YAMLParser("engine/test/test2.yml")
    config = parser.parse()
    
    print(f"\nTotal agents: {len(config['agents'])}")
    print(f"Workflow type: {config['workflow']['type']}")

    print(config)

    print("Agent IDs:")
    for agent in config['agents']:
        print(f"  - {agent['id']}")
    
    # Access first agent
    first_agent = config['agents'][0]
    print(f"\nFirst agent details:")
    print(f"  ID: {first_agent['id']}")
    print(f"  Role: {first_agent['role']}")
    print(f"  Goal: {first_agent['goal']}")
    print(f"  Model: {first_agent['model']}")
    
    return config


def example_2_working_with_defaults():
    """Example 2: Demonstrate how defaults fill missing values"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Defaults for Missing Values")
    print("="*70)
    
    # test4.yml has agents without role/goal defined
    parser = YAMLParser("engine/test/test4.yml")
    config = parser.parse()
    
    agent = config['agents'][0]
    
    print(f"\nAgent: {agent['id']}")
    print(f"  Role (not in YAML): {agent['role']} <- Default: 'Agent'")
    print(f"  Goal (not in YAML): '{agent['goal']}' <- Default: empty string")
    print(f"  Description (provided): {agent['description'][:50]}...")
    print(f"  Model (provided): {agent['model']}")
    print(f"  Tools (not in YAML): {agent['tools']} <- Default: empty list")
    
    return config


def example_3_workflow_execution_order():
    """Example 3: Extract execution order from workflow"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Workflow Execution Order")
    print("="*70)
    
    # Sequential workflow
    parser_seq = YAMLParser("engine/test/test1.yml")
    config_seq = parser_seq.parse()
    
    print("\nSEQUENTIAL WORKFLOW:")
    print(f"  Type: {config_seq['workflow']['type']}")
    print(f"  Execution order:")
    for i, step in enumerate(config_seq['workflow']['steps'], 1):
        print(f"    {i}. {step}")
    
    # Parallel workflow
    parser_par = YAMLParser("engine/test/test2.yml")
    config_par = parser_par.parse()
    
    print("\nPARALLEL WORKFLOW:")
    print(f"  Type: {config_par['workflow']['type']}")
    print(f"  Parallel branches:")
    for branch in config_par['workflow']['branches']:
        print(f"    - {branch}")
    if 'then' in config_par['workflow']:
        print(f"  Then execute: {config_par['workflow']['then']}")
    
    return config_seq, config_par


def example_4_model_management():
    """Example 4: Working with model configurations"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Model Configuration Management")
    print("="*70)
    
    parser = YAMLParser("engine/examples/config_sequential.yml")
    config = parser.parse()
    
    print(f"\nAvailable models: {list(config['models'].keys())}")
    
    # Show model details
    for model_name, model_config in config['models'].items():
        print(f"\n  {model_name}:")
        print(f"    Provider: {model_config['provider']}")
        print(f"    Model: {model_config['model']}")
        print(f"    Temperature: {model_config['temperature']}")
        print(f"    Max tokens: {model_config['max_tokens']}")
    
    # Show which agents use which models
    print("\nAgent-to-Model mapping:")
    for agent in config['agents']:
        print(f"  {agent['id']} -> {agent['model']}")
    
    return config


def example_5_agent_hierarchy():
    """Example 5: Working with agent hierarchies (sub-agents)"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Agent Hierarchies and Sub-agents")
    print("="*70)
    
    parser = YAMLParser("engine/examples/config_sequential.yml")
    config = parser.parse()
    
    # Find agents with sub-agents
    print("\nAgent hierarchy:")
    for agent in config['agents']:
        if agent['sub_agents']:
            print(f"\n{agent['id']} (Coordinator):")
            print(f"  Delegates to:")
            for sub_agent_id in agent['sub_agents']:
                # Find sub-agent details
                sub_agent = next(
                    (a for a in config['agents'] if a['id'] == sub_agent_id),
                    None
                )
                if sub_agent:
                    print(f"    - {sub_agent_id} ({sub_agent['role']})")
        else:
            print(f"\n{agent['id']} (Worker):")
            print(f"  No sub-agents")
    
    return config


def example_6_custom_filtering():
    """Example 6: Filter and process agents based on criteria"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Custom Agent Filtering")
    print("="*70)
    
    parser = YAMLParser("engine/examples/config_sequential.yml")
    config = parser.parse()
    
    # Find agents with specific tools
    print("\nAgents with 'python' tool:")
    python_agents = [
        a for a in config['agents']
        if 'python' in a['tools']
    ]
    for agent in python_agents:
        print(f"  - {agent['id']} ({agent['role']})")
    
    # Find agents with sub-agents (coordinators)
    print("\nCoordinator agents:")
    coordinators = [
        a for a in config['agents']
        if a['sub_agents']
    ]
    for agent in coordinators:
        print(f"  - {agent['id']} ({agent['role']})")
        print(f"    Sub-agents: {', '.join(agent['sub_agents'])}")
    
    return config


def example_7_export_to_json():
    """Example 7: Export parsed configuration to JSON"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Export to JSON")
    print("="*70)
    
    parser = YAMLParser("engine/test/test3.yml")
    config = parser.parse()
    
    json_str = json.dumps(config, indent=2)
    print("\nJSON export (first 500 chars):")
    print(json_str[:500] + "...")
    
    # Could save to file
    # with open("output_config.json", "w") as f:
    #     json.dump(config, f, indent=2)
    
    return config


def example_8_batch_processing():
    """Example 8: Process multiple YAML files"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Batch Processing Multiple Files")
    print("="*70)
    
    files = [
        "engine/test/test1.yml",
        "engine/test/test2.yml",
        "engine/test/test3.yml",
        "engine/test/test4.yml",
    ]
    
    results = {}
    for file_path in files:
        try:
            parser = YAMLParser(file_path)
            config = parser.parse()
            results[file_path] = {
                'agents_count': len(config['agents']),
                'workflow_type': config['workflow']['type'],
                'models': list(config['models'].keys()),
                'success': True
            }
        except Exception as e:
            results[file_path] = {
                'error': str(e),
                'success': False
            }
    
    print("\nProcessing results:")
    for file_path, result in results.items():
        file_name = file_path.split('/')[-1]
        if result['success']:
            print(f"\n✓ {file_name}")
            print(f"  Agents: {result['agents_count']}")
            print(f"  Workflow: {result['workflow_type']}")
            print(f"  Models: {result['models']}")
        else:
            print(f"\n✗ {file_name}")
            print(f"  Error: {result['error']}")
    
    return results


if __name__ == "__main__":
    # Run all examples
    example_1_basic_parsing()
    # example_2_working_with_defaults()
    # example_3_workflow_execution_order()
    # example_4_model_management()
    # example_5_agent_hierarchy()
    # example_6_custom_filtering()
    # example_7_export_to_json()
    # example_8_batch_processing()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70 + "\n")
