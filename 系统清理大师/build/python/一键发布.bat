@echo off
chcp 65001 >nul
title 文洲系统清理大师 一键发布

:: ==================================
::  每次更新只改这里的版本号就行！
set VERSION=4.0.1
:: ==================================

echo.
echo ==================================
echo 1. 正在打包 Python → EXE
echo ==================================
pyinstaller -F --noconsole CleanMaster.py

echo.
echo ==================================
echo 2. 复制到官网根目录（覆盖旧版）
echo ==================================
copy "dist\CleanMaster.exe" "C:\Users\Administrator\Desktop\wenzhou\系统清理大师_setup_%VERSION%.exe" /y

echo.
echo ==================================
echo 3. 自动更新版本号文件
echo ==================================
echo %VERSION% > "C:\Users\Administrator\Desktop\wenzhou\version.txt"

echo.
echo ==================================
echo 4. 自动上传到 GitHub
echo ==================================
cd /d "C:\Users\Administrator\Desktop\wenzhou"
git add .
git commit -m "更新到 v%VERSION%"
git push origin main

echo.
echo ==================================
echo ✅ 全部完成！
echo 官网：https://vneobytedev.github.io/wenzhou-cleanmaster/
echo 等3-5分钟就会自动更新
echo ==================================
pause