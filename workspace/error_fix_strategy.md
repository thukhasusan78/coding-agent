import os

def fix_deployment_structure():
    """
    Resolves 'requirements.txt not found' error by consolidating dependencies 
    from sub-project directories into the root directory.
    """
    # Define paths to existing requirements files based on the project structure
    sub_requirements = [
        'chinese_tutor/requirements.txt',
        'bitcoin_tracker/requirements.txt'
    ]
    
    root_requirements_file = 'requirements.txt'
    consolidated_dependencies = set()

    print("--- Deployment Fix: Consolidating Requirements ---")

    # 1. Extract dependencies from sub-projects
    for req_path in sub_requirements:
        if os.path.exists(req_path):
            print(f"Reading: {req_path}")
            try:
                with open(req_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments, empty lines, and recursive references
                        if line and not line.startswith('#') and not line.startswith('-r'):
                            consolidated_dependencies.add(line)
            except Exception as e:
                print(f"Error reading {req_path}: {e}")
        else:
            print(f"Warning: {req_path} not found. Skipping.")

    # 2. Ensure core dependencies are present (Safety check)
    # Based on file structure, streamlit and common libs are likely needed
    core_deps = {'streamlit', 'pandas', 'requests'}
    for dep in core_deps:
        if not any(dep in existing.lower() for existing in consolidated_dependencies):
            consolidated_dependencies.add(dep)

    # 3. Write the consolidated requirements to the root directory
    try:
        with open(root_requirements_file, 'w') as f:
            f.write("# AUTO-GENERATED CONSOLIDATED REQUIREMENTS\n")
            f.write("# This file was created to resolve deployment errors.\n\n")
            for dep in sorted(list(consolidated_dependencies)):
                f.write(f"{dep}\n")
        
        print(f"SUCCESS: Created {root_requirements_file} at root.")
        print(f"Total unique dependencies: {len(consolidated_dependencies)}")
        print("--- Fix Complete ---")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to write root requirements file: {e}")
        exit(1)

if __name__ == "__main__":
    # Execute the fix
    fix_deployment_structure()

    # Deployment Instruction:
    # If the deployment environment allows custom build commands, 
    # run this script before 'pip install -r requirements.txt'.
    # Alternatively, ensure this script is committed to the repo.