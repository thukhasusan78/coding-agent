import os

def fix_deployment_structure():
    """
    Fixes the 'requirements.txt not found' error by consolidating 
    dependencies from subdirectories into the root directory.
    """
    subprojects = [
        'bitcoin_price_tracker',
        'chinese_tutor'
    ]
    
    combined_requirements = set()
    
    # Standard dependencies often required for these types of apps if files are missing
    base_requirements = {
        'streamlit',
        'pandas',
        'requests',
        'pyyaml'
    }
    combined_requirements.update(base_requirements)

    for project in subprojects:
        req_path = os.path.join(project, 'requirements.txt')
        if os.path.exists(req_path):
            with open(req_path, 'r') as f:
                for line in f:
                    dep = line.strip()
                    if dep and not dep.startswith('#'):
                        combined_requirements.add(dep)
        else:
            print(f"Warning: {req_path} not found.")

    # Write the consolidated requirements.txt to the root directory
    root_req_path = 'requirements.txt'
    with open(root_req_path, 'w') as f:
        for dep in sorted(combined_requirements):
            f.write(f"{dep}\n")
            
    print(f"Successfully created {root_req_path} with {len(combined_requirements)} dependencies.")

if __name__ == "__main__":
    fix_deployment_structure()

# To resolve the error immediately in a shell environment, run:
# cat bitcoin_price_tracker/requirements.txt chinese_tutor/requirements.txt | sort | uniq > requirements.txt