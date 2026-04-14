@echo off
echo Installing uv...
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

SET "PATH=%PATH%;%USERPROFILE%\.local\bin"
echo Done, starting Signal Viewer...
powershell -ExecutionPolicy ByPass -NoProfile -Command "Start-Process -FilePath 'uv' -ArgumentList 'run sv'"