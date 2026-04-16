@echo off
REM 一键升级脚本 - 从旧版本升级到 1.0.2-beta0.1

echo ==================================
echo Human Thinking Memory Manager 升级脚本
echo 目标版本: 1.0.2-beta0.1
echo ==================================

REM 检测当前目录
if not exist "core" if not exist "HumanThinkingMemoryManager" (
    echo 错误: 请在 QwenPaw_HumanThinkingMemoryManager 目录中运行此脚本
    pause
    exit /b 1
)

REM 检测QwenPaw路径
set QWENPAW_PATH=
if exist "..\..\..\src\qwenpaw" (
    set QWENPAW_PATH=..\..\..\
) else if exist "..\..\src\qwenpaw" (
    set QWENPAW_PATH=..\..\
) else if exist "..\src\qwenpaw" (
    set QWENPAW_PATH=..\
) else (
    echo 警告: 未找到 QwenPaw 安装目录
    echo 请确保此脚本在 QwenPaw\tools\HumanThinkingMemoryManager 目录中运行
)

REM 备份旧版本
echo.
echo 1. 备份旧版本...
mkdir backups 2>nul
set BACKUP_FILE=backups\backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.zip

if exist "HumanThinkingMemoryManager" (
    powershell Compress-Archive -Path HumanThinkingMemoryManager -DestinationPath %BACKUP_FILE%
    echo 已备份旧版本到: %BACKUP_FILE%
) else (
    echo 未找到旧版本目录，跳过备份
)

REM 清理旧文件
echo.
echo 2. 清理旧文件...
if exist "HumanThinkingMemoryManager" (
    rmdir /s /q HumanThinkingMemoryManager
    echo 已删除旧版本目录
)

REM 下载新版本
echo.
echo 3. 下载新版本...
echo 请确保已通过 git pull 或手动更新代码

REM 安装到 QwenPaw
echo.
echo 4. 安装到 QwenPaw...
if not "%QWENPAW_PATH%" == "" (
    REM 复制文件到 QwenPaw 的 tools 目录
    set TOOLS_DIR=%QWENPAW_PATH%src\qwenpaw\agents\tools
    mkdir "%TOOLS_DIR%" 2>nul
    
    REM 复制核心文件
    xcopy /E /Y core "%TOOLS_DIR%\core"
    xcopy /E /Y search "%TOOLS_DIR%\search"
    xcopy /E /Y hooks "%TOOLS_DIR%\hooks"
    xcopy /E /Y utils "%TOOLS_DIR%\utils"
    xcopy /E /Y config "%TOOLS_DIR%\config"
    copy /Y install.sh "%TOOLS_DIR%\"
    copy /Y uninstall.sh "%TOOLS_DIR%\"
    
    echo 已安装到 QwenPaw tools 目录
) else (
    echo 未找到 QwenPaw 目录，跳过安装
)

REM 运行数据库升级
echo.
echo 5. 运行数据库升级...
if exist "core\database.py" (
    echo 数据库结构已更新，下次启动时会自动升级
) else (
    echo 未找到数据库文件，跳过升级
)

echo.
echo ==================================
echo 升级完成！
echo 目标版本: 1.0.2-beta0.1
echo.
echo 新功能：
echo - 智能记忆管理：记忆分类、记忆关联、记忆摘要、记忆优先级
echo - 数据库结构优化
echo - 版本管理改进
echo.
echo 请重启 QwenPaw 以应用更改
echo ==================================
pause
