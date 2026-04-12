@echo off

SET CurrentDir="%~dp0"

powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

cmd /c "cd %CurrentDir%"
cmd run_windows.cmd