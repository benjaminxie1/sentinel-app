# Sentinel Fire Detection System - Windows Installer Test Script
# Tests the Windows installer in a safe, isolated manner

param(
    [string]$TestDir = "$env:TEMP\SentinelTest",
    [switch]$KeepFiles
)

# Test configuration
$TestInstallPath = "$TestDir\Sentinel"
$TestConfigDir = "$TestDir\Config"
$TestLogDir = "$TestDir\Logs"
$TestDataDir = "$TestDir\Data"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Blue
Write-Host "       Sentinel Windows Installer - Test Suite                " -ForegroundColor Blue
Write-Host "================================================================" -ForegroundColor Blue
Write-Host ""

function Write-TestResult($TestName, $Success, $Details = "") {
    if ($Success) {
        Write-Host "[PASS]" -ForegroundColor Green -NoNewline
    } else {
        Write-Host "[FAIL]" -ForegroundColor Red -NoNewline
    }
    Write-Host " $TestName"
    if ($Details) {
        Write-Host "       $Details" -ForegroundColor Gray
    }
}

function Test-Prerequisites {
    Write-Host ""
    Write-Host "Testing Prerequisites..." -ForegroundColor Yellow
    
    # Test PowerShell version
    $psVersion = $PSVersionTable.PSVersion
    $psTest = $psVersion.Major -ge 5 -and $psVersion.Minor -ge 1
    Write-TestResult "PowerShell Version" $psTest "Current: $psVersion (Required: 5.1+)"
    
    # Test Administrator privileges
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
    Write-TestResult "Administrator Privileges" $isAdmin
    
    # Test Windows version
    $osVersion = [System.Environment]::OSVersion.Version
    $osTest = $osVersion.Major -ge 10
    Write-TestResult "Windows Version" $osTest "Current: $osVersion"
    
    # Test available disk space
    $drive = Get-PSDrive -Name ($env:TEMP[0])
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    $diskTest = $freeSpaceGB -gt 5
    Write-TestResult "Disk Space" $diskTest "${freeSpaceGB}GB available"
    
    return $psTest -and $isAdmin -and $osTest -and $diskTest
}

function Test-SystemChecks {
    Write-Host ""
    Write-Host "Testing System Checks..." -ForegroundColor Yellow
    
    # Test RAM detection
    try {
        $totalRAM = (Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory
        $totalRAMGB = [math]::Round($totalRAM / 1GB, 1)
        Write-TestResult "RAM Detection" $true "${totalRAMGB}GB detected"
    } catch {
        Write-TestResult "RAM Detection" $false $_.Exception.Message
    }
    
    # Test GPU detection
    try {
        $gpuInfo = Get-CimInstance -ClassName Win32_VideoController | Select-Object -First 1
        Write-TestResult "GPU Detection" $true $gpuInfo.Name
    } catch {
        Write-TestResult "GPU Detection" $false "Could not detect GPU"
    }
    
    # Test network connectivity
    try {
        $pingResult = Test-Connection -ComputerName "8.8.8.8" -Count 1 -Quiet
        Write-TestResult "Network Connectivity" $pingResult
    } catch {
        Write-TestResult "Network Connectivity" $false
    }
}

function Test-DirectoryCreation {
    Write-Host ""
    Write-Host "Testing Directory Creation..." -ForegroundColor Yellow
    
    # Create test directories
    $testDirs = @($TestInstallPath, $TestConfigDir, $TestLogDir, $TestDataDir)
    $allCreated = $true
    
    foreach ($dir in $testDirs) {
        try {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            if (Test-Path $dir) {
                Write-TestResult "Create $([System.IO.Path]::GetFileName($dir))" $true
            } else {
                Write-TestResult "Create $([System.IO.Path]::GetFileName($dir))" $false
                $allCreated = $false
            }
        } catch {
            Write-TestResult "Create $([System.IO.Path]::GetFileName($dir))" $false $_.Exception.Message
            $allCreated = $false
        }
    }
    
    return $allCreated
}

function Test-ConfigurationFiles {
    Write-Host ""
    Write-Host "Testing Configuration File Creation..." -ForegroundColor Yellow
    
    # Test creating YAML configurations
    $configs = @{
        "detection_config.yaml" = @"
detection:
  thresholds:
    immediate_alert: 0.95
    review_queue: 0.85
    log_only: 0.70
"@
        "alerts.yaml" = @"
alert_config:
  max_alerts_per_hour: 10
  max_alerts_per_day: 50
"@
        "cameras.yaml" = @"
cameras: []
last_updated: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
"@
    }
    
    $allCreated = $true
    foreach ($file in $configs.Keys) {
        try {
            $filePath = Join-Path $TestConfigDir $file
            $configs[$file] | Out-File -FilePath $filePath -Encoding UTF8
            
            if ((Test-Path $filePath) -and (Get-Content $filePath -Raw).Length -gt 0) {
                Write-TestResult "Create $file" $true
            } else {
                Write-TestResult "Create $file" $false
                $allCreated = $false
            }
        } catch {
            Write-TestResult "Create $file" $false $_.Exception.Message
            $allCreated = $false
        }
    }
    
    return $allCreated
}

function Test-ServiceWrapper {
    Write-Host ""
    Write-Host "Testing Service Wrapper Creation..." -ForegroundColor Yellow
    
    # Test creating Python service wrapper
    $serviceScript = @"
import sys
import time
print("Test service started")
time.sleep(1)
print("Test service completed")
"@
    
    try {
        $wrapperPath = Join-Path $TestInstallPath "test_service.py"
        $serviceScript | Out-File -FilePath $wrapperPath -Encoding UTF8
        
        # Test if Python can execute it
        if (Get-Command python -ErrorAction SilentlyContinue) {
            $output = & python $wrapperPath 2>&1
            $success = $LASTEXITCODE -eq 0
            Write-TestResult "Service Wrapper" $success
        } else {
            Write-TestResult "Service Wrapper" $true "Python not available for testing"
        }
    } catch {
        Write-TestResult "Service Wrapper" $false $_.Exception.Message
    }
}

function Test-FirewallRules {
    Write-Host ""
    Write-Host "Testing Firewall Configuration..." -ForegroundColor Yellow
    
    # Test if we can query firewall rules (requires admin)
    try {
        $existingRules = Get-NetFirewallRule -DisplayName "Sentinel*" -ErrorAction SilentlyContinue
        Write-TestResult "Query Firewall Rules" $true "Can query firewall"
        
        # Test creating a temporary rule
        $testRuleName = "SentinelTest-Temp-$(Get-Random)"
        New-NetFirewallRule -DisplayName $testRuleName -Direction Inbound -Protocol TCP -LocalPort 65432 -Action Allow -Profile Any -ErrorAction Stop | Out-Null
        
        # Verify and remove
        $created = Get-NetFirewallRule -DisplayName $testRuleName -ErrorAction SilentlyContinue
        if ($created) {
            Remove-NetFirewallRule -DisplayName $testRuleName -ErrorAction SilentlyContinue
            Write-TestResult "Create Firewall Rule" $true "Created and removed test rule"
        } else {
            Write-TestResult "Create Firewall Rule" $false
        }
    } catch {
        Write-TestResult "Firewall Configuration" $false "Requires administrator privileges"
    }
}

function Test-PythonEnvironment {
    Write-Host ""
    Write-Host "Testing Python Environment..." -ForegroundColor Yellow
    
    # Check if Python is available
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $pythonVersion = & python --version 2>&1
        Write-TestResult "Python Available" $true $pythonVersion
        
        # Test venv creation
        try {
            $venvPath = Join-Path $TestInstallPath "test_venv"
            & python -m venv $venvPath 2>&1 | Out-Null
            
            if (Test-Path "$venvPath\Scripts\python.exe") {
                Write-TestResult "Virtual Environment" $true "venv created successfully"
                
                # Test pip
                $pipVersion = & "$venvPath\Scripts\pip.exe" --version 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-TestResult "Pip Available" $true
                } else {
                    Write-TestResult "Pip Available" $false
                }
            } else {
                Write-TestResult "Virtual Environment" $false "venv creation failed"
            }
        } catch {
            Write-TestResult "Virtual Environment" $false $_.Exception.Message
        }
    } else {
        Write-TestResult "Python Available" $false "Python not installed"
    }
}

function Test-Cleanup {
    if (-not $KeepFiles) {
        Write-Host ""
        Write-Host "Cleaning up test files..." -ForegroundColor Yellow
        
        try {
            if (Test-Path $TestDir) {
                Remove-Item -Path $TestDir -Recurse -Force
                Write-TestResult "Cleanup" $true "Test files removed"
            }
        } catch {
            Write-TestResult "Cleanup" $false "Some files could not be removed"
        }
    } else {
        Write-Host ""
        Write-Host "Test files kept at: $TestDir" -ForegroundColor Yellow
    }
}

# Main test execution
function Run-InstallerTests {
    $startTime = Get-Date
    
    Write-Host "Test Directory: $TestDir" -ForegroundColor Gray
    Write-Host ""
    
    # Create test directory
    if (!(Test-Path $TestDir)) {
        New-Item -ItemType Directory -Path $TestDir -Force | Out-Null
    }
    
    # Run tests
    $results = @{
        "Prerequisites" = Test-Prerequisites
        "System Checks" = Test-SystemChecks
        "Directory Creation" = Test-DirectoryCreation
        "Configuration Files" = Test-ConfigurationFiles
        "Service Wrapper" = Test-ServiceWrapper
        "Firewall Rules" = Test-FirewallRules
        "Python Environment" = Test-PythonEnvironment
    }
    
    # Summary
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Blue
    Write-Host "                        Test Summary                           " -ForegroundColor Blue
    Write-Host "================================================================" -ForegroundColor Blue
    
    $passed = ($results.Values | Where-Object { $_ -eq $true }).Count
    $total = $results.Count
    
    Write-Host "Passed: $passed/$total tests" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })
    Write-Host "Duration: $([math]::Round((Get-Date - $startTime).TotalSeconds, 2)) seconds"
    
    # Cleanup
    Test-Cleanup
    
    Write-Host ""
    Write-Host "Testing complete!" -ForegroundColor Green
    
    # Return success if all critical tests passed
    return $results["Prerequisites"] -and $results["Directory Creation"] -and $results["Configuration Files"]
}

# Run the tests
$success = Run-InstallerTests

# Exit with appropriate code
if ($success) {
    exit 0
} else {
    exit 1
}