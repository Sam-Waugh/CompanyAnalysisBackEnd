# Change CODING_DIRECTORY to your projects folder 'C:\path\to\your\code'
$PROJECT_DIRECTORY = (Get-Item .).FullName
$VENV_DIRECTORY = "$PROJECT_DIRECTORY\.venv"
# Create the virtual environment if it doesn't already exist
if (-Not $(Test-Path $VENV_DIRECTORY)) {
Write-Host "Creating environment $VENV_NAME"
python.exe -m venv $VENV_DIRECTORY
}
# Move to venv folder and run the activation script
Set-Location "$VENV_DIRECTORY\Scripts"
.\Activate.ps1
# Install python dependancies
Set-Location "$PROJECT_DIRECTORY"
pip install -r requirements.txt