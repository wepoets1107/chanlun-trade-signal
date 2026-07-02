@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "$pids = Get-NetTCPConnection -LocalPort 8040 -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 } | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($processId in $pids) { Stop-Process -Id $processId -Force; Write-Host \"Stopped process $processId\" }"
