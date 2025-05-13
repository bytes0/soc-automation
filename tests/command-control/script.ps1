# sample_script.ps1

# 1) Greeting
Write-Host "=== PowerShell Test Script ==="

# 2) Basic system info
Write-Host "Date & Time: $(Get-Date)"
Write-Host "Computer Name: $env:COMPUTERNAME"
Write-Host "User: $env:USERNAME"
Write-Host "OS:  $(Get-CimInstance Win32_OperatingSystem).Caption"

# 3) Top 5 CPU-hungry processes
Write-Host "`nTop 5 Processes by CPU Usage:"
Get-Process |
  Sort-Object -Property CPU -Descending |
  Select-Object -First 5 -Property @{N='Process';E={$_.ProcessName}},@{N='CPU(s)';E={$_.CPU}} |
  Format-Table -AutoSize

# 4) List all environment variables
Write-Host "`nEnvironment Variables:"
Get-ChildItem Env: | Sort-Object Name | Format-Table -AutoSize

# 5) Simple loop example
Write-Host "`nCounting to 5:"
1..5 | ForEach-Object {
    Start-Sleep -Seconds 1
    Write-Host "  $_"
}

Write-Host "`nScript complete."
