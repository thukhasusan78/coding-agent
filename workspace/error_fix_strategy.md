import os

def fix_deployment_error():
    """
    Fixes the 'requirements.txt not found' error by consolidating 
    dependencies from sub-projects into a root requirements.txt file.
    """
    # Define paths to existing requirements files
    sub_requirements = [
        'bitcoin_price_tracker/requirements.txt',
        'chinese_tutor/requirements.txt'
    ]
    
    root_requirements_path = 'requirements.txt'
    unique_dependencies = set()

    print("Analyzing sub-project dependencies...")

    for req_path in sub_requirements:
        if os.path.exists(req_path):
            try:
                with open(req_path, 'r') as f:
                    for line in f:
                        dependency = line.strip()
                        # Ignore empty lines and comments
                        if dependency and not dependency.startswith('#'):
                            unique_dependencies.add(dependency)
                print(f"Successfully read: {req_path}")
            except Exception as e:
                print(f"Error reading {req_path}: {e}")
        else:
            print(f"Warning: {req_path} not found.")

    # Add common deployment dependencies if missing
    common_deps = {'streamlit', 'pandas', 'requests', 'pyyaml'}
    unique_dependencies.update(common_deps)

    # Write the consolidated requirements.txt to the root directory
    try:
        with open(root_requirements_path, 'w') as f:
            for dep in sorted(list(unique_dependencies)):
                f.write(f"{dep}\n")
        print(f"SUCCESS: Created root '{root_requirements_path}' with {len(unique_dependencies)} dependencies.")
    except Exception as e:
        print(f"FAILED to create root requirements file: {e}")

if __name__ == "__main__":
    fix_deployment_error()