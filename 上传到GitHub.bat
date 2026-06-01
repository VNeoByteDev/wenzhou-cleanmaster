@echo off
chcp 65001 >nul 2>&1
title 一键发布到GitHub

:: 配置：你的文件名
set "src=网站.html"
set "dst=index.html"

:: 1. 检查文件
if not exist "%src%" (
    echo 错误：找不到 %src%
    pause
    exit /b 1
)

:: 2. 复制成 index.html（覆盖）
copy "%src%" "%dst%" /y >nul
echo [1] 已复制：%src% → %dst%
echo.

:: 3. Git 提交上传
echo [2] git add .
git add .

echo [3] git commit
git commit -m "更新网站 %date% %time%"

echo [4] git push origin main
git push origin main

echo.
echo ✅ 全部完成！
pause