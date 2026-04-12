@echo off
powershell -ExecutionPolicy ByPass -NoProfile -Command "Start-Process -WindowStyle Hidden -FilePath 'uv' -ArgumentList 'run sv'"