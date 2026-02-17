bash
# This script addresses the deployment error:
# "ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'"
#
# The error occurs because the deployment process is looking for 'requirements.txt'
# in the current working directory, but based on the provided file context,
# the requirements files are located within subdirectories:
# - bitcoin_price_tracker/requirements.txt
# - chinese_tutor/requirements.txt
#
# The fix involves explicitly providing the correct relative path to each
# requirements file when running the 'pip install' command.

# Optional: Upgrade pip as suggested in the error notice.
# This is not the direct fix for the FileNotFoundError, but good practice.
python -m pip install --upgrade pip

# Install dependencies for the 'bitcoin_price_tracker' application.
# This assumes the script is run from the project's root directory.
echo "Installing dependencies for bitcoin_price_tracker..."
pip install -r bitcoin_price_tracker/requirements.txt

# Install dependencies for the 'chinese_tutor' application.
# This assumes the script is run from the project's root directory.
echo "Installing dependencies for chinese_tutor..."
pip install -r chinese_tutor/requirements.txt

echo "Deployment dependency installation complete."