@echo off
chcp 65001 >nul 2>&1
title strMan Packing Script

echo ========================================
echo   strMan Packing Script
echo ========================================
echo.

REM ==================== 配置 ====================
set "SOURCE_DIR=%~dp0"
set "PROJECT_DIR=%SOURCE_DIR%"
set "PACK_DIR=%SOURCE_DIR%strMan-portable"
set "TEMP_DIR=%TEMP%\strMan-temp"

REM 设置打包选项 (Y=包含, N=不包含)
set "INCLUDE_PYTHON=Y"
set "INCLUDE_MODELS=Y"
set "INCLUDE_CUDA=Y"

echo Source: %PROJECT_DIR%
echo Pack to: %PACK_DIR%
echo.

REM ==================== 清理 ====================
echo [1/5] Cleaning...
if exist "%PACK_DIR%" rmdir /s /q "%PACK_DIR%"
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"
echo   Cleaned.
echo.

REM ==================== 复制项目代码 ====================
echo [2/5] Copying project...

REM 复制项目目录 (排除 output, temp, __pycache__)
xcopy /E /Y /Q "%PROJECT_DIR%src" "%TEMP_DIR%\project\src\"
xcopy /E /Y /Q "%PROJECT_DIR%main.py" "%TEMP_DIR%\project\"
xcopy /E /Y /Q "%PROJECT_DIR%config.yaml" "%TEMP_DIR%\project\"
xcopy /E /Y /Q "%PROJECT_DIR%requirements.txt" "%TEMP_DIR%\project\"
xcopy /E /Y /Q "%PROJECT_DIR%.env" "%TEMP_DIR%\project\"

REM 排除的文件
if exist "%PROJECT_DIR%output" rmdir /s /q "%TEMP_DIR%\project\output"
if exist "%PROJECT_DIR%temp" rmdir /s /q "%TEMP_DIR%\project\temp"

echo   Project copied.
echo.

REM ==================== 修改配置 ====================
echo [3/5] Updating config...

REM 创建临时配置文件，修改路径为相对路径
powershell -Command "(Get-Content '%TEMP_DIR%\project\config.yaml') -replace 'G:\\\\fastwhisper-res\\\\fastwhisper-model', '..\\models' -replace 'G:\\\\fastwhisper-res\\\\fastwhisper\\\\fastwhisper', '..\\python\\fastwhisper' -replace 'C:\\\\Users\\\\mengxi\\\\.conda\\\\envs\\\\fastwhisper', '..\\cuda' | Set-Content '%TEMP_DIR%\project\config.yaml'"

echo   Config updated.
echo.

REM ==================== Python 环境 ====================
if "%INCLUDE_PYTHON%"=="Y" (
    echo [4/5] Copying Python environment...
    set "PYTHON_SRC=C:\Users\mengxi\.conda\envs\fastwhisper"

   REM 基础文件
    xcopy /E /Y /Q "%PYTHON_SRC%\python.exe" "%TEMP_DIR%\python\"
    xcopy /E /Y /Q "%PYTHON_SRC%\pythonw.exe" "%TEMP_DIR%\python\"
    xcopy /E /Y /Q "%PYTHON_SRC%\python3.dll" "%TEMP_DIR%\python\"
    xcopy /E /Y /Q "%PYTHON_SRC%\python311.dll" "%TEMP_DIR%\python\"

    xcopy /E /Y /Q "%PYTHON_SRC%\Lib" "%TEMP_DIR%\python\Lib"
    xcopy /E /Y /Q "%PYTHON_SRC%\Library" "%TEMP_DIR%\python\Library"
    xcopy /E /Y /Q "%PYTHON_SRC%\Scripts" "%TEMP_DIR%\python\Scripts"
    xcopy /E /Y /Q "%PYTHON_SRC%\DLLs" "%TEMP_DIR%\python\DLLs"

    REM 根目录 DLL (api-ms-*)
    xcopy /E /Y /Q "%PYTHON_SRC%\*.dll" "%TEMP_DIR%\python\"

    REM 复制 faster-whisper 模块
    xcopy /E /Y /Q "G:\fastwhisper-res\fastwhisper\fastwhisper" "%TEMP_DIR%\python\fastwhisper"

    REM 复制 VC++ runtime
    copy /Y "C:\Windows\System32\vcruntime140.dll" "%TEMP_DIR%\python\"
    copy /Y "C:\Windows\System32\msvcp140.dll" "%TEMP_DIR%\python\"

    echo   Python copied.
)

if "%INCLUDE_MODELS%"=="Y" (
    echo [.] Copying models...
    xcopy /E /Y /Q "G:\fastwhisper-res\fastwhisper-model" "%TEMP_DIR%\models"
    echo   Models copied.
)

if "%INCLUDE_CUDA%"=="Y" (
    echo [.] Copying CUDA...
    set "CUDA_SRC=C:\Users\mengxi\.conda\envs\fastwhisper\Lib\site-packages\nvidia"
    xcopy /E /Y /Q "%CUDA_SRC%\nvidia" "%TEMP_DIR%\cuda"
    echo   CUDA copied.
)

echo.

REM ==================== 创建启动脚本 ====================
echo [5/5] Creating run.bat...

(
echo @echo off
echo chcp 65001 ^>nul 2^>^&1
echo title strMan
echo.
echo cd /d "%%~dp0.."
echo cd project
echo.
echo set "LOCAL_PY=%%CD%%\..\python\python.exe"
echo set "CONDA_ENV=%%CD%%\..\python"
echo set "PATH=%%CONDA_ENV%%\DLLs;%%CONDA_ENV%%;%%CONDA_ENV%%\Scripts;%%CONDA_ENV%%\Library\bin;%%PATH%%"
echo set "CUDA_DIR=%%CD%%\..\cuda"
echo set "PATH=%%CUDA_DIR%%\nvidia\cublas\bin;%%CUDA_DIR%%\nvidia\cudnn\bin;%%CUDA_DIR%%\nvidia\cuda_nvrtc\bin;%%PATH%%"
echo set "PYTHONHOME=%%CONDA_ENV%%"
echo set "PYTHONPATH=%%CONDA_ENV%%\fastwhisper;%%PYTHONPATH%%"
echo.
echo if not exist "%%LOCAL_PY%%" ^(
echo     echo [ERROR] Python not found
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Using: %%LOCAL_PY%%\n\echo.\nif "%%~1"=="" ^(\necho     echo Usage: run.bat "video.mp4"\necho     echo.\necho     pause\n) ^else ^(\necho     "%%LOCAL_PY%%" main.py %*\necho ^)
) > "%TEMP_DIR%\project\run.bat"

echo   run.bat created.
echo.

REM ==================== 完成 ====================
echo ========================================
echo   DONE!
echo ========================================
echo.
echo Packed to: %PACK_DIR%
echo.
echo Use: run.bat "video.mp4"
echo.

REM 打开打包目录
explorer "%TEMP_DIR%"

pause