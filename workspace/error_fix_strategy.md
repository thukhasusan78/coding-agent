import os

def fix_deployment_structure():
    """
    Fixes the 'requirements.txt not found' error by consolidating 
    dependencies from subdirectories into the root directory.
    """
    # Define paths to search for requirements
    subprojects = [
        'bitcoin_price_tracker',
        'chinese_tutor'
    ]
    
    combined_requirements = set()
    
    # Base requirements often needed for these specific Streamlit/Data apps
    base_requirements = {
        'streamlit',
        'pandas',
        'requests',
        'pyyaml',
        'plotly'
    }
    combined_requirements.update(base_requirements)

    # Iterate through subdirectories and collect dependencies
    for project in subprojects:
        req_path = os.path.join(project, 'requirements.txt')
        if os.path.exists(req_path):
            try:
                with open(req_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        dep = line.strip()
                        # Filter out comments and empty lines
                        if dep and not dep.startswith('#'):
                            # Handle potential versioning or git links
                            combined_requirements.add(dep)
                print(f"Collected dependencies from: {req_path}")
            except Exception as e:
                print(f"Error reading {req_path}: {e}")
        else:
            print(f"Warning: {req_path} not found.")

    # Write the consolidated requirements.txt to the root directory
    root_req_path = 'requirements.txt'
    try:
        # Sort requirements for consistency
        sorted_reqs = sorted(list(combined_requirements), key=lambda s: s.lower())
        
        with open(root_req_path, 'w', encoding='utf-8') as f:
            for dep in sorted_reqs:
                f.write(f"{dep}\n")
                
        print(f"Successfully created {root_req_path} with {len(sorted_reqs)} dependencies.")
        
        # Verify file creation
        if os.path.exists(root_req_path):
            print(f"Deployment Fix Verified: {os.path.abspath(root_req_path)}")
            
    except Exception as e:
        print(f"Critical Error writing root requirements: {e}")

if __name__ == "__main__":
    fix_deployment_structure()