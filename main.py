"""
Main entry point for the Agentic Workflow System.
Processes YAML configuration files to execute AI agent workflows.
"""

import argparse
import sys
import warnings
from pathlib import Path
from engine.Agent import run_agent

# Suppress Windows pipe cleanup warnings
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")


def main():
    """Parse command-line arguments and execute the workflow."""
    parser = argparse.ArgumentParser(
        description="Execute AI agent workflows from YAML configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --file engine/examples/config_sequential.yml
  python main.py --file engine/test/test1.yml
        """
    )
    
    parser.add_argument(
        '--file',
        type=str,
        required=True,
        help='Path to the YAML configuration file'
    )
    
    args = parser.parse_args()
    
    # Validate file exists
    yaml_file = Path(args.file)
    if not yaml_file.exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)
    
    if not yaml_file.suffix.lower() in ['.yml', '.yaml']:
        print(f"Warning: File does not have .yml or .yaml extension: {args.file}")
    
    # Execute the workflow
    print(f"Loading workflow from: {args.file}")
    print("-" * 60)
    
    try:
        run_agent(str(yaml_file))
    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError executing workflow: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
