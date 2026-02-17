import os
import shutil
import textwrap

def fix_deployment_structure():
    """
    Senior Developer Fix: 
    1. Consolidates requirements from sub-projects.
    2. Generates a root-level Dockerfile for multi-app support.
    3. Creates a unified entry point script.
    4. Ensures streamlit configurations are respected.
    """
    root_dir = os.getcwd()
    
    # 1. Consolidate requirements.txt
    consolidated_requirements = {
        "streamlit",
        "pandas",
        "requests",
        "plotly",
        "sqlite3"
    }
    
    sub_projects = ['bitcoin_price_tracker', 'chinese_tutor']
    for project in sub_projects:
        req_path = os.path.join(root_dir, project, 'requirements.txt')
        if os.path.exists(req_path):
            with open(req_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        consolidated_requirements.add(line)
    
    with open(os.path.join(root_dir, 'requirements.txt'), 'w') as f:
        for req in sorted(list(consolidated_requirements)):
            f.write(f"{req}\n")

    # 2. Generate Dockerfile
    dockerfile_content = textwrap.dedent("""
        FROM python:3.9-slim
        
        WORKDIR /app
        
        RUN apt-get update && apt-get install -y \\
            build-essential \\
            curl \\
            software-properties-common \\
            && rm -rf /var/lib/apt/lists/*
            
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        
        COPY . .
        
        # Default to bitcoin_price_tracker, can be overridden by env var
        ENV APP_PATH=bitcoin_price_tracker/main.py
        
        EXPOSE 8501
        
        HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
        
        ENTRYPOINT ["sh", "-c", "streamlit run ${APP_PATH} --server.port=8501 --server.address=0.0.0.0"]
    """).strip()
    
    with open(os.path.join(root_dir, 'Dockerfile'), 'w') as f:
        f.write(dockerfile_content)

    # 3. Fix Streamlit Config Pathing
    # Ensure the root has a .streamlit folder if needed, or copy from sub-project
    root_streamlit = os.path.join(root_dir, '.streamlit')
    if not os.path.exists(root_streamlit):
        os.makedirs(root_streamlit)
        source_toml = os.path.join(root_dir, 'bitcoin_price_tracker', '.streamlit', 'config.toml')
        if os.path.exists(source_toml):
            shutil.copy(source_toml, os.path.join(root_streamlit, 'config.toml'))

    # 4. Create .dockerignore
    dockerignore = textwrap.dedent("""
        __pycache__/
        *.py[cod]
        *$py.class
        .env
        .venv
        env/
        venv/
        .git/
        .github/
        checkpoints.sqlite*
        memory_db/
    """).strip()
    
    with open(os.path.join(root_dir, '.dockerignore'), 'w') as f:
        f.write(dockerignore)

    print(f"✅ Deployment structure fixed.")
    print(f"✅ Created: requirements.txt, Dockerfile, .dockerignore, .streamlit/config.toml")
    print(f"👉 To run Bitcoin Tracker: docker build -t btc-app . && docker run -p 8501:8501 btc-app")
    print(f"👉 To run Chinese Tutor: docker run -p 8501:8501 -e APP_PATH=chinese_tutor/main.py btc-app")

if __name__ == "__main__":
    fix_deployment_structure()