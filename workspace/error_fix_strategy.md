import os
import textwrap
import shutil

def fix_deployment_structure():
    """
    Senior Developer Fix:
    1. Consolidates dependencies for multi-app support (Bitcoin Tracker & Chinese Tutor).
    2. Generates a production-ready Dockerfile with dynamic entry points.
    3. Configures .dockerignore to prevent sensitive/local data leakage.
    4. Standardizes Streamlit configuration for cloud deployment.
    """
    root_dir = os.getcwd()
    
    # 1. Consolidate requirements.txt
    # Analysis of file structure suggests: chromadb (memory_db), plotly (bitcoin), openai/langchain (tutor)
    consolidated_requirements = {
        "streamlit>=1.24.0",
        "pandas",
        "requests",
        "plotly",
        "chromadb",
        "pysqlite3-binary", # Required for ChromaDB on many Linux distros
        "openai",
        "pyyaml",
        "watchdog"
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

    # 2. Generate Optimized Dockerfile
    dockerfile_content = textwrap.dedent("""
        FROM python:3.9-slim
        
        # Prevent Python from writing pyc files and buffering stdout/stderr
        ENV PYTHONDONTWRITEBYTECODE=1
        ENV PYTHONUNBUFFERED=1
        # Default app path
        ENV APP_PATH=bitcoin_price_tracker/main.py
        
        WORKDIR /app
        
        # Install system dependencies
        RUN apt-get update && apt-get install -y \\
            build-essential \\
            curl \\
            software-properties-common \\
            && rm -rf /var/lib/apt/lists/*
            
        # Install Python dependencies
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        
        # Copy project structure
        COPY . .
        
        # Ensure data directories exist
        RUN mkdir -p /app/memory_db /app/data
        
        EXPOSE 8501
        
        HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
        
        # Use shell form to allow environment variable expansion for APP_PATH
        ENTRYPOINT streamlit run ${APP_PATH} --server.port=8501 --server.address=0.0.0.0
    """).strip()
    
    with open(os.path.join(root_dir, 'Dockerfile'), 'w') as f:
        f.write(dockerfile_content)

    # 3. Create .dockerignore
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
        *.log
        checkpoints.sqlite*
        memory_db/
        active_processes.json
        cert.pem
        tunnel.log
        *.sqlite-shm
        *.sqlite-wal
    """).strip()
    
    with open(os.path.join(root_dir, '.dockerignore'), 'w') as f:
        f.write(dockerignore)

    # 4. Standardize Streamlit Config
    dot_streamlit = os.path.join(root_dir, '.streamlit')
    os.makedirs(dot_streamlit, exist_ok=True)
    
    config_toml = textwrap.dedent("""
        [server]
        headless = true
        enableCORS = false
        enableXsrfProtection = false
        port = 8501
        maxUploadSize = 200

        [browser]
        gatherUsageStats = false

        [theme]
        primaryColor = "#F63366"
        backgroundColor = "#FFFFFF"
        secondaryBackgroundColor = "#F0F2F6"
        textColor = "#262730"
        font = "sans serif"
    """).strip()
    
    with open(os.path.join(dot_streamlit, 'config.toml'), 'w') as f:
        f.write(config_toml)

    print(f"✅ Deployment structure fixed.")
    print(f"✅ Created: requirements.txt, Dockerfile, .dockerignore, .streamlit/config.toml")
    print(f"\n[DEPLOYMENT COMMANDS]")
    print(f"1. Build: docker build -t multi-app-tracker .")
    print(f"2. Run Bitcoin Tracker: docker run -p 8501:8501 multi-app-tracker")
    print(f"3. Run Chinese Tutor:   docker run -p 8501:8501 -e APP_PATH=chinese_tutor/main.py multi-app-tracker")

if __name__ == "__main__":
    fix_deployment_structure()