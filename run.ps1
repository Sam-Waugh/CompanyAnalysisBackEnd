$PROJECT_DIRECTORY = (Get-Item .).FullName
$VENV_DIRECTORY = "$PROJECT_DIRECTORY\.venv"

#if (-Not Test-Path env:VIRTUAL_ENV) {
    Set-Location "$VENV_DIRECTORY\Scripts"
    .\Activate.ps1
#}
Set-Location "$PROJECT_DIRECTORY"
fastapi run main.py