@echo off
chcp 65001 >nul

:: 检测Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 检测到您的系统中未安装Python环境！
    echo 本软件需要Python 3.9或更高版本才能运行。
    echo.
    echo 请选择以下选项：
    echo 1. 打开Python官方下载页面
    echo 2. 退出
    echo.
    set /p choice=请输入选项编号： 
    
    if "%choice%"=="1" (
        echo 正在打开Python官方下载页面...
        start "" "https://www.python.org/downloads/"
    ) else (
        echo 已退出。
    )
    pause
    exit /b 1
)

:: 检测Python版本
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i

:: 提取主版本号和次版本号
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAIN_VERSION=%%a
    set MINOR_VERSION=%%b
)

:: 检查版本是否满足要求（至少3.9）
if %MAIN_VERSION% lss 3 (
    echo Python版本过低！需要Python 3.9或更高版本。
    echo 您当前的Python版本是 %PYTHON_VERSION%
    echo 正在打开Python官方下载页面...
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
) else if %MAIN_VERSION% equ 3 if %MINOR_VERSION% lss 9 (
    echo Python版本过低！需要Python 3.9或更高版本。
    echo 您当前的Python版本是 %PYTHON_VERSION%
    echo 正在打开Python官方下载页面...
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)

:: 检查是否存在EXE文件，如果存在则运行EXE
if exist "dist\番剧批量重命名工具 - Kaze.exe" (
    echo 正在启动番剧批量重命名工具 - Kaze...
    start "" "dist\番剧批量重命名工具 - Kaze.exe"
    exit /b 0
)

:: 如果没有EXE文件，直接运行Python脚本
if exist "main_tkinter.py" (
    echo 正在启动番剧批量重命名工具 - Kaze...
    python main_tkinter.py
    exit /b 0
)

echo 错误：未找到可执行文件或Python脚本！
echo 请确保软件已正确安装。
pause
exit /b 1