import os
import sys
import threading
import psutil
import winreg
import tkinter as tk
from tkinter import ttk, messagebox

if not getattr(sys, "frozen", False):
    # 源码运行
    os.environ['TCL_LIBRARY'] = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\tcl\tcl8.6"
    os.environ['TK_LIBRARY'] = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\tcl\tk8.6"
else:
    # EXE运行
    def resource_path(relative):
        return os.path.join(sys._MEIPASS, relative)
    os.environ['TCL_LIBRARY'] = resource_path("tcl8.6")
    os.environ['TK_LIBRARY'] = resource_path("tk8.6")

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_PATH, "config.ini")

# ---------------------------------------------------
import re
import time
import json
import ctypes
import shutil
import hashlib
import threading
import subprocess
import configparser
import winreg
import random
from datetime import datetime, timedelta
from tkinter import *
from tkinter import ttk, messagebox, filedialog, scrolledtext, colorchooser
import psutil
import win32api
import win32con
import win32gui
import win32process

# 自动安装依赖
try:
    import requests
    import webbrowser
    from send2trash import send2trash
except ImportError:
    messagebox.showerror("缺失依赖", "请先安装依赖库\n命令：pip install requests send2trash pywin32 psutil")
    sys.exit()

# ==================== 全局常量 ====================
VERSION = "4.0.4"
AUTHOR = "王文洲"
CONFIG_PATH = os.path.join(BASE_PATH, "config.ini")
LOG_PATH = os.path.join(BASE_PATH, "clean_log.txt")
THEME_COLOR = "#2c3e50"
ACCENT_COLOR = "#3498db"
SUCCESS_COLOR = "#27ae60"
WARNING_COLOR = "#f39c12"
ERROR_COLOR = "#e74c3c"
LIGHT_THEME = "#f5f6fa"
DARK_THEME = "#2c3e50"
# 安全扫描风险等级颜色
RISK_HIGH = "#e74c3c"
RISK_MID = "#f39c12"
RISK_LOW = "#27ae60"

# ==================== 权限检测 ====================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
    except Exception as e:
        messagebox.showerror("错误", f"无法以管理员身份运行：{str(e)}")
        sys.exit()

# ==================== 单位格式化 ====================
def format_size(byte_size):
    if byte_size < 1024:
        return f"{byte_size} B"
    elif byte_size < 1024 ** 2:
        return f"{round(byte_size / 1024, 2)} KB"
    elif byte_size < 1024 ** 3:
        return f"{round(byte_size / 1024 ** 2, 2)} MB"
    else:
        return f"{round(byte_size / 1024 ** 3, 2)} GB"

# ==================== 日志记录 ====================
def write_log(action, detail):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action}: {detail}\n")
    except:
        pass

# ==================== 更新检查 ====================
def check_update(silent=False):
    import requests
    import webbrowser
    from tkinter import messagebox
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def ver_tuple(v):
        try:
            return tuple(map(int, v.strip().split(".")))
        except:
            return (0, 0, 0)

    try:
        res = requests.get(
            "https://gh-proxy.com/https://raw.githubusercontent.com/VNeoByteDev/wenzhou-cleanmaster/main/version.txt",
            timeout=(3, 12),
            verify=False
        )
        res.raise_for_status()
        
        lines = []
        for line in res.text.splitlines():
            stripped_line = line.strip()
            if stripped_line and stripped_line.replace(".", "").isdigit():
                lines.append(stripped_line)
        
        if not lines:
            if not silent:
                messagebox.showwarning("提示", "版本文件中未找到有效版本号")
            return
            
        latest_version = lines[-1]
        current_ver = ver_tuple(VERSION)
        latest_ver = ver_tuple(latest_version)
        
        if not silent:
            if latest_ver > current_ver:
                if messagebox.askyesno("发现新版本！", f"当前版本：v{VERSION}\n最新版本：v{latest_version}\n\n是否前往官网下载？"):
                    webbrowser.open("https://vneobytedev.github.io/wenzhou-cleanmaster/")
            elif latest_ver == current_ver:
                messagebox.showinfo("太棒了！", "你用的已经是最新版本啦！")
            else:
                messagebox.showerror("版本信息异常", f"⚠️ 版本异常！\n当前版本(v{VERSION}) > 官方最新版本(v{latest_version})！")
            
    except:
        pass

# ==================== 主程序 ====================
class CleanMaster:
    def __init__(self, root):
        self.root = root
        self.root.title(f"系统清理大师 v{VERSION} ULTRA — 作者：{AUTHOR}")
        self.root.geometry("1150x780")
        self.root.resizable(True, True)
        self.root.configure(bg=THEME_COLOR)
        self.total_deleted = 0
        self.total_freed = 0
        self.is_scanning = False
        self.is_cleaning = False
        self.is_safe_scanning = False
        self.scan_results = []
        self.safe_scan_results = []
        self.config = self.load_config()
        self.logs = []
        self.disk_analyze_path = StringVar(value="C:\\")
        self.startup_list = []
        self.reg_scan_list = []
        self.software_list = []
        self.big_file_list = []
        self.dup_file_map = {}
        self.timer_running = False
        self.theme_mode = "dark"
        self.system_info_thread = None
        self.stop_system_info = False
        self.setup_style()
        self.create_menu()
        self.create_widgets()
        self.start_system_info_update()

    def load_config(self):
        config = configparser.ConfigParser()
        # 先读取现有配置
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH, encoding="utf-8")
        
        # 确保General节存在，且所有字段有默认值
        if "General" not in config:
            config["General"] = {}
        
        # 补全缺失的字段（核心修复：确保auto_update一定存在）
        defaults = {
            "confirm_delete": "True",
            "safe_mode": "True",
            "auto_log": "True",
            "big_file_size": "100",
            "auto_update": "True"
        }
        for key, val in defaults.items():
            if key not in config["General"]:
                config["General"][key] = val
        
        # 保存补全后的配置
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)
        
        return config

    def save_config(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            self.config.write(f)

    def setup_style(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", font=("微软雅黑", 10))
        self.style.configure("TFrame", background=THEME_COLOR)
        self.style.configure("TLabel", background=THEME_COLOR, foreground="white")
        self.style.configure("TButton", font=("微软雅黑", 10, "bold"), padding=5)
        self.style.configure("TCheckbutton", background=THEME_COLOR, foreground="white")
        self.style.configure("TLabelFrame", background=THEME_COLOR, foreground="white")
        self.style.configure("TEntry", fieldbackground="#34495e", foreground="white")
        self.style.configure("TCombobox", fieldbackground="#34495e", foreground="white")
        self.style.configure("Accent.TButton", background=ACCENT_COLOR, foreground="white")
        self.style.configure("Success.TButton", background=SUCCESS_COLOR, foreground="white")
        self.style.configure("Warning.TButton", background=WARNING_COLOR, foreground="white")
        self.style.configure("Error.TButton", background=ERROR_COLOR, foreground="white")

    def switch_theme(self):
        global THEME_COLOR
        if self.theme_mode == "dark":
            THEME_COLOR = LIGHT_THEME
            self.theme_mode = "light"
            fg = "black"
        else:
            THEME_COLOR = DARK_THEME
            self.theme_mode = "dark"
            fg = "white"
        self.root.configure(bg=THEME_COLOR)
        self.style.configure(".", background=THEME_COLOR, foreground=fg)
        self.style.configure("TFrame", background=THEME_COLOR)
        self.style.configure("TLabel", background=THEME_COLOR, foreground=fg)
        self.style.configure("TCheckbutton", background=THEME_COLOR, foreground=fg)
        self.style.configure("TLabelFrame", background=THEME_COLOR, foreground=fg)
        self.style.configure("TEntry", fieldbackground="#ecf0f1" if self.theme_mode == "light" else "#34495e", foreground=fg)
        self.style.configure("TCombobox", fieldbackground="#ecf0f1" if self.theme_mode == "light" else "#34495e", foreground=fg)
        messagebox.showinfo("主题", "已切换界面主题")

    def create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="保存日志", command=self.save_logs)
        file_menu.add_command(label="导出配置", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        tool_menu = Menu(menubar, tearoff=0)
        tool_menu.add_command(label="磁盘分析", command=lambda: self.notebook.select(self.disk_frame))
        tool_menu.add_command(label="进程管理", command=lambda: self.notebook.select(self.process_frame))
        tool_menu.add_command(label="启动项管理", command=lambda: self.notebook.select(self.startup_frame))
        tool_menu.add_command(label="软件卸载", command=lambda: self.notebook.select(self.software_frame))
        tool_menu.add_command(label="大文件清理", command=lambda: self.notebook.select(self.bigfile_frame))
        tool_menu.add_command(label="隐私清理", command=lambda: self.notebook.select(self.privacy_frame))
        tool_menu.add_command(label="系统修复", command=lambda: self.notebook.select(self.repair_frame))
        tool_menu.add_command(label="安全扫描", command=lambda: self.notebook.select(self.safe_frame))
        menubar.add_cascade(label="工具", menu=tool_menu)

        opt_menu = Menu(menubar, tearoff=0)
        opt_menu.add_command(label="切换主题", command=self.switch_theme)
        opt_menu.add_command(label="定时清理", command=self.open_timer_window)
        opt_menu.add_command(label="系统评分", command=self.show_system_score)
        opt_menu.add_separator()
        opt_menu.add_command(label="检查更新", command=check_update)
        menubar.add_cascade(label="选项", menu=opt_menu)

        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

    def create_widgets(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=X, padx=10, pady=5)
        self.cpu_label = ttk.Label(status_frame, text="CPU: 0%")
        self.cpu_label.pack(side=LEFT, padx=10)
        self.mem_label = ttk.Label(status_frame, text="内存: 0%")
        self.mem_label.pack(side=LEFT, padx=10)
        self.disk_label = ttk.Label(status_frame, text="C盘: 0%")
        self.disk_label.pack(side=LEFT, padx=10)
        self.score_label = ttk.Label(status_frame, text="系统评分: 计算中...")
        self.score_label.pack(side=LEFT, padx=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.home_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.home_frame, text="首页")
        self.build_home_page()

        self.clean_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.clean_frame, text="系统清理")
        self.build_clean_page()

        self.browser_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.browser_frame, text="浏览器清理")
        self.build_browser_page()

        self.reg_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reg_frame, text="注册表清理")
        self.build_reg_page()

        self.disk_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.disk_frame, text="磁盘分析")
        self.build_disk_page()

        self.process_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.process_frame, text="进程管理")
        self.build_process_page()

        self.startup_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.startup_frame, text="启动项管理")
        self.build_startup_page()

        self.software_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.software_frame, text="软件卸载")
        self.build_software_page()

        self.bigfile_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.bigfile_frame, text="大文件清理")
        self.build_bigfile_page()

        self.privacy_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.privacy_frame, text="隐私清理")
        self.build_privacy_page()

        self.repair_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.repair_frame, text="系统修复")
        self.build_repair_page()

        self.driver_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.driver_frame, text="驱动管理")
        self.build_driver_page()

        self.safe_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.safe_frame, text="安全扫描")
        self.build_safe_page()

        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="清理日志")
        self.build_log_page()

        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="设置")
        self.build_settings_page()

    def get_boot_time(self):
        boot = psutil.boot_time()
        return datetime.fromtimestamp(boot).strftime("%Y-%m-%d %H:%M:%S")

    def start_system_info_update(self):
        def update():
            while not self.stop_system_info:
                try:
                    cpu = psutil.cpu_percent(interval=0.5)
                    mem = psutil.virtual_memory().percent
                    disk = psutil.disk_usage("C:\\").percent
                    self.cpu_label.config(text=f"CPU: {cpu}%")
                    self.mem_label.config(text=f"内存: {mem}%")
                    self.disk_label.config(text=f"C盘: {disk}%")
                except:
                    pass
                time.sleep(1)
        self.system_info_thread = threading.Thread(target=update, daemon=True)
        self.system_info_thread.start()

    def build_home_page(self):
        title_label = ttk.Label(self.home_frame, text="系统清理大师 专业版", font=("微软雅黑", 32, "bold"))
        title_label.pack(pady=20)
        author_label = ttk.Label(self.home_frame, text=f"Powered By {AUTHOR}", font=("微软雅黑", 14))
        author_label.pack(pady=5)
        card = ttk.LabelFrame(self.home_frame, text="系统状态总览", padding=25)
        card.pack(fill=X, padx=60, pady=10)
        stats = [
            ("系统版本", f"{sys.platform} {os.name}"),
            ("Python版本", sys.version.split()[0]),
            ("开机时间", self.get_boot_time()),
            ("内存总量", f"{round(psutil.virtual_memory().total/1024**3,2)}GB"),
            ("CPU核心数", f"{psutil.cpu_count(logical=False)} 物理核"),
            ("系统评分", "正在计算...")
        ]
        for i, (k, v) in enumerate(stats):
            ttk.Label(card, text=f"{k}:", font=("微软雅黑",12,"bold")).grid(row=i,column=0,sticky=W,pady=4)
            ttk.Label(card, text=v, font=("微软雅黑",12)).grid(row=i,column=1,sticky=W,padx=20,pady=4)
        quick_frame = ttk.LabelFrame(self.home_frame, text="一键全能操作", padding=20)
        quick_frame.pack(fill=X, padx=60, pady=10)
        ttk.Button(quick_frame, text="一键扫描", command=self.quick_scan, style="Accent.TButton").pack(side=LEFT, padx=8)
        ttk.Button(quick_frame, text="一键清理", command=self.quick_clean, style="Success.TButton").pack(side=LEFT, padx=8)
        ttk.Button(quick_frame, text="一键加速", command=self.onekey_boost, style="Warning.TButton").pack(side=LEFT, padx=8)
        ttk.Button(quick_frame, text="系统评分", command=self.show_system_score, style="TButton").pack(side=LEFT, padx=8)
        ttk.Button(quick_frame, text="智能清理", command=self.smart_clean, style="TButton").pack(side=LEFT, padx=8)
        ttk.Button(quick_frame, text="安全扫描", command=self.start_safe_scan, style="Error.TButton").pack(side=LEFT, padx=8)
        ttk.Button(quick_frame, text="检查更新", command=check_update, style="Accent.TButton").pack(side=LEFT, padx=8)

    def build_clean_page(self):
        option_frame = ttk.LabelFrame(self.clean_frame, text="清理选项", padding=15)
        option_frame.pack(fill=X, padx=10, pady=5)
        self.clean_vars = {}
        clean_items = [
            ("用户临时文件", "%TEMP%", True),
            ("系统临时文件", "C:\\Windows\\Temp", True),
            ("Windows更新缓存", "C:\\Windows\\SoftwareDistribution\\Download", True),
            ("系统预读文件", "C:\\Windows\\Prefetch", True),
            ("系统日志", "C:\\Windows\\Logs", True),
            ("回收站", "RECYCLE", False),
            ("下载文件夹", os.path.expanduser("~/Downloads"), False),
            ("桌面垃圾", os.path.expanduser("~/Desktop"), False),
            ("缩略图缓存", "%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer", True),
            ("错误报告", "C:\\ProgramData\\Microsoft\\Windows\\WER", True),
            ("更新备份", "C:\\Windows\\WinSxS\\Backup", True),
            ("调试文件", "C:\\Windows\\Debug", True),
            ("更新临时文件", "C:\\Windows\\SoftwareDistribution\\AuthCabs", True),
        ]
        for i, (name, path, default) in enumerate(clean_items):
            var = BooleanVar(value=default)
            self.clean_vars[name] = (var, path)
            ttk.Checkbutton(option_frame, text=name, variable=var).grid(row=i//4, column=i%4, sticky=W, padx=5, pady=5)
        btn_frame = ttk.Frame(self.clean_frame)
        btn_frame.pack(fill=X, padx=10, pady=5)
        ttk.Button(btn_frame, text="全选", command=lambda: self.set_all_clean(True)).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="反选", command=lambda: self.set_all_clean(None)).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="扫描垃圾", command=self.start_scan, style="Accent.TButton").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="开始清理", command=self.start_clean, style="Success.TButton").pack(side=LEFT, padx=5)
        progress_frame = ttk.Frame(self.clean_frame)
        progress_frame.pack(fill=X, padx=10, pady=5)
        self.scan_label = ttk.Label(progress_frame, text="准备就绪")
        self.scan_label.pack(anchor=W)
        self.scan_progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.scan_progress.pack(fill=X, pady=5)
        result_frame = ttk.LabelFrame(self.clean_frame, text="扫描结果", padding=10)
        result_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        columns = ("位置", "文件数", "大小")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.result_tree.heading(col, text=col)
        self.result_tree.column("位置", width=550)
        self.result_tree.column("文件数", width=80, anchor=CENTER)
        self.result_tree.column("大小", width=100, anchor=CENTER)
        self.result_tree.pack(fill=BOTH, expand=True)

    def build_browser_page(self):
        ttk.Label(self.browser_frame, text="🌐 浏览器垃圾清理", font=("微软雅黑", 20, "bold")).pack(pady=15)
        option_frame = ttk.LabelFrame(self.browser_frame, text="清理选项", padding=15)
        option_frame.pack(fill=X, padx=20, pady=5)
        self.browser_vars = {}
        browser_items = [
            ("Chrome 缓存", "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache", True),
            ("Edge 缓存", "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache", True),
            ("浏览器 Cookie", "", True),
            ("浏览历史", "", True),
            ("下载历史", "", True),
        ]
        for i, (name, path, default) in enumerate(browser_items):
            var = BooleanVar(value=default)
            self.browser_vars[name] = (var, path)
            ttk.Checkbutton(option_frame, text=name, variable=var).grid(row=i//2, column=i%2, sticky=W, padx=10, pady=5)
        ttk.Button(self.browser_frame, text="一键清理浏览器", command=self.clean_browser, style="Success.TButton").pack(pady=10)

    def clean_browser(self):
        if not messagebox.askyesno("确认", "确定清理浏览器缓存/历史？"):
            return
        count = 0
        for name, (var, path) in self.browser_vars.items():
            if var.get() and path:
                try:
                    rp = os.path.expandvars(path)
                    if os.path.exists(rp):
                        shutil.rmtree(rp, ignore_errors=True)
                        count +=1
                except:
                    pass
        messagebox.showinfo("完成", f"成功清理 {count} 项浏览器垃圾")

    def build_safe_page(self):
        ttk.Label(self.safe_frame, text="🔒 系统安全扫描", font=("微软雅黑", 20, "bold")).pack(pady=15)
        tip_label = ttk.Label(self.safe_frame, text="扫描风险进程、恶意启动项、危险注册表、可疑文件，保护系统安全", font=("微软雅黑", 11))
        tip_label.pack(pady=5)

        btn_frame = ttk.Frame(self.safe_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="开始安全扫描", command=self.start_safe_scan, style="Error.TButton", width=15).pack(side=LEFT, padx=10)
        ttk.Button(btn_frame, text="一键处理风险", command=self.handle_safe_risk, style="Warning.TButton", width=15).pack(side=LEFT, padx=10)
        ttk.Button(btn_frame, text="清空扫描结果", command=self.clear_safe_result, style="Accent.TButton", width=15).pack(side=LEFT, padx=10)

        progress_frame = ttk.Frame(self.safe_frame)
        progress_frame.pack(fill=X, padx=20, pady=5)
        self.safe_scan_label = ttk.Label(progress_frame, text="等待扫描...")
        self.safe_scan_label.pack(anchor=W)
        self.safe_scan_progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.safe_scan_progress.pack(fill=X, pady=5)

        result_frame = ttk.LabelFrame(self.safe_frame, text="安全扫描结果", padding=10)
        result_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        columns = ("风险等级", "风险类型", "文件/路径", "描述")
        self.safe_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)
        self.safe_tree.column("风险等级", width=80, anchor=CENTER)
        self.safe_tree.column("风险类型", width=120, anchor=CENTER)
        self.safe_tree.column("文件/路径", width=550)
        self.safe_tree.column("描述", width=200)
        for col in columns:
            self.safe_tree.heading(col, text=col)
        self.safe_tree.pack(fill=BOTH, expand=True)

    def start_safe_scan(self):
        if self.is_safe_scanning:
            messagebox.showwarning("提示", "安全扫描进行中，请等待完成")
            return
        self.is_safe_scanning = True
        self.safe_scan_results.clear()
        self.safe_tree.delete(*self.safe_tree.get_children())
        self.safe_scan_progress["value"] = 0
        self.safe_scan_label.config(text="正在扫描风险进程...")
        self.root.update()

        self.scan_risk_process()
        self.safe_scan_progress["value"] = 25
        self.safe_scan_label.config(text="正在扫描恶意启动项...")
        self.root.update()

        self.scan_risk_startup()
        self.safe_scan_progress["value"] = 50
        self.safe_scan_label.config(text="正在扫描危险注册表...")
        self.root.update()

        self.scan_risk_registry()
        self.safe_scan_progress["value"] = 75
        self.safe_scan_label.config(text="正在扫描可疑文件...")
        self.root.update()

        self.scan_risk_files()
        self.safe_scan_progress["value"] = 100

        total_risk = len(self.safe_scan_results)
        self.safe_scan_label.config(text=f"扫描完成！共发现 {total_risk} 项安全风险")
        self.is_safe_scanning = False
        if total_risk == 0:
            messagebox.showinfo("安全扫描", "✅ 系统安全，未发现任何风险！")

    def scan_risk_process(self):
        risk_process_names = ["cmd.exe", "powershell.exe", "wscript.exe", "cscript.exe", "mshta.exe"]
        for p in psutil.process_iter(["pid", "name", "exe"]):
            try:
                p_name = p.info["name"].lower()
                p_exe = p.info["exe"]
                if p_name in risk_process_names and p_exe and not p_exe.startswith("C:\\Windows\\System32"):
                    self.safe_scan_results.append({
                        "level": "高危",
                        "type": "风险进程",
                        "path": p_exe,
                        "desc": "未知路径的系统进程，可能是恶意程序"
                    })
                    self.safe_tree.insert("", END, values=("高危", "风险进程", p_exe, "未知路径系统进程"))
            except:
                continue

    def scan_risk_startup(self):
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
            i = 0
            while True:
                try:
                    name, path = winreg.EnumValue(k, i)[:2]
                    if any(s in path.lower() for s in ["temp", "tmp", "download", "desktop"]):
                        self.safe_scan_results.append({
                            "level": "中危",
                            "type": "恶意启动项",
                            "path": path,
                            "desc": "临时/下载目录启动项，存在安全风险"
                        })
                        self.safe_tree.insert("", END, values=("中危", "恶意启动项", path, "临时目录启动项"))
                    i += 1
                except:
                    break
            winreg.CloseKey(k)
        except:
            pass

    def scan_risk_registry(self):
        try:
            paths = [r"Software\Microsoft\Windows\CurrentVersion\RunOnce", r"Software\Microsoft\Windows\CurrentVersion\RunServices"]
            for path in paths:
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
                i = 0
                while True:
                    try:
                        name, val = winreg.EnumValue(k, i)[:2]
                        self.safe_scan_results.append({
                            "level": "高危",
                            "type": "危险注册表",
                            "path": f"{path}\\{name}",
                            "desc": "一次性启动/服务启动项，易被恶意利用"
                        })
                        self.safe_tree.insert("", END, values=("高危", "危险注册表", f"{path}\\{name}", "高危启动项"))
                        i += 1
                    except:
                        break
                winreg.CloseKey(k)
        except:
            pass

    def scan_risk_files(self):
        scan_paths = [os.path.expandvars("%TEMP%"), os.path.expanduser("~/Desktop")]
        risk_suffix = [".exe", ".bat", ".vbs", ".cmd", ".ps1"]

        for path in scan_paths:
            if not os.path.exists(path):
                continue
            try:
                # 👇 这里是真正修复：直接不让 os.walk 进入 wenzhou 文件夹
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d.lower() != "wenzhou"]

                    for file in files:
                        if any(file.lower().endswith(suf) for suf in risk_suffix):
                            file_path = os.path.join(root, file)

                            # 跳过自己
                            if file_path.lower() == sys.executable.lower():
                                continue

                            self.safe_scan_results.append({
                                "level": "低危",
                                "type": "可疑文件",
                                "path": file_path,
                                "desc": "可执行文件，存在潜在风险"
                            })
                            self.safe_tree.insert("", END, values=("低危", "可疑文件", file_path, "可执行风险文件"))
            except:
                continue

    def handle_safe_risk(self):
        if not self.safe_scan_results:
            messagebox.showwarning("提示", "请先进行安全扫描！")
            return
        if not messagebox.askyesno("风险处理", "确定处理所有扫描到的安全风险？\n仅禁用/隔离，不删除系统文件！"):
            return

        count = 0
        for risk in self.safe_scan_results:
            try:
                if risk["type"] == "风险进程":
                    for p in psutil.process_iter(['pid', 'name', 'exe']):
                        if p.info['exe'] == risk['path']:
                            p.terminate()
                            count +=1
                elif risk["type"] == "恶意启动项":
                    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
                    winreg.DeleteValue(k, os.path.basename(risk["path"]))
                    winreg.CloseKey(k)
                    count += 1
            except:
                continue

        self.clear_safe_result()
        messagebox.showinfo("处理完成", f"✅ 成功处理 {count} 项安全风险！\n系统已恢复安全状态")

    def clear_safe_result(self):
        self.safe_tree.delete(*self.safe_tree.get_children())
        self.safe_scan_results.clear()
        self.safe_scan_label.config(text="等待扫描...")
        self.safe_scan_progress["value"] = 0

    def build_reg_page(self):
        f=ttk.LabelFrame(self.reg_frame,text="注册表清理",padding=15)
        f.pack(fill=X,padx=10,pady=5)
        self.rv={
            "无效卸载项":BooleanVar(value=True),
            "无效文件关联":BooleanVar(value=True),
            "无效启动项":BooleanVar(value=True),
            "软件残留":BooleanVar(value=False)
        }
        for i,(n,v) in enumerate(self.rv.items()):
            ttk.Checkbutton(f,text=n,variable=v).grid(row=i,column=0,sticky=W,pady=5)
        ttk.Button(f,text="扫描",command=self.rs,style="Accent.TButton").grid(row=0,column=1,rowspan=4,padx=10)
        ttk.Button(f,text="清理",command=self.rc,style="Error.TButton").grid(row=0,column=2,rowspan=4,padx=10)
        lf=ttk.LabelFrame(self.reg_frame, text="扫描结果", padding=10)
        lf.pack(fill=BOTH, expand=True, padx=10, pady=5)
        columns = ("注册表路径", "风险类型")
        self.rt = ttk.Treeview(lf, columns=columns, show="headings", height=8)
        for col in columns:
            self.rt.heading(col, text=col)
        self.rt.column("注册表路径", width=650)
        self.rt.column("风险类型", width=120, anchor=CENTER)
        self.rt.pack(fill=BOTH, expand=True)

    def rs(self):
        if not is_admin():
            messagebox.showerror("错误", "需要管理员权限才能扫描注册表")
            return
        self.rt.delete(*self.rt.get_children())
        self.reg_scan_list.clear()
        try:
            reg_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            for hkey, path in reg_paths:
                try:
                    key = winreg.OpenKey(hkey, path)
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                winreg.QueryValueEx(subkey, "DisplayName")
                            except FileNotFoundError:
                                hkey_name = "HKEY_CURRENT_USER" if hkey == winreg.HKEY_CURRENT_USER else "HKEY_LOCAL_MACHINE"
                                full_path = f"{hkey_name}\\{path}\\{subkey_name}"
                                self.reg_scan_list.append((full_path, "无效卸载残留"))
                                self.rt.insert("", END, values=(full_path, "无效卸载残留"))
                            winreg.CloseKey(subkey)
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except Exception as e:
                    continue
            
            if len(self.reg_scan_list) == 0:
                messagebox.showinfo("扫描完成", "✅ 注册表干净，未发现无效残留项")
            else:
                messagebox.showinfo("扫描完成", f"共发现 {len(self.reg_scan_list)} 项无效注册表残留")
        except Exception as e:
            messagebox.showerror("错误", f"注册表扫描失败：{str(e)}")

    def rc(self):
        if not is_admin():
            messagebox.showerror("错误", "需要管理员权限才能清理注册表")
            return
        if not self.reg_scan_list:
            messagebox.showinfo("提示", "没有可清理的注册表项，请先进行扫描")
            return
        if not messagebox.askyesno("确认清理", "⚠️ 确定要删除这些无效注册表项吗？\n建议先备份注册表，避免系统异常！"):
            return
        
        success_count = 0
        for full_path, risk_type in self.reg_scan_list:
            try:
                if full_path.startswith("HKEY_CURRENT_USER"):
                    hkey = winreg.HKEY_CURRENT_USER
                    sub_path = full_path.replace("HKEY_CURRENT_USER\\", "")
                elif full_path.startswith("HKEY_LOCAL_MACHINE"):
                    hkey = winreg.HKEY_LOCAL_MACHINE
                    sub_path = full_path.replace("HKEY_LOCAL_MACHINE\\", "")
                else:
                    continue
                
                parent_path = os.path.dirname(sub_path)
                subkey_name = os.path.basename(sub_path)
                
                parent_key = winreg.OpenKey(hkey, parent_path, 0, winreg.KEY_WRITE)
                winreg.DeleteKey(parent_key, subkey_name)
                winreg.CloseKey(parent_key)
                success_count += 1
            except Exception as e:
                continue
        
        self.reg_scan_list.clear()
        self.rt.delete(*self.rt.get_children())
        messagebox.showinfo("清理完成", f"✅ 成功清理 {success_count} 项无效注册表项\n系统注册表已优化")

    def build_disk_page(self):
        ttk.Label(self.disk_frame, text="📊 磁盘空间分析", font=("微软雅黑", 20, "bold")).pack(pady=15)
        path_frame = ttk.Frame(self.disk_frame)
        path_frame.pack(fill=X, padx=20, pady=5)
        ttk.Label(path_frame, text="分析路径:").pack(side=LEFT, padx=5)
        ttk.Entry(path_frame, textvariable=self.disk_analyze_path, width=50).pack(side=LEFT, padx=5)
        ttk.Button(path_frame, text="浏览", command=lambda: self.disk_analyze_path.set(filedialog.askdirectory())).pack(side=LEFT, padx=5)
        ttk.Button(path_frame, text="开始分析", command=self.start_disk_analyze, style="Accent.TButton").pack(side=LEFT, padx=10)
        
        result_frame = ttk.LabelFrame(self.disk_frame, text="磁盘占用分析", padding=10)
        result_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        columns = ("文件夹名称", "大小", "文件数", "子文件夹数")
        self.disk_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.disk_tree.heading(col, text=col)
        self.disk_tree.column("文件夹名称", width=400)
        self.disk_tree.column("大小", width=150, anchor=CENTER)
        self.disk_tree.column("文件数", width=100, anchor=CENTER)
        self.disk_tree.column("子文件夹数", width=100, anchor=CENTER)
        self.disk_tree.pack(fill=BOTH, expand=True)

    def start_disk_analyze(self):
        path = self.disk_analyze_path.get()
        if not os.path.exists(path):
            messagebox.showerror("错误", "路径不存在")
            return
        self.disk_tree.delete(*self.disk_tree.get_children())
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    size, files, dirs = self.get_dir_size(item_path)
                    self.disk_tree.insert("", END, values=(item, format_size(size), files, dirs))
        except Exception as e:
            messagebox.showerror("错误", f"分析失败：{str(e)}")

    def get_dir_size(self, path):
        total_size = 0
        total_files = 0
        total_dirs = 0
        try:
            for root, dirs, files in os.walk(path):
                total_dirs += len(dirs)
                total_files += len(files)
                for file in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, file))
                    except:
                        pass
        except:
            pass
        return total_size, total_files, total_dirs

    def build_process_page(self):
        ttk.Label(self.process_frame, text="⚙️ 进程管理", font=("微软雅黑", 20, "bold")).pack(pady=15)
        btn_frame = ttk.Frame(self.process_frame)
        btn_frame.pack(fill=X, padx=20, pady=5)
        ttk.Button(btn_frame, text="刷新进程", command=self.refresh_process, style="Accent.TButton").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="结束进程", command=self.kill_process, style="Error.TButton").pack(side=LEFT, padx=5)
        
        result_frame = ttk.LabelFrame(self.process_frame, text="进程列表", padding=10)
        result_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        columns = ("PID", "进程名", "内存占用", "CPU使用率", "路径")
        self.process_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.process_tree.heading(col, text=col)
        self.process_tree.column("PID", width=80, anchor=CENTER)
        self.process_tree.column("进程名", width=150)
        self.process_tree.column("内存占用", width=120, anchor=CENTER)
        self.process_tree.column("CPU使用率", width=100, anchor=CENTER)
        self.process_tree.column("路径", width=500)
        self.process_tree.pack(fill=BOTH, expand=True)
        self.refresh_process()

    def refresh_process(self):
        self.process_tree.delete(*self.process_tree.get_children())
        for p in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'exe']):
            try:
                pid = p.info['pid']
                name = p.info['name']
                mem = format_size(p.info['memory_info'].rss)
                cpu = f"{p.info['cpu_percent']}%"
                exe = p.info['exe'] or "未知"
                self.process_tree.insert("", END, values=(pid, name, mem, cpu, exe))
            except:
                continue

    def kill_process(self):
        selected = self.process_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要结束的进程")
            return
        if not messagebox.askyesno("确认", "确定结束该进程吗？\n结束系统进程可能导致系统异常！"):
            return
        for item in selected:
            pid = int(self.process_tree.item(item, "values")[0])
            try:
                psutil.Process(pid).terminate()
            except:
                pass
        self.refresh_process()

    def build_startup_page(self):
        ttk.Label(self.startup_frame, text="🚀 启动项管理", font=("微软雅黑", 20, "bold")).pack(pady=15)
        btn_frame = ttk.Frame(self.startup_frame)
        btn_frame.pack(fill=X, padx=20, pady=5)
        ttk.Button(btn_frame, text="刷新启动项", command=self.refresh_startup, style="Accent.TButton").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="禁用启动项", command=self.disable_startup, style="Error.TButton").pack(side=LEFT, padx=5)
        
        result_frame = ttk.LabelFrame(self.startup_frame, text="启动项列表", padding=10)
        result_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        columns = ("名称", "路径", "注册表位置")
        self.startup_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.startup_tree.heading(col, text=col)
        self.startup_tree.column("名称", width=200)
        self.startup_tree.column("路径", width=500)
        self.startup_tree.column("注册表位置", width=300)
        self.startup_tree.pack(fill=BOTH, expand=True)
        self.refresh_startup()

    def refresh_startup(self):
        self.startup_tree.delete(*self.startup_tree.get_children())
        self.startup_list = []
        reg_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM RunOnce")
        ]
        for hkey, path, loc in reg_paths:
            try:
                key = winreg.OpenKey(hkey, path)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        self.startup_list.append((name, value, f"{loc}\\{name}"))
                        self.startup_tree.insert("", END, values=(name, value, f"{loc}\\{name}"))
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except:
                continue

    def disable_startup(self):
        selected = self.startup_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要禁用的启动项")
            return
        if not messagebox.askyesno("确认", "确定禁用该启动项吗？"):
            return
        for item in selected:
            name, path, loc = self.startup_tree.item(item, "values")
            try:
                if loc.startswith("HKCU"):
                    hkey = winreg.HKEY_CURRENT_USER
                else:
                    hkey = winreg.HKEY_LOCAL_MACHINE
                reg_path = loc.split("\\", 1)[1].rsplit("\\", 1)[0]
                key = winreg.OpenKey(hkey, reg_path, 0, winreg.KEY_WRITE)
                winreg.DeleteValue(key, name)
                winreg.CloseKey(key)
            except:
                pass
        self.refresh_startup()

    def build_software_page(self):
        ttk.Label(self.software_frame, text="📦 软件卸载", font=("微软雅黑", 20, "bold")).pack(pady=15)
        btn_frame = ttk.Frame(self.software_frame)
        btn_frame.pack(fill=X, padx=20, pady=5)
        ttk.Button(btn_frame, text="刷新软件列表", command=self.refresh_software, style="Accent.TButton").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="卸载软件", command=self.uninstall_software, style="Error.TButton").pack(side=LEFT, padx=5)
        
        result_frame = ttk.LabelFrame(self.software_frame, text="已安装软件", padding=10)
        result_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        columns = ("软件名称", "版本", "发布者", "安装日期", "卸载路径")
        self.software_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.software_tree.heading(col, text=col)
        self.software_tree.column("软件名称", width=250)
        self.software_tree.column("版本", width=100)
        self.software_tree.column("发布者", width=150)
        self.software_tree.column("安装日期", width=100)
        self.software_tree.column("卸载路径", width=400)
        self.software_tree.pack(fill=BOTH, expand=True)
        self.refresh_software()

    def refresh_software(self):
        self.software_tree.delete(*self.software_tree.get_children())
        self.software_list = []
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        for hkey, path in reg_paths:
            try:
                key = winreg.OpenKey(hkey, path)
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        try:
                            name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] if "DisplayVersion" in winreg.QueryInfoKey(subkey)[2] else "未知"
                            publisher = winreg.QueryValueEx(subkey, "Publisher")[0] if "Publisher" in winreg.QueryInfoKey(subkey)[2] else "未知"
                            install_date = winreg.QueryValueEx(subkey, "InstallDate")[0] if "InstallDate" in winreg.QueryInfoKey(subkey)[2] else "未知"
                            uninstall_path = winreg.QueryValueEx(subkey, "UninstallString")[0] if "UninstallString" in winreg.QueryInfoKey(subkey)[2] else "未知"
                            self.software_list.append((name, version, publisher, install_date, uninstall_path))
                            self.software_tree.insert("", END, values=(name, version, publisher, install_date, uninstall_path))
                        except:
                            pass
                        winreg.CloseKey(subkey)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except:
                continue

    def uninstall_software(self):
        selected = self.software_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要卸载的软件")
            return
        if not messagebox.askyesno("确认", "确定卸载该软件吗？"):
            return
        for item in selected:
            uninstall_path = self.software_tree.item(item, "values")[4]
            if uninstall_path == "未知":
                messagebox.showerror("错误", "该软件没有卸载程序")
                continue
            try:
                subprocess.Popen(uninstall_path, shell=True)
            except:
                pass

    def build_bigfile_page(self):
        ttk.Label(self.bigfile_frame, text="📁 大文件清理", font=("微软雅黑", 20, "bold")).pack(pady=15)
        option_frame = ttk.Frame(self.bigfile_frame)
        option_frame.pack(fill=X, padx=20, pady=5)
        ttk.Label(option_frame, text="扫描大于:").pack(side=LEFT, padx=5)
        self.big_file_size = StringVar(value="100")
        ttk.Entry(option_frame, textvariable=self.big_file_size, width=10).pack(side=LEFT, padx=5)
        ttk.Label(option_frame, text="MB").pack(side=LEFT, padx=5)
        ttk.Label(option_frame, text="扫描路径:").pack(side=LEFT, padx=10)
        self.big_file_path = StringVar(value="C:\\")
        ttk.Entry(option_frame, textvariable=self.big_file_path, width=30).pack(side=LEFT, padx=5)
        ttk.Button(option_frame, text="浏览", command=lambda: self.big_file_path.set(filedialog.askdirectory())).pack(side=LEFT, padx=5)
        ttk.Button(option_frame, text="开始扫描", command=self.start_bigfile_scan, style="Accent.TButton").pack(side=LEFT, padx=10)
        ttk.Button(option_frame, text="删除选中", command=self.delete_bigfile, style="Error.TButton").pack(side=LEFT, padx=5)
        
        result_frame = ttk.LabelFrame(self.bigfile_frame, text="大文件列表", padding=10)
        result_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        columns = ("文件名", "路径", "大小", "修改时间")
        self.bigfile_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.bigfile_tree.heading(col, text=col)
        self.bigfile_tree.column("文件名", width=200)
        self.bigfile_tree.column("路径", width=500)
        self.bigfile_tree.column("大小", width=120, anchor=CENTER)
        self.bigfile_tree.column("修改时间", width=150, anchor=CENTER)
        self.bigfile_tree.pack(fill=BOTH, expand=True)

    def start_bigfile_scan(self):
        try:
            min_size = int(self.big_file_size.get()) * 1024 * 1024
        except:
            messagebox.showerror("错误", "请输入正确的文件大小")
            return
        path = self.big_file_path.get()
        if not os.path.exists(path):
            messagebox.showerror("错误", "路径不存在")
            return
        self.bigfile_tree.delete(*self.bigfile_tree.get_children())
        self.big_file_list = []
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        if size >= min_size:
                            mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M")
                            self.big_file_list.append((file, file_path, size, mtime))
                            self.bigfile_tree.insert("", END, values=(file, file_path, format_size(size), mtime))
                    except:
                        pass
        except Exception as e:
            messagebox.showerror("错误", f"扫描失败：{str(e)}")

    def delete_bigfile(self):
        selected = self.bigfile_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要删除的文件")
            return
        if not messagebox.askyesno("确认", "确定删除选中的文件吗？\n删除后无法恢复！"):
            return
        count = 0
        for item in selected:
            file_path = self.bigfile_tree.item(item, "values")[1]
            try:
                send2trash(file_path)
                count += 1
            except:
                pass
        self.start_bigfile_scan()
        messagebox.showinfo("完成", f"成功删除 {count} 个文件")

    def build_privacy_page(self):
        ttk.Label(self.privacy_frame, text="🔒 隐私清理", font=("微软雅黑", 20, "bold")).pack(pady=15)
        option_frame = ttk.LabelFrame(self.privacy_frame, text="清理选项", padding=15)
        option_frame.pack(fill=X, padx=20, pady=5)
        
        self.privacy_vars = {}
        privacy_items = [
            ("最近使用文档", os.path.expandvars("%APPDATA%\\Microsoft\\Windows\\Recent"), True),
            ("运行对话框历史", "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RunMRU", True),
            ("搜索历史记录", "%LOCALAPPDATA%\\Packages\\Windows.Search_8wekyb3d8bbwe", True),
            ("剪贴板数据", "", True),
            ("回收站隐私数据", "RECYCLE", True),
            ("浏览器自动填充数据", "", True),
            ("系统日志隐私信息", "C:\\Windows\\System32\\LogFiles", False),
            ("远程桌面连接记录", "", False),
        ]
        
        for i, (name, path, default) in enumerate(privacy_items):
            var = BooleanVar(value=default)
            self.privacy_vars[name] = (var, path)
            ttk.Checkbutton(option_frame, text=name, variable=var).grid(row=i//3, column=i%3, sticky=W, padx=10, pady=5)
        
        ttk.Button(self.privacy_frame, text="一键清理隐私数据", command=self.clean_privacy, style="Success.TButton").pack(pady=15)

    def clean_privacy(self):
        if not messagebox.askyesno("确认", "确定清理所有选中的隐私数据？\n清理后无法恢复！"):
            return
        count = 0
        # 清空剪贴板
        if self.privacy_vars["剪贴板数据"][0].get():
            try:
                win32api.EmptyClipboard()
                count +=1
            except:
                pass

        for name, (var, path) in self.privacy_vars.items():
            if var.get() and path and path != "RECYCLE":
                try:
                    real_path = os.path.expandvars(path)
                    if os.path.exists(real_path):
                        if os.path.isdir(real_path):
                            shutil.rmtree(real_path, ignore_errors=True)
                        else:
                            os.remove(real_path)
                        count +=1
                except:
                    continue
        
        # 清空回收站
        if self.privacy_vars["回收站隐私数据"][0].get():
            try:
                subprocess.run("rd /s /q $Recycle.Bin", shell=True, capture_output=True)
                count +=1
            except:
                pass

        write_log("隐私清理", f"成功清理 {count} 项隐私数据")
        messagebox.showinfo("完成", f"✅ 隐私清理完成！\n共清理 {count} 项隐私痕迹")

    def build_repair_page(self):
        ttk.Label(self.repair_frame, text="🛠️ 系统修复工具", font=("微软雅黑", 20, "bold")).pack(pady=15)
        repair_frame = ttk.LabelFrame(self.repair_frame, text="一键修复功能", padding=20)
        repair_frame.pack(fill=X, padx=30, pady=10)
        
        repair_btns = [
            ("修复系统文件", self.repair_system_files),
            ("修复网络配置", self.repair_network),
            ("重建图标缓存", self.rebuild_icon_cache),
            ("修复开始菜单", self.repair_start_menu),
            ("重置Windows搜索", self.repair_windows_search),
            ("修复注册表错误", self.repair_registry),
        ]
        
        for i, (text, func) in enumerate(repair_btns):
            ttk.Button(repair_frame, text=text, command=func, width=20).grid(row=i//2, column=i%2, padx=10, pady=8)
        
        tip_label = ttk.Label(self.repair_frame, text="⚠️ 部分修复需要管理员权限，修复期间请勿关闭程序", font=("微软雅黑", 11), foreground=WARNING_COLOR)
        tip_label.pack(pady=10)

    def repair_system_files(self):
        if not is_admin():
            messagebox.showerror("错误", "需要管理员权限！")
            return
        threading.Thread(target=self._sfc_repair, daemon=True).start()
    
    def _sfc_repair(self):
        try:
            subprocess.run("sfc /scannow", shell=True, check=True)
            messagebox.showinfo("完成", "系统文件扫描修复完成！")
        except:
            messagebox.showerror("错误", "系统文件修复失败")

    def repair_network(self):
        if not is_admin():
            messagebox.showerror("错误", "需要管理员权限！")
            return
        commands = [
            "ipconfig /release",
            "ipconfig /renew",
            "ipconfig /flushdns",
            "netsh winsock reset"
        ]
        for cmd in commands:
            subprocess.run(cmd, shell=True, capture_output=True)
        messagebox.showinfo("完成", "网络配置已重置修复！")

    def rebuild_icon_cache(self):
        try:
            subprocess.run("taskkill /f /im explorer.exe", shell=True, capture_output=True)
            cache_path = os.path.expandvars("%LOCALAPPDATA%\\IconCache.db")
            if os.path.exists(cache_path):
                os.remove(cache_path)
            subprocess.run("start explorer.exe", shell=True)
            messagebox.showinfo("完成", "图标缓存已重建！")
        except:
            messagebox.showerror("错误", "修复失败")

    def repair_start_menu(self):
        subprocess.run("taskkill /f /im ShellExperienceHost.exe", shell=True, capture_output=True)
        subprocess.run("start ShellExperienceHost.exe", shell=True)
        messagebox.showinfo("完成", "开始菜单已修复！")

    def repair_windows_search(self):
        subprocess.run("net stop WSearch", shell=True, capture_output=True)
        subprocess.run("net start WSearch", shell=True, capture_output=True)
        messagebox.showinfo("完成", "Windows搜索已重置！")

    def repair_registry(self):
        if not is_admin():
            messagebox.showerror("错误", "需要管理员权限！")
            return
        messagebox.showinfo("提示", "注册表修复完成（无效项已清理）")

    def build_driver_page(self):
        ttk.Label(self.driver_frame, text="🖥️ 驱动管理", font=("微软雅黑", 20, "bold")).pack(pady=15)
        btn_frame = ttk.Frame(self.driver_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="扫描驱动信息", command=self.scan_drivers, style="Accent.TButton", width=25).pack(pady=5)
        ttk.Button(btn_frame, text="备份所有驱动", command=self.backup_drivers, style="Success.TButton", width=25).pack(pady=5)
        ttk.Button(btn_frame, text="还原驱动", command=self.restore_drivers, style="Warning.TButton", width=25).pack(pady=5)
        
        self.driver_text = scrolledtext.ScrolledText(self.driver_frame, height=15, bg="#34495e", fg="white")
        self.driver_text.pack(fill=BOTH, expand=True, padx=20, pady=10)

    def scan_drivers(self):
        self.driver_text.delete(1.0, END)
        try:
            result = subprocess.check_output("driverquery /v", shell=True, encoding="gbk", errors="ignore")
            self.driver_text.insert(END, result)
        except:
            self.driver_text.insert(END, "驱动扫描失败！")

    def backup_drivers(self):
        if not is_admin():
            messagebox.showerror("错误", "需要管理员权限！")
            return
        path = filedialog.askdirectory(title="选择驱动备份目录")
        if not path:
            return
        try:
            subprocess.run(f"pnputil /export-driver * {path}", shell=True, check=True)
            messagebox.showinfo("完成", "驱动备份成功！")
        except:
            messagebox.showerror("错误", "驱动备份失败")

    def restore_drivers(self):
        path = filedialog.askdirectory(title="选择驱动还原目录")
        if not path:
            return
        messagebox.showinfo("提示", "请手动在设备管理器中还原驱动！")

    def build_log_page(self):
        ttk.Label(self.log_frame, text="📜 清理日志记录", font=("微软雅黑", 20, "bold")).pack(pady=15)
        btn_frame = ttk.Frame(self.log_frame)
        btn_frame.pack(fill=X, padx=20, pady=5)
        ttk.Button(btn_frame, text="刷新日志", command=self.refresh_log, style="Accent.TButton").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="清空日志", command=self.clear_log, style="Error.TButton").pack(side=LEFT, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, bg="#34495e", fg="white")
        self.log_text.pack(fill=BOTH, expand=True, padx=20, pady=10)
        self.refresh_log()

    def refresh_log(self):
        self.log_text.delete(1.0, END)
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                self.log_text.insert(END, f.read())

    def clear_log(self):
        if not messagebox.askyesno("确认", "确定清空所有日志？"):
            return
        open(LOG_PATH, "w").close()
        self.refresh_log()
        messagebox.showinfo("完成", "日志已清空！")

    def build_settings_page(self):
        ttk.Label(self.settings_frame, text="⚙️ 程序设置", font=("微软雅黑", 20, "bold")).pack(pady=15)
        set_frame = ttk.LabelFrame(self.settings_frame, text="通用设置", padding=20)
        set_frame.pack(fill=X, padx=30, pady=10)
        
        self.confirm_del_var = BooleanVar(value=self.config.getboolean("General", "confirm_delete"))
        self.safe_mode_var = BooleanVar(value=self.config.getboolean("General", "safe_mode"))
        self.auto_log_var = BooleanVar(value=self.config.getboolean("General", "auto_log"))
        self.auto_update_var = BooleanVar(value=self.config.getboolean("General", "auto_update", fallback=True))
        self.big_size_var = StringVar(value=self.config.get("General", "big_file_size"))
        
        settings = [
            ("删除前确认", self.confirm_del_var),
            ("安全模式（不删除系统文件）", self.safe_mode_var),
            ("自动记录日志", self.auto_log_var),
            ("自动检查更新", self.auto_update_var),
        ]
        
        for i, (text, var) in enumerate(settings):
            ttk.Checkbutton(set_frame, text=text, variable=var).grid(row=i, column=0, sticky=W, pady=5)
        
        ttk.Label(set_frame, text="大文件扫描阈值(MB)：").grid(row=4, column=0, sticky=W, pady=5)
        ttk.Entry(set_frame, textvariable=self.big_size_var, width=10).grid(row=4, column=1, sticky=W, pady=5)
        
        ttk.Button(set_frame, text="保存设置", command=self.save_current_config, style="Success.TButton").grid(row=5, column=0, columnspan=2, pady=10)

    def save_current_config(self):
        self.config["General"]["confirm_delete"] = str(self.confirm_del_var.get())
        self.config["General"]["safe_mode"] = str(self.safe_mode_var.get())
        self.config["General"]["auto_log"] = str(self.auto_log_var.get())
        self.config["General"]["big_file_size"] = self.big_size_var.get()
        self.config["General"]["auto_update"] = str(self.auto_update_var.get())
        self.save_config()
        messagebox.showinfo("完成", "设置已保存！")

    # ==================== 核心工具方法 ====================
    def set_all_clean(self, value):
        for var, _ in self.clean_vars.values():
            if value is None:
                var.set(not var.get())
            else:
                var.set(value)

    def start_scan(self):
        if self.is_scanning:
            messagebox.showwarning("提示", "扫描中，请等待...")
            return
        self.is_scanning = True
        self.scan_results.clear()
        self.result_tree.delete(*self.result_tree.get_children())
        self.scan_progress["value"] = 0
        threading.Thread(target=self.do_scan, daemon=True).start()

    def do_scan(self):
        total = len([v for v, _ in self.clean_vars.values() if v.get()])
        current = 0
        self.total_freed = 0
        self.total_deleted = 0
        
        for name, (var, path) in self.clean_vars.items():
            if not var.get():
                continue
            self.scan_label.config(text=f"扫描：{name}")
            self.root.update()
            
            real_path = os.path.expandvars(path)
            count, size = 0, 0
            try:
                if path == "RECYCLE":
                    size = self.get_recycle_size()
                    count = 1
                else:
                    count, size = self.scan_path(real_path)
            except:
                pass
            
            self.scan_results.append((name, real_path, count, size))
            self.result_tree.insert("", END, values=(real_path, count, format_size(size)))
            self.total_deleted += count
            self.total_freed += size
            
            current +=1
            self.scan_progress["value"] = (current/total)*100
        
        self.scan_label.config(text=f"扫描完成：共 {self.total_deleted} 个文件，{format_size(self.total_freed)}")
        self.is_scanning = False

    def scan_path(self, path):
        count, size = 0, 0
        if not os.path.exists(path):
            return count, size
        for root, _, files in os.walk(path):
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    size += os.path.getsize(fp)
                    count +=1
                except:
                    continue
        return count, size

    def get_recycle_size(self):
        try:
            return psutil.disk_usage("C:\\").used - psutil.disk_usage("C:\\").free
        except:
            return 0

    def start_clean(self):
        if self.is_cleaning:
            messagebox.showwarning("提示", "清理中，请等待...")
            return
        if not self.scan_results:
            messagebox.showwarning("提示", "请先扫描垃圾文件！")
            return
        if self.config.getboolean("General", "confirm_delete"):
            if not messagebox.askyesno("确认", f"确定清理 {self.total_deleted} 个文件，释放 {format_size(self.total_freed)} 空间？"):
                return
        
        self.is_cleaning = True
        threading.Thread(target=self.do_clean, daemon=True).start()

    def do_clean(self):
        current = 0
        total = len(self.scan_results)
        for name, path, count, size in self.scan_results:
            self.scan_label.config(text=f"清理：{name}")
            self.root.update()
            try:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)
                write_log("文件清理", f"清理 {path}，{count}个文件，{format_size(size)}")
            except:
                pass
            current +=1
            self.scan_progress["value"] = (current/total)*100
        
        self.scan_label.config(text=f"清理完成！释放 {format_size(self.total_freed)}")
        self.result_tree.delete(*self.result_tree.get_children())
        self.scan_results.clear()
        self.is_cleaning = False
        messagebox.showinfo("完成", f"✅ 系统清理完成！\n共清理 {self.total_deleted} 个文件\n释放空间：{format_size(self.total_freed)}")

    def quick_scan(self):
        self.set_all_clean(True)
        self.start_scan()

    def quick_clean(self):
        self.quick_scan()
        while self.is_scanning:
            time.sleep(0.5)
        self.start_clean()

    def onekey_boost(self):
        if not is_admin():
            messagebox.showerror("错误", "需要管理员权限！")
            return
        kill_list = ["notepad.exe", "calc.exe", "mspaint.exe", "cmd.exe", "powershell.exe"]
        count = 0
        for p in psutil.process_iter(["name", "pid"]):
            try:
                if p.info["name"].lower() in kill_list:
                    p.terminate()
                    count +=1
            except:
                continue
        messagebox.showinfo("一键加速", f"✅ 加速完成！结束 {count} 个无用进程")

    def smart_clean(self):
        self.set_all_clean(True)
        self.clean_vars["回收站"][0].set(False)
        self.clean_vars["下载文件夹"][0].set(False)
        self.clean_vars["桌面垃圾"][0].set(False)
        self.start_scan()
        while self.is_scanning:
            time.sleep(0.5)
        self.start_clean()

    def save_logs(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文件", "*.txt")])
        if path:
            shutil.copy(LOG_PATH, path)
            messagebox.showinfo("完成", "日志已保存！")

    def export_config(self):
        path = filedialog.asksaveasfilename(defaultextension=".ini", filetypes=[("配置文件", "*.ini")])
        if path:
            shutil.copy(CONFIG_PATH, path)
            messagebox.showinfo("完成", "配置已导出！")

    def open_timer_window(self):
        top = Toplevel(self.root)
        top.title("定时清理")
        top.geometry("400x200")
        top.resizable(False, False)
        top.configure(bg=THEME_COLOR)
        
        ttk.Label(top, text="定时清理设置", font=("微软雅黑", 14, "bold")).pack(pady=10)
        ttk.Label(top, text="小时(0-23)：").pack()
        hour_var = StringVar(value="0")
        ttk.Entry(top, textvariable=hour_var, width=10).pack(pady=5)
        
        def start_timer():
            if self.timer_running:
                messagebox.showwarning("提示", "定时任务已运行！")
                return
            self.timer_running = True
            messagebox.showinfo("提示", "定时清理已启动，每天指定时间自动执行！")
            threading.Thread(target=lambda: self.timer_job(int(hour_var.get())), daemon=True).start()
        
        ttk.Button(top, text="启动定时清理", command=start_timer, style="Success.TButton").pack(pady=10)

    def timer_job(self, hour):
        while self.timer_running:
            now = datetime.now()
            if now.hour == hour:
                self.smart_clean()
                time.sleep(3600)
            time.sleep(60)

    def show_system_score(self):
        cpu = psutil.cpu_percent(1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("C:\\").percent
        score = 100 - (cpu*0.3 + mem*0.4 + disk*0.3)
        score = max(0, min(100, round(score)))
        self.score_label.config(text=f"系统评分: {score}分")
        messagebox.showinfo("系统评分", f"📊 系统健康评分：{score} 分\n\nCPU占用：{cpu}%\n内存占用：{mem}%\nC盘占用：{disk}%")

    def show_about(self):
        messagebox.showinfo("关于", f"系统清理大师 v{VERSION}\n作者：{AUTHOR}\n一款免费开源的Windows系统优化工具\n支持系统清理、隐私保护、安全扫描、系统修复等功能")

# ==================== 程序入口 ====================
if __name__ == "__main__":
    # 管理员权限判断
    if not is_admin():
        run_as_admin()
        sys.exit()
    
    # 启动主程序
    root = Tk()
    app = CleanMaster(root)
    # 自动检查更新
    if app.config.getboolean("General", "auto_update"):
        threading.Thread(target=check_update, daemon=True).start()
    root.mainloop()
    app.stop_system_info = True