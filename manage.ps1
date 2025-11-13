# Management CLI for Lemuel Eduspace Backend
# PowerShell version

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create virtual environment with: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then install dependencies with: venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Build arguments
$args = @($Command) + $RemainingArgs

# Run the management command
try {
    & python "manage.py" @args
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Command failed with exit code $LASTEXITCODE" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Error running command: $_" -ForegroundColor Red
}

# Deactivate virtual environment
deactivate