@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

REM 激活 conda 环境
call conda activate fastwhisper

REM 或者使用完整路径 (二选一)
REM set PYTHONPATH=%CONDA_PREFIX%

cd /d "%~dp0"

REM 使用 conda 环境中的 Python
python main.py %*