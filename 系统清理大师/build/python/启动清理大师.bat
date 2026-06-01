@echo off
title 启动系统清理大师
echo 正在启动文洲系统清理大师...

:: 自动跳转到当前 .bat 文件所在的目录
cd /d "%~dp0"

:: 运行程序
python.exe "CleanMaster.py"

echo 程序已退出
pause