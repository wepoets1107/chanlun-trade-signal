@echo off
cd /d "%~dp0"
start "ChanLun BTC Risk MCP" /D "%~dp0" /min python run_server.py
echo Open http://127.0.0.1:8040 in your browser.
