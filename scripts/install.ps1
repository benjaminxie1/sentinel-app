# Sentinel Fire Detection System - Windows Installer
# Professional deployment script for Windows 10/11

param(
    [switch]$SkipChecks,
    [string]$InstallPath = "C:\Program Files\Sentinel",
    [switch]$Silent
)

# Requires PowerShell 5.1 or later
#Requires -Version 5.1
#Requires -RunAsAdministrator

# Color functions for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Info($Message) {
    Write-ColorOutput Green "[INFO] $Message"
}

function Write-Warning($Message) {
    Write-ColorOutput Yellow "[WARN] $Message"
}

function Write-Error($Message) {
    Write-ColorOutput Red "[ERROR] $Message"
}

# Installation configuration
$ServiceName = "SentinelFireDetection"
$ServiceDisplayName = "Sentinel Fire Detection System"
$ServiceDescription = "Supplementary fire detection using AI and camera feeds"

$ConfigDir = "$env:ProgramData\Sentinel"
$LogDir = "$env:ProgramData\Sentinel\Logs"
$DataDir = "$env:ProgramData\Sentinel\Data"

# System requirements
$MinRAMGB = 8
$MinDiskGB = 100
$RequiredPythonVersion = [Version]"3.10.0"

# Display header
Write-Host ""
Write-Host "================================================================" -ForegroundColor Blue
Write-Host "        Sentinel Fire Detection System - Windows Installer     " -ForegroundColor Blue
Write-Host "================================================================" -ForegroundColor Blue
Write-Host ""
Write-Warning "⚠️  CRITICAL SAFETY NOTICE:"
Write-Warning "   This is a SUPPLEMENTARY fire detection system only."
Write-Warning "   Does NOT replace certified fire alarm systems."
Write-Warning "   Always maintain UL-listed fire detection as primary."
Write-Host ""

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-SystemRequirements {
    Write-Info "Checking system requirements..."
    
    # Check Windows version
    $osVersion = [System.Environment]::OSVersion.Version
    if ($osVersion.Major -lt 10) {
        Write-Error "Unsupported Windows version: $($osVersion). Windows 10 or later required."
        exit 1
    }
    Write-Info "Windows version: $($osVersion) ✓"
    
    # Check RAM
    $totalRAM = (Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory
    $totalRAMGB = [math]::Round($totalRAM / 1GB, 1)
    
    if ($totalRAMGB -lt $MinRAMGB) {
        Write-Error "Insufficient RAM: ${totalRAMGB}GB (minimum: ${MinRAMGB}GB)"
        exit 1
    }
    Write-Info "RAM: ${totalRAMGB}GB ✓"
    
    # Check disk space
    $systemDrive = Get-CimInstance -ClassName Win32_LogicalDisk | Where-Object { $_.DeviceID -eq $env:SystemDrive }
    $freeSpaceGB = [math]::Round($systemDrive.FreeSpace / 1GB, 1)
    
    if ($freeSpaceGB -lt $MinDiskGB) {
        Write-Error "Insufficient disk space: ${freeSpaceGB}GB (minimum: ${MinDiskGB}GB)"
        exit 1
    }
    Write-Info "Disk space: ${freeSpaceGB}GB available ✓"
    
    # Check GPU (optional)
    try {
        $gpuInfo = Get-CimInstance -ClassName Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" } | Select-Object -First 1
        if ($gpuInfo) {
            Write-Info "NVIDIA GPU detected: $($gpuInfo.Name) ✓"
        } else {
            Write-Warning "No NVIDIA GPU detected - CPU inference will be slower"
        }
    } catch {
        Write-Warning "Could not detect GPU information"
    }
    
    # Check PowerShell version
    $psVersion = $PSVersionTable.PSVersion
    Write-Info "PowerShell version: $psVersion ✓"
}

function Install-Prerequisites {
    Write-Info "Installing prerequisites..."
    
    # Check if Chocolatey is installed
    if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Info "Installing Chocolatey package manager..."
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    }
    
    # Install Python 3.10+
    $pythonInstalled = $false
    try {
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+\.\d+)") {
            $currentVersion = [Version]$matches[1]
            if ($currentVersion -ge $RequiredPythonVersion) {
                Write-Info "Python $currentVersion already installed ✓"
                $pythonInstalled = $true
            }
        }
    } catch {
        # Python not found
    }
    
    if (-not $pythonInstalled) {
        Write-Info "Installing Python 3.10..."
        choco install python310 -y
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    }
    
    # Install Git
    if (!(Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Info "Installing Git..."
        choco install git -y
    } else {
        Write-Info "Git already installed ✓"
    }
    
    # Install Node.js
    if (!(Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Info "Installing Node.js..."
        choco install nodejs -y
    } else {
        $nodeVersion = & node --version
        Write-Info "Node.js already installed: $nodeVersion ✓"
    }
    
    # Install Rust
    if (!(Get-Command rustc -ErrorAction SilentlyContinue)) {
        Write-Info "Installing Rust..."
        choco install rust -y
    } else {
        $rustVersion = & rustc --version
        Write-Info "Rust already installed: $rustVersion ✓"
    }
    
    # Install Visual Studio Build Tools (required for some Python packages)
    try {
        $buildTools = Get-CimInstance -ClassName Win32_Product | Where-Object { $_.Name -like "*Visual Studio*Build Tools*" }
        if (-not $buildTools) {
            Write-Info "Installing Visual Studio Build Tools..."
            choco install visualstudio2022buildtools --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools" -y
        } else {
            Write-Info "Visual Studio Build Tools already installed ✓"
        }
    } catch {
        Write-Warning "Could not verify Visual Studio Build Tools installation"
    }
    
    Write-Info "Prerequisites installation completed ✓"
}

function New-InstallationDirectories {
    Write-Info "Creating installation directories..."
    
    # Create main directories
    $directories = @($InstallPath, $ConfigDir, $LogDir, $DataDir, "$DataDir\models", "$DataDir\datasets", "$DataDir\alerts", "$DataDir\cameras")
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Info "Created directory: $dir"
        }
    }
    
    # Set appropriate permissions
    try {
        $acl = Get-Acl $ConfigDir
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("SYSTEM", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
        $acl.SetAccessRule($accessRule)
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
        $acl.SetAccessRule($accessRule)
        Set-Acl $ConfigDir $acl
    } catch {
        Write-Warning "Could not set directory permissions"
    }
    
    Write-Info "Directories created ✓"
}

function Install-Application {
    Write-Info "Installing Sentinel application..."
    
    # Check if we're running from the source directory
    $sourceDir = Split-Path -Parent $PSScriptRoot
    if (!(Test-Path "$sourceDir\backend")) {
        Write-Error "Application source files not found. Run installer from project root."
        exit 1
    }
    
    # Copy application files
    Write-Info "Copying application files..."
    Copy-Item -Path "$sourceDir\*" -Destination $InstallPath -Recurse -Force -Exclude @(".git", "node_modules", "target", "dist", "venv")
    
    # Create Python virtual environment
    Write-Info "Creating Python virtual environment..."
    & python -m venv "$InstallPath\venv"
    
    # Install Python dependencies
    Write-Info "Installing Python dependencies..."
    & "$InstallPath\venv\Scripts\pip.exe" install --upgrade pip
    & "$InstallPath\venv\Scripts\pip.exe" install -r "$InstallPath\requirements.txt"
    
    # Install Node dependencies
    Write-Info "Installing Node.js dependencies..."
    Set-Location $InstallPath
    & npm install
    
    # Build Tauri application
    Write-Info "Building Tauri application..."
    & npm run tauri build
    
    Write-Info "Application installed ✓"
}

function New-WindowsService {
    Write-Info "Creating Windows service..."
    
    # Create service wrapper script
    $serviceScript = @"
import sys
import os
import time
import logging
from pathlib import Path

# Add application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('$LogDir\\sentinel-service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('SentinelService')

try:
    # Import and run the main application
    from run_sentinel import main
    logger.info("Starting Sentinel Fire Detection Service")
    main()
except Exception as e:
    logger.error(f"Service error: {e}")
    sys.exit(1)
"@
    
    $serviceScript | Out-File -FilePath "$InstallPath\service_wrapper.py" -Encoding UTF8
    
    # Create batch file to run the service
    $batchContent = @"
@echo off
cd /d "$InstallPath"
"$InstallPath\venv\Scripts\python.exe" service_wrapper.py
"@
    
    $batchContent | Out-File -FilePath "$InstallPath\run_service.bat" -Encoding ASCII
    
    # Install service using NSSM (Non-Sucking Service Manager)
    if (!(Get-Command nssm -ErrorAction SilentlyContinue)) {
        Write-Info "Installing NSSM service manager..."
        choco install nssm -y
    }
    
    # Remove existing service if it exists
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Info "Removing existing service..."
        & nssm remove $ServiceName confirm
    }
    
    # Install new service
    & nssm install $ServiceName "$InstallPath\run_service.bat"
    & nssm set $ServiceName DisplayName "$ServiceDisplayName"
    & nssm set $ServiceName Description "$ServiceDescription"
    & nssm set $ServiceName Start SERVICE_AUTO_START
    & nssm set $ServiceName AppStdout "$LogDir\service-stdout.log"
    & nssm set $ServiceName AppStderr "$LogDir\service-stderr.log"
    & nssm set $ServiceName AppRotateFiles 1
    & nssm set $ServiceName AppRotateOnline 1
    & nssm set $ServiceName AppRotateSeconds 86400
    & nssm set $ServiceName AppRotateBytes 10485760
    
    Write-Info "Windows service created ✓"
}

function New-FirewallRules {
    Write-Info "Configuring Windows Firewall..."
    
    try {
        # Allow RTSP traffic
        New-NetFirewallRule -DisplayName "Sentinel - RTSP Cameras" -Direction Inbound -Protocol TCP -LocalPort 554,8554 -Action Allow -Profile Any -ErrorAction SilentlyContinue
        
        # Allow web interface (if needed)
        New-NetFirewallRule -DisplayName "Sentinel - Web Interface" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow -Profile Any -ErrorAction SilentlyContinue
        
        Write-Info "Firewall rules configured ✓"
    } catch {
        Write-Warning "Could not configure firewall rules"
    }
}

function New-DefaultConfiguration {
    Write-Info "Creating default configuration files..."
    
    # Detection configuration
    $detectionConfig = @"
detection:
  thresholds:
    immediate_alert: 0.95
    review_queue: 0.85
    log_only: 0.70
  environmental:
    fog_adjustment: -0.05
    sunset_hours: [17, 19]
  adaptive:
    enabled: false
    learning_window_days: 7
    max_auto_adjustment: 0.05

system:
  detection_latency_target: 2.0
  max_concurrent_cameras: 10
  gpu_enabled: true
  
logging:
  level: INFO
  max_file_size: 100MB
  backup_count: 10
"@
    
    $detectionConfig | Out-File -FilePath "$ConfigDir\detection_config.yaml" -Encoding UTF8
    
    # Network configuration
    $networkConfig = @"
monitor_interval: 30
test_timeout: 5
failover_threshold: 3
test_targets: ['8.8.8.8', '1.1.1.1', '208.67.222.222']

interface_priorities:
  ethernet: 1
  wifi: 2
  cellular: 3
"@
    
    $networkConfig | Out-File -FilePath "$ConfigDir\network_config.yaml" -Encoding UTF8
    
    # Alert configuration
    $alertConfig = @"
alert_config:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  smtp_username: ""
  smtp_password: ""
  smtp_use_tls: true
  
  max_retries: 3
  retry_interval: 60
  max_alerts_per_hour: 10
  max_alerts_per_day: 50
  
  sms_providers:
    - name: "twilio"
      api_url: "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
      account_sid: ""
      auth_token: ""
      from_number: ""
"@
    
    $alertConfig | Out-File -FilePath "$ConfigDir\alerts.yaml" -Encoding UTF8
    
    # Recipients configuration
    $recipientsConfig = @"
recipients:
  - name: "admin"
    email: "admin@example.com"
    phone: "+1234567890"
    alert_types: ["P1", "P2"]
    enabled: false
"@
    
    $recipientsConfig | Out-File -FilePath "$ConfigDir\recipients.yaml" -Encoding UTF8
    
    # Camera configuration
    $cameraConfig = @"
cameras: []
last_updated: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
"@
    
    $cameraConfig | Out-File -FilePath "$ConfigDir\cameras.yaml" -Encoding UTF8
    
    Write-Info "Configuration files created ✓"
}

function Test-Installation {
    Write-Info "Running installation health checks..."
    
    # Test Python environment
    try {
        $pythonTest = & "$InstallPath\venv\Scripts\python.exe" -c "import torch, cv2, ultralytics; print('Python dependencies OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Info "Python dependencies ✓"
        } else {
            Write-Error "Python dependencies check failed: $pythonTest"
            return $false
        }
    } catch {
        Write-Error "Python environment test failed"
        return $false
    }
    
    # Test service installation
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Info "Service installation ✓"
    } else {
        Write-Error "Service installation check failed"
        return $false
    }
    
    # Test configuration files
    $configFiles = @("$ConfigDir\detection_config.yaml", "$ConfigDir\alerts.yaml", "$ConfigDir\cameras.yaml")
    foreach ($file in $configFiles) {
        if (Test-Path $file) {
            Write-Info "Configuration file exists: $(Split-Path -Leaf $file) ✓"
        } else {
            Write-Error "Configuration file missing: $file"
            return $false
        }
    }
    
    Write-Info "Health checks passed ✓"
    return $true
}

function Show-PostInstallInstructions {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "                Installation Completed Successfully!             " -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Blue
    Write-Host ""
    Write-Host "1. Configure alert recipients:"
    Write-Host "   notepad `"$ConfigDir\recipients.yaml`""
    Write-Host ""
    Write-Host "2. Configure email/SMS settings:"
    Write-Host "   notepad `"$ConfigDir\alerts.yaml`""
    Write-Host ""
    Write-Host "3. Add RTSP cameras:"
    Write-Host "   notepad `"$ConfigDir\cameras.yaml`""
    Write-Host ""
    Write-Host "4. Start the service:"
    Write-Host "   Start-Service -Name $ServiceName"
    Write-Host ""
    Write-Host "5. Check service status:"
    Write-Host "   Get-Service -Name $ServiceName"
    Write-Host ""
    Write-Host "6. View logs:"
    Write-Host "   Get-Content `"$LogDir\sentinel-service.log`" -Tail 50 -Wait"
    Write-Host ""
    Write-Host "Management Commands:" -ForegroundColor Blue
    Write-Host "   Start:    Start-Service -Name $ServiceName"
    Write-Host "   Stop:     Stop-Service -Name $ServiceName"
    Write-Host "   Restart:  Restart-Service -Name $ServiceName"
    Write-Host "   Status:   Get-Service -Name $ServiceName"
    Write-Host ""
    Write-Host "Configuration Files:" -ForegroundColor Blue
    Write-Host "   Detection: $ConfigDir\detection_config.yaml"
    Write-Host "   Cameras:   $ConfigDir\cameras.yaml"
    Write-Host "   Alerts:    $ConfigDir\alerts.yaml"
    Write-Host "   Network:   $ConfigDir\network_config.yaml"
    Write-Host ""
    Write-Host "Log Files:" -ForegroundColor Blue
    Write-Host "   Service:   $LogDir\sentinel-service.log"
    Write-Host "   Stdout:    $LogDir\service-stdout.log"
    Write-Host "   Stderr:    $LogDir\service-stderr.log"
    Write-Host ""
    Write-Warning "⚠️  IMPORTANT SAFETY REMINDER:"
    Write-Warning "   This system is SUPPLEMENTARY ONLY"
    Write-Warning "   Always maintain certified fire alarm systems"
    Write-Warning "   Test and verify all fire safety systems regularly"
    Write-Host ""
}

# Main installation process
function Start-Installation {
    try {
        Write-Info "Starting Sentinel Fire Detection System installation..."
        
        # Check administrator privileges
        if (!(Test-Administrator)) {
            Write-Error "This installer must be run as Administrator"
            exit 1
        }
        
        # System requirements check
        if (-not $SkipChecks) {
            Test-SystemRequirements
        }
        
        # Install prerequisites
        Install-Prerequisites
        
        # Create directories
        New-InstallationDirectories
        
        # Install application
        Install-Application
        
        # Create Windows service
        New-WindowsService
        
        # Configure firewall
        New-FirewallRules
        
        # Create default configuration
        New-DefaultConfiguration
        
        # Run health checks
        if (Test-Installation) {
            Write-Info "Installation completed successfully!"
            
            if (-not $Silent) {
                Show-PostInstallInstructions
            }
        } else {
            Write-Error "Installation health checks failed"
            exit 1
        }
        
    } catch {
        Write-Error "Installation failed: $($_.Exception.Message)"
        Write-Error "Stack trace: $($_.ScriptStackTrace)"
        exit 1
    }
}

# Run the installation
Start-Installation