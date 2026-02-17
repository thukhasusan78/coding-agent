import os

def fix_deployment_structure():
    """
    Consolidates requirements.txt files from subdirectories to the root 
    to resolve deployment 'File Not Found' errors.
    """
    root_dir = os.getcwd()
    consolidated_requirements = set()
    
    # Subdirectories containing requirements
    sub_projects = ['bitcoin_price_tracker', 'chinese_tutor']
    
    for project in sub_projects:
        req_path = os.path.join(root_dir, project, 'requirements.txt')
        if os.path.exists(req_path):
            with open(req_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        consolidated_requirements.add(line)
    
    # Create the missing root requirements.txt
    root_req_path = os.path.join(root_dir, 'requirements.txt')
    with open(root_req_path, 'w') as f:
        for req in sorted(list(consolidated_requirements)):
            f.write(f"{req}\n")
            
    print(f"SUCCESS: Created {root_req_path} with {len(consolidated_requirements)} dependencies.")

if __name__ == "__main__":
    fix_deployment_structure()