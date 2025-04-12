import os
import sys
import json
import yaml

# Check if PyYAML is installed
try:
    import yaml
    print("PyYAML is installed")
except ImportError:
    print("PyYAML is not installed")
    sys.exit(1)

# Check if main.py exists
if not os.path.exists('main.py'):
    print("main.py does not exist")
    sys.exit(1)
else:
    print("main.py exists")

# Check if docker-compose.yaml exists
if not os.path.exists('docker-compose.yaml'):
    print("docker-compose.yaml does not exist")
else:
    print("docker-compose.yaml exists")
    # Read docker-compose.yaml
    try:
        with open('docker-compose.yaml', 'r') as f:
            docker_compose = yaml.safe_load(f)
        print("Docker Compose file loaded successfully")
        print(f"Current port mapping: {docker_compose['services']['v2ray']['ports']}")
    except Exception as e:
        print(f"Error loading docker-compose.yaml: {str(e)}")

# Print the command-line arguments for main.py
import main
import inspect
print("\nCommand-line arguments for main.py:")
for action in main.__name__ == "__main__" and hasattr(main, 'parser') and main.parser._actions or []:
    if action.dest != 'help':
        print(f"  {', '.join(action.option_strings)}: {action.help}")

print("\nTest completed successfully")
