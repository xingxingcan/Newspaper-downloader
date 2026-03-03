@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 报纸下载器 - 打包为单文件 EXE
echo ========================================
echo.

REM 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [1/2] 安装 PyInstaller...
    pip install pyinstaller
) else (
    echo [1/2] PyInstaller 已安装
)
echo.

echo [2/2] 开始打包...
pyinstaller newspaper_downloader.spec --noconfirm
echo.

if exist "dist\报纸下载器.exe" (
    echo ========================================
    echo 打包完成！
    echo 输出文件: dist\报纸下载器.exe
    echo ========================================
    explorer dist
) else (
    echo 打包失败，请检查上方错误信息。
    pause
)
