# ============================================================
# 用户配置区域 - 请在这里修改路径
# ============================================================

# 临时目录位置 (不要放在C盘)
# 示例: "D:\\Temp\\strMan-temp" 或 "E:\\temp\\strMan-pack-temp"
USER_TEMP_DIR = "D:\\Temp\\strMan-temp"  # None = 使用默认 (TEMP环境变量下的strMan-temp-时间戳)

# 输出目录位置 (不要放在本目录)
# 示例: "E:\\output\\strMan-portable" 或 "D:\\portable\\strMan"
USER_OUTPUT_DIR = r"D:\output\strMan-portable-v2"  # None = 使用默认 (源码目录的上一级)

# 是否包含 Python 环境
INCLUDE_PYTHON = True

# 是否包含模型
INCLUDE_MODELS = True

# 是否包含 CUDA
INCLUDE_CUDA = True

# ============================================================
# 源码路径配置 (根据你的实际情况修改)
# ============================================================

# conda python 环境路径
PYTHON_SRC = r"C:\Users\mengxi\.conda\envs\fastwhisper"

# fastwhisper 模块路径
FASTWHISPER_MODULE_SRC = r"G:\fastwhisper-res\fastwhisper\fastwhisper"

# 模型目录路径
MODEL_SRC = r"G:\fastwhisper-res\fastwhisper-model"

# ============================================================
# 以下为打包脚本内部逻辑，请勿修改
# ============================================================

import os
import shutil
import sys
from datetime import datetime

print("=" * 50)
print("strMan Packing Script")
print("=" * 50)
print()

# 配置
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = "strMan-portable"

# 使用用户配置的临时目录，或使用默认
if USER_TEMP_DIR:
    TEMP_DIR = os.path.join(USER_TEMP_DIR, f"strMan-temp-{datetime.now().strftime('%Y%m%d%H%M%S')}")
else:
    TEMP_DIR = os.path.join(os.environ.get("TEMP", "D:\\Temp"), f"strMan-temp-{datetime.now().strftime('%Y%m%d%H%M%S')}")

# 使用用户配置的输出目录，或使用默认
if USER_OUTPUT_DIR:
    PACK_DIR = USER_OUTPUT_DIR
else:
    PACK_DIR = os.path.join(os.path.dirname(SOURCE_DIR), PROJECT_NAME)

print(f"Source: {SOURCE_DIR}")
print(f"Temp: {TEMP_DIR}")
print(f"Pack to: {PACK_DIR}")
print()

# 路径配置
PYTHON_SRC = r"C:\Users\mengxi\.conda\envs\fastwhisper"
FASTWHISPER_MODULE_SRC = r"G:\fastwhisper-res\fastwhisper\fastwhisper"
MODEL_SRC = r"G:\fastwhisper-res\fastwhisper-model"

# 1. 清理
print("[1/5] Cleaning...")
if os.path.exists(TEMP_DIR):
    shutil.rmtree(TEMP_DIR)
os.makedirs(TEMP_DIR, exist_ok=True)
print("  Cleaned.")
print()

# 2. 复制项目代码
print("[2/5] Copying project...")

# 复制目录
for item in ["src"]:
    src_path = os.path.join(SOURCE_DIR, item)
    if os.path.exists(src_path):
        dst_path = os.path.join(TEMP_DIR, "project", item)
        shutil.copytree(src_path, dst_path)
        print(f"  Copied: {item}/")

# 复制文件
for item in ["main.py", "config.yaml", "requirements.txt", ".env", "README.md", "CHANGELOG.md"]:
    src_path = os.path.join(SOURCE_DIR, item)
    if os.path.exists(src_path):
        shutil.copy2(src_path, os.path.join(TEMP_DIR, "project", item))
        print(f"  Copied: {item}")

print("  Project copied.")
print()

# 3. 修改配置为相对路径
print("[3/5] Updating config...")

config_path = os.path.join(TEMP_DIR, "project", "config.yaml")
if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换绝对路径为相对路径 (双反斜杠避免 YAML 转义问题)
    # 原始路径替换后，需要用双反斜杠，否则 YAML 双引号会把 \p 当成转义字符
    content = content.replace(r"G:\\fastwhisper-res\\fastwhisper-model", r"..\\models")
    content = content.replace(r"G:\\fastwhisper-res\\fastwhisper\\fastwhisper", r"..\\python\\fastwhisper")
    content = content.replace(r"C:\\Users\\mengxi\\.conda\\envs\\fastwhisper", r"..\\cuda")
    
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("  Config updated.")
print()

# 4. Python 环境
if INCLUDE_PYTHON:
    print("[4/5] Copying Python environment...")
    
    # 创建目录
    os.makedirs(os.path.join(TEMP_DIR, "python"), exist_ok=True)
    
    # 基础文件
    for f in ["python.exe", "pythonw.exe", "python3.dll", "python311.dll"]:
        src = os.path.join(PYTHON_SRC, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(TEMP_DIR, "python", f))
    
    # Lib 目录 (使用 copy2 避免递归问题)
    src_lib = os.path.join(PYTHON_SRC, "Lib")
    dst_lib = os.path.join(TEMP_DIR, "python", "Lib")
    if os.path.exists(src_lib):
        shutil.copytree(src_lib, dst_lib)
    
    # Library 目录
    src_library = os.path.join(PYTHON_SRC, "Library")
    dst_library = os.path.join(TEMP_DIR, "python", "Library")
    if os.path.exists(src_library):
        shutil.copytree(src_library, dst_library)
    
    # Scripts 目录
    src_scripts = os.path.join(PYTHON_SRC, "Scripts")
    dst_scripts = os.path.join(TEMP_DIR, "python", "Scripts")
    if os.path.exists(src_scripts):
        shutil.copytree(src_scripts, dst_scripts)
    
    # DLLs 目录
    src_dlls = os.path.join(PYTHON_SRC, "DLLs")
    dst_dlls = os.path.join(TEMP_DIR, "python", "DLLs")
    if os.path.exists(src_dlls):
        shutil.copytree(src_dlls, dst_dlls)
    
    # 根目录 DLL
    for f in os.listdir(PYTHON_SRC):
        if f.endswith(".dll"):
            src_file = os.path.join(PYTHON_SRC, f)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, os.path.join(TEMP_DIR, "python"))
    
    # faster-whisper 模块
    if os.path.exists(FASTWHISPER_MODULE_SRC):
        dst_fw = os.path.join(TEMP_DIR, "python", "fastwhisper")
        if os.path.exists(FASTWHISPER_MODULE_SRC):
            shutil.copytree(FASTWHISPER_MODULE_SRC, dst_fw)
    
    # VC++ runtime
    vc_dlls = [r"C:\Windows\System32\vcruntime140.dll", r"C:\Windows\System32\msvcp140.dll"]
    for vc in vc_dlls:
        if os.path.exists(vc):
            shutil.copy2(vc, os.path.join(TEMP_DIR, "python"))
    
    print("  Python copied.")

# 模型
if INCLUDE_MODELS:
    print("[.] Copying models...")
    if os.path.exists(MODEL_SRC):
        shutil.copytree(MODEL_SRC, os.path.join(TEMP_DIR, "models"))
    print("  Models copied.")

# CUDA
if INCLUDE_CUDA:
    print("[.] Copying CUDA...")
    cuda_src = os.path.join(PYTHON_SRC, r"Lib\site-packages\nvidia")
    if os.path.exists(cuda_src):
        shutil.copytree(cuda_src, os.path.join(TEMP_DIR, "cuda", "nvidia"))
    print("  CUDA copied.")

print()

# 5. 创建启动脚本
print("[5/5] Creating run.bat...")

run_bat = '''@echo off
chcp 65001 >nul 2>&1
title strMan

cd /d "%~dp0.."
cd project

set "LOCAL_PY=%CD%\\..\\python\\python.exe"
set "CONDA_ENV=%CD%\\..\\python"

set "PATH=%CONDA_ENV%\\DLLs;%CONDA_ENV%;%CONDA_ENV%\\Scripts;%CONDA_ENV%\\Library\\bin;%PATH%"

set "CUDA_DIR=%CD%\\..\\cuda"
set "PATH=%CUDA_DIR%\\nvidia\\cublas\\bin;%CUDA_DIR%\\nvidia\\cudnn\\bin;%CUDA_DIR%\\nvidia\\cuda_nvrtc\\bin;%PATH%"

set "PYTHONHOME=%CONDA_ENV%"
set "PYTHONPATH=%CONDA_ENV%\\fastwhisper;%PYTHONPATH%"

if not exist "%LOCAL_PY%" (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo Using: %LOCAL_PY%
echo.

if "%~1"=="" (
    echo Usage: run.bat "video.mp4"
    echo.
    pause
) else (
    "%LOCAL_PY%" main.py %*
)
'''

with open(os.path.join(TEMP_DIR, "project", "run.bat"), "w", encoding="utf-8") as f:
    f.write(run_bat)

print("  run.bat created.")
print()

# 移动到最终位置
print("Moving to final location...")

import stat

def remove_readonly(func, path, exc):
    """强制删除只读文件"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

if os.path.exists(PACK_DIR):
    shutil.rmtree(PACK_DIR, onerror=remove_readonly)
shutil.move(TEMP_DIR, PACK_DIR)

# 完成
print()
print("=" * 50)
print("DONE!")
print("=" * 50)
print()
print(f"Packed to: {PACK_DIR}")
print()
print("Use: run.bat \"video.mp4\"")
print()

# 打开目录
os.startfile(PACK_DIR)