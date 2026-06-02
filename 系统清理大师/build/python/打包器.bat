@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set "APP=文洲系统清理大师"
set "PY=CleanMaster.py"
set "ICO=icon.ico"
set "VER_FILE=local_version.txt"
set "OUT=C:\Users\Administrator\Desktop\wenzhou\系统清理大师\build\python\新exe"
set "BUILD=C:\Users\Administrator\Desktop\wenzhou\系统清理大师\build\python\build"

:: ==================== 版本自动迭代 ====================
if not exist "%VER_FILE%" echo 4.0.2>"%VER_FILE%"
set /p CURRENT_VER=<"%VER_FILE%"
for /f "tokens=1,2,3 delims=." %%a in ("%CURRENT_VER%") do (
    set MAJOR=%%a&set MINOR=%%b&set /a PATCH=%%c+1
)
set NEW_VER=!MAJOR!.!MINOR!.!PATCH!
echo !NEW_VER!>"%VER_FILE%"

:: 只删spec缓存，不删除新exe文件夹
del *.spec /f/q 2>nul

:: ==================== 打包模式选择 ====================
echo ======================================
echo          文洲系统清理大师 打包工具
echo ======================================
echo 【1】标准模式（精简单文件，本机使用）
echo 【2】安全模式（兼容所有电脑，修复Tkinter报错，推荐分发）
echo ======================================
set /p "MODE=请选择打包模式(1/2)："

:: ==================== 执行打包 ====================
if "!MODE!"=="1" (
    echo 正在使用【标准模式】打包...
    pyinstaller -F -w --clean --noupx -y ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=_tkinter ^
    -i "!ICO!" --name "!APP!" ^
    --distpath "!OUT!" ^
    --workpath "!BUILD!" ^
    "!PY!"
)

if "!MODE!"=="2" (
    echo 正在使用【安全模式】打包（完整兼容，无报错）...
    pyinstaller -F -w --clean --noupx -y ^
--exclude-module=_pyi_rth_tkinter ^
--collect-all tkinter ^
--hidden-import=tkinter ^
--hidden-import=tkinter.ttk ^
--hidden-import=_tkinter ^
--hidden-import=requests ^
--hidden-import=psutil ^
-i "!ICO!" --name "!APP!" ^
--distpath "!OUT!" ^
--workpath "!BUILD!" ^
--add-data "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\tcl\tcl8.6;tcl8.6" ^
--add-data "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\tcl\tk8.6;tk8.6" ^
--add-binary "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\DLLs\tcl86t.dll;." ^
--add-binary "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\DLLs\tk86t.dll;." ^
--add-binary "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python312.dll;." ^
"!PY!"
)

:: ==================== 重命名 ====================
ren "%OUT%\%APP%.exe" "%APP%_v%NEW_VER%.exe"

echo ======================================
echo ✅ 打包成功：%APP%_v%NEW_VER%.exe
echo ✅ 版本迭代：%CURRENT_VER% → %NEW_VER%
echo ======================================
if "!MODE!"=="1" echo ✅ 打包模式：标准模式（精简）
if "!MODE!"=="2" echo ✅ 打包模式：安全模式（全兼容，无Tkinter报错）
echo ======================================
explorer "%OUT%"
pause