# -*- coding: utf-8 -*-
"""
Tcl / Tk / tkinter 完整环境检测工具
用于排查 init.tcl 找不到、窗口无法创建、环境错乱问题
"""
import os
import sys
import platform
import traceback

def full_check():
    print("=" * 70)
    print("📌 TCL / TK / TKINTER 完整环境检测")
    print("=" * 70)

    # ====================== 1. 基础信息 ======================
    print("\n【1】系统 & Python 基础信息")
    print(f"操作系统：{platform.system()} {platform.version()}")
    print(f"Python 路径：{sys.executable}")
    print(f"Python 版本：{sys.version}")
    print(f"当前目录：{os.getcwd()}")
    print(f"脚本目录：{os.path.dirname(os.path.abspath(__file__))}")

    # ====================== 2. 环境变量 ======================
    print("\n【2】核心环境变量（Tcl/Tk 依赖）")
    env_list = ["TCL_LIBRARY", "TK_LIBRARY", "PATH", "PYTHONPATH"]
    for key in env_list:
        value = os.environ.get(key, "未设置")
        if key == "PATH":
            value = value[:300] + "..." if len(value) > 300 else value
        print(f"{key:15} : {value}")

    # ====================== 3. 模块导入检测 ======================
    print("\n【3】tkinter 模块加载检测")
    try:
        import tkinter
        print("✅ tkinter 模块导入成功")
    except Exception as e:
        print(f"❌ tkinter 导入失败：{e}")
        traceback.print_exc()

    try:
        import _tkinter
        print(f"✅ _tkinter C 扩展正常")
        print(f"   TCL 版本：{_tkinter.TCL_VERSION}")
        print(f"   TK  版本：{_tkinter.TK_VERSION}")
    except Exception as e:
        print(f"❌ _tkinter 底层依赖损坏：{e}")
        traceback.print_exc()

    # ====================== 4. 窗口创建（最关键！） ======================
    print("\n【4】Tk 窗口初始化（检测 init.tcl）")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.title("测试窗口")
        root.geometry("200x100")
        root.update()
        root.destroy()
        print("🎉🎉🎉 检测结果：Tcl/Tk 环境 100% 完美正常！")
        print("🎉 init.tcl 存在、可读取、无任何问题！")
    except _tkinter.TclError as e:
        print(f"❌ Tcl 错误：{e}")
        print("🔴 原因：路径被篡改 / Python 安装不完整")
        traceback.print_exc()
    except Exception as e:
        print(f"❌ 未知错误：{e}")
        traceback.print_exc()

    # ====================== 5. 自动搜索 init.tcl ======================
    print("\n【5】系统搜索 init.tcl 核心文件")
    search_paths = [
        sys.prefix,
        os.path.join(sys.prefix, "tcl"),
        os.path.join(sys.prefix, "tcl", "tcl8.6"),
        os.path.join(sys.prefix, "Lib", "tcl8.6"),
        os.path.join(os.path.dirname(sys.executable), "tcl"),
        "C:/Python312/tcl/tcl8.6",
        os.path.expandvars("%LOCALAPPDATA%/Programs/Python/Python312/tcl/tcl8.6")
    ]

    found_files = []
    for path in search_paths:
        target_file = os.path.join(path, "init.tcl")
        if os.path.isfile(target_file):
            found_files.append(target_file)

    if found_files:
        for f in found_files:
            print(f"✅ 找到 init.tcl：{f}")
    else:
        print("❌ 未找到 init.tcl！Python 安装损坏！")

    # ====================== 6. 打包环境检测 ======================
    print("\n【6】PyInstaller 打包环境")
    print(f"是否为打包 EXE：{getattr(sys, 'frozen', False)}")
    print(f"临时资源目录：{getattr(sys, '_MEIPASS', '非打包环境')}")

    print("\n" + "=" * 70)
    print("检测完成！按回车键退出")
    print("=" * 70)
    input()

if __name__ == "__main__":
    full_check()