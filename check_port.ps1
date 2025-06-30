# Check what's using port 1420
Write-Host "Checking port 1420..."
$port1420 = netstat -ano | findstr ":1420"
if ($port1420) {
    Write-Host "Port 1420 is in use:"
    Write-Host $port1420
} else {
    Write-Host "Port 1420 is free"
}

Write-Host "`nChecking for Python/Node processes..."
$processes = Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*" -or $_.ProcessName -like "*sentinel*"}
if ($processes) {
    Write-Host "Found processes:"
    $processes | Format-Table ProcessName, Id, CPU -AutoSize
} else {
    Write-Host "No Python/Node/Sentinel processes found"
}

Write-Host "`nChecking for any processes on port 1420..."
$tcpConnections = Get-NetTCPConnection -LocalPort 1420 -ErrorAction SilentlyContinue
if ($tcpConnections) {
    Write-Host "TCP connections on port 1420:"
    $tcpConnections | Format-Table LocalAddress, LocalPort, RemoteAddress, State, OwningProcess -AutoSize
} else {
    Write-Host "No TCP connections on port 1420"
}