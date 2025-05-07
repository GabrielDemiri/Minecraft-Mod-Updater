import os
import sys
import json
import zipfile
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk, ImageDraw, ImageFont

class CustomTkTheme:
    DARK_BG = "#0f0f0f"
    DARK_SECONDARY = "#1a1a1a"
    DARK_TERTIARY = "#252525"
    ACCENT = "#8c52ff"
    ACCENT_HOVER = "#9d6fff"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    SUCCESS = "#4ade80"
    WARNING = "#facc15"
    ERROR = "#f87171"
    
    @staticmethod
    def apply_theme(root, style):
        root.configure(bg=CustomTkTheme.DARK_BG)
        
        style.configure("TFrame", background=CustomTkTheme.DARK_BG)
        
        style.configure("Card.TFrame", 
                       background=CustomTkTheme.DARK_SECONDARY,
                       relief="flat",
                       borderwidth=0)
        
        style.configure("TLabel", 
                       background=CustomTkTheme.DARK_BG, 
                       foreground=CustomTkTheme.TEXT_PRIMARY,
                       font=("Segoe UI", 10))
        
        style.configure("Header.TLabel", 
                       background=CustomTkTheme.DARK_BG, 
                       foreground=CustomTkTheme.TEXT_PRIMARY,
                       font=("Segoe UI", 18, "bold"))
        
        style.configure("Subheader.TLabel", 
                       background=CustomTkTheme.DARK_BG, 
                       foreground=CustomTkTheme.TEXT_PRIMARY,
                       font=("Segoe UI", 14))
        
        style.configure("Card.TLabel", 
                       background=CustomTkTheme.DARK_SECONDARY, 
                       foreground=CustomTkTheme.TEXT_PRIMARY)
        
        style.configure("TButton", 
                       background=CustomTkTheme.ACCENT, 
                       foreground=CustomTkTheme.TEXT_PRIMARY,
                       font=("Segoe UI", 10, "bold"),
                       borderwidth=0,
                       focusthickness=0,
                       padding=(15, 8))
        
        style.map("TButton", 
                 background=[("active", CustomTkTheme.ACCENT_HOVER)],
                 foreground=[("active", CustomTkTheme.TEXT_PRIMARY)])
        
        style.configure("Secondary.TButton", 
                       background=CustomTkTheme.DARK_TERTIARY)
        
        style.map("Secondary.TButton", 
                 background=[("active", "#333333")])
        
        style.configure("TEntry", 
                       fieldbackground=CustomTkTheme.DARK_TERTIARY, 
                       foreground=CustomTkTheme.TEXT_PRIMARY,
                       borderwidth=0,
                       padding=10)
        
        style.configure("Treeview", 
                       background=CustomTkTheme.DARK_SECONDARY, 
                       foreground=CustomTkTheme.TEXT_PRIMARY,
                       fieldbackground=CustomTkTheme.DARK_SECONDARY,
                       font=("Segoe UI", 10),
                       borderwidth=0,
                       rowheight=30)
        
        style.map("Treeview", 
                 background=[("selected", CustomTkTheme.ACCENT)],
                 foreground=[("selected", CustomTkTheme.TEXT_PRIMARY)])
        
        style.configure("Treeview.Heading", 
                       background=CustomTkTheme.DARK_TERTIARY, 
                       foreground=CustomTkTheme.TEXT_PRIMARY,
                       font=("Segoe UI", 10, "bold"),
                       borderwidth=0,
                       padding=10)
        
        style.configure("TScrollbar", 
                       background=CustomTkTheme.DARK_TERTIARY, 
                       troughcolor=CustomTkTheme.DARK_BG,
                       borderwidth=0,
                       arrowsize=14,
                       arrowcolor=CustomTkTheme.TEXT_PRIMARY)
        
        style.configure("TSeparator", 
                       background=CustomTkTheme.DARK_TERTIARY)
    
    @staticmethod
    def create_rounded_rectangle(width, height, radius, fill_color):
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        draw.rounded_rectangle([(0, 0), (width-1, height-1)], radius, fill=fill_color)
        
        return ImageTk.PhotoImage(image)


class ModrinthAPI:
    BASE_URL = "https://api.modrinth.com/v2"
    USER_AGENT = "MinecraftModManager/1.0 (github.com/user/mod-manager)"
    
    @staticmethod
    def search_mod(query: str) -> List[Dict]:
        headers = {"User-Agent": ModrinthAPI.USER_AGENT}
        params = {
            "query": query,
            "limit": 10
        }
        
        try:
            response = requests.get(
                f"{ModrinthAPI.BASE_URL}/search", 
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()["hits"]
            else:
                print(f"Error searching mods: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            print(f"Exception during search: {e}")
            return []
    
    @staticmethod
    def get_mod_versions(mod_id: str, game_version: str = None) -> List[Dict]:
        headers = {"User-Agent": ModrinthAPI.USER_AGENT}
        url = f"{ModrinthAPI.BASE_URL}/project/{mod_id}/version"
        
        params = {}
        if game_version:
            params["game_versions"] = f"[\"{game_version}\"]"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting mod versions: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            print(f"Exception getting versions: {e}")
            return []


class ModAnalyzer:
    @staticmethod
    def get_mod_info_from_jar(jar_path: str) -> Dict:
        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                if "META-INF/mods.toml" in jar.namelist():
                    with jar.open("META-INF/mods.toml") as toml_file:
                        content = toml_file.read().decode('utf-8')
                        mod_id = None
                        version = None
                        display_name = None
                        
                        for line in content.split('\n'):
                            line = line.strip()
                            if line.startswith("modId"):
                                mod_id = line.split('=')[1].strip().strip('"\'')
                            elif line.startswith("version"):
                                version = line.split('=')[1].strip().strip('"\'')
                            elif line.startswith("displayName"):
                                display_name = line.split('=')[1].strip().strip('"\'')
                        
                        return {
                            "mod_id": mod_id,
                            "version": version,
                            "name": display_name,
                            "type": "forge"
                        }
                
                elif "fabric.mod.json" in jar.namelist():
                    with jar.open("fabric.mod.json") as json_file:
                        data = json.loads(json_file.read().decode('utf-8'))
                        return {
                            "mod_id": data.get("id"),
                            "version": data.get("version"),
                            "name": data.get("name"),
                            "type": "fabric"
                        }
                
                return {
                    "mod_id": None,
                    "version": None,
                    "name": os.path.basename(jar_path).replace(".jar", ""),
                    "type": "unknown"
                }
        except Exception as e:
            print(f"Error analyzing JAR file {jar_path}: {e}")
            return {
                "mod_id": None,
                "version": None,
                "name": os.path.basename(jar_path).replace(".jar", ""),
                "type": "error",
                "error": str(e)
            }


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=120, height=36, 
                 bg_color=CustomTkTheme.ACCENT, hover_color=CustomTkTheme.ACCENT_HOVER, 
                 text_color=CustomTkTheme.TEXT_PRIMARY, **kwargs):
        super().__init__(parent, width=width, height=height, 
                         bg=CustomTkTheme.DARK_BG, highlightthickness=0, **kwargs)
        
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.command = command
        self.text = text
        
        self.normal_bg = CustomTkTheme.create_rounded_rectangle(width, height, 8, bg_color)
        self.hover_bg = CustomTkTheme.create_rounded_rectangle(width, height, 8, hover_color)
        
        self.bg_img = self.create_image(width//2, height//2, image=self.normal_bg)
        self.text_id = self.create_text(width//2, height//2, text=text, 
                                       fill=text_color, font=("Segoe UI", 10, "bold"))
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
    def on_enter(self, event):
        self.itemconfig(self.bg_img, image=self.hover_bg)
    
    def on_leave(self, event):
        self.itemconfig(self.bg_img, image=self.normal_bg)
    
    def on_click(self, event):
        if self.command:
            self.command()


class RoundedFrame(tk.Canvas):
    def __init__(self, parent, width, height, bg_color=CustomTkTheme.DARK_SECONDARY, **kwargs):
        super().__init__(parent, width=width, height=height, 
                         bg=CustomTkTheme.DARK_BG, highlightthickness=0, **kwargs)
        
        self.bg_img = CustomTkTheme.create_rounded_rectangle(width, height, 10, bg_color)
        self.create_image(width//2, height//2, image=self.bg_img)
        
        self.frame = tk.Frame(self, bg=bg_color)
        self.frame.place(x=10, y=10, width=width-20, height=height-20)


class StatusBadge(tk.Canvas):
    def __init__(self, parent, text, status_type="normal", **kwargs):
        if status_type == "success":
            bg_color = CustomTkTheme.SUCCESS
            text_color = "#000000"
        elif status_type == "warning":
            bg_color = CustomTkTheme.WARNING
            text_color = "#000000"
        elif status_type == "error":
            bg_color = CustomTkTheme.ERROR
            text_color = "#000000"
        else:
            bg_color = CustomTkTheme.DARK_TERTIARY
            text_color = CustomTkTheme.TEXT_PRIMARY
        
        text_width = len(text) * 7 + 20
        width = max(text_width, 80)
        height = 24
        
        super().__init__(parent, width=width, height=height, 
                         bg=CustomTkTheme.DARK_SECONDARY, highlightthickness=0, **kwargs)
        
        self.bg_img = CustomTkTheme.create_rounded_rectangle(width, height, 12, bg_color)
        self.create_image(width//2, height//2, image=self.bg_img)
        
        self.create_text(width//2, height//2, text=text, 
                        fill=text_color, font=("Segoe UI", 9, "bold"))


class VersionSelectionDialog(tk.Toplevel):
    def __init__(self, parent, title, versions):
        super().__init__(parent)
        self.title(title)
        self.geometry("700x600")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.configure(bg=CustomTkTheme.DARK_BG)
        
        self.versions = versions
        self.selected_version = None
        
        self.create_ui()
        
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.wait_window()
    
    def create_ui(self):
        main_frame = tk.Frame(self, bg=CustomTkTheme.DARK_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        header_label = tk.Label(main_frame, text="Select Version", 
                               bg=CustomTkTheme.DARK_BG, 
                               fg=CustomTkTheme.TEXT_PRIMARY,
                               font=("Segoe UI", 18, "bold"))
        header_label.pack(anchor=tk.W, pady=(0, 25))
        
        columns = ("version", "mc_version", "date")
        
        tree_frame = RoundedFrame(main_frame, 640, 420)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 25))
        
        self.versions_tree = ttk.Treeview(tree_frame.frame, columns=columns, show="headings")
        
        self.versions_tree.heading("version", text="Version")
        self.versions_tree.heading("mc_version", text="Minecraft Version")
        self.versions_tree.heading("date", text="Release Date")
        
        self.versions_tree.column("version", width=200)
        self.versions_tree.column("mc_version", width=200)
        self.versions_tree.column("date", width=200)
        
        scrollbar = ttk.Scrollbar(tree_frame.frame, orient=tk.VERTICAL, command=self.versions_tree.yview)
        self.versions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.versions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for version in self.versions:
            version_number = version.get("version_number", "Unknown")
            game_versions = ", ".join(version.get("game_versions", ["Unknown"]))
            date_published = version.get("date_published", "Unknown").split("T")[0]
            
            self.versions_tree.insert("", tk.END, values=(
                version_number,
                game_versions,
                date_published
            ))
        
        self.versions_tree.bind("<Double-1>", self.on_version_select)
        
        buttons_frame = tk.Frame(main_frame, bg=CustomTkTheme.DARK_BG)
        buttons_frame.pack(fill=tk.X)
        
        cancel_btn = RoundedButton(buttons_frame, "Cancel", 
                                  command=self.destroy, 
                                  width=140,
                                  height=40,
                                  bg_color=CustomTkTheme.DARK_TERTIARY,
                                  hover_color="#333333")
        cancel_btn.pack(side=tk.RIGHT, padx=(15, 0))
        
        select_btn = RoundedButton(buttons_frame, "Select", 
                                  command=self.on_select_button,
                                  width=140,
                                  height=40)
        select_btn.pack(side=tk.RIGHT)
    
    def on_version_select(self, event):
        self.on_select_button()
    
    def on_select_button(self):
        selected = self.versions_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No version selected")
            return
        
        values = self.versions_tree.item(selected[0], "values")
        version_number = values[0]
        
        for version in self.versions:
            if version.get("version_number") == version_number:
                self.selected_version = version
                break
        
        self.destroy()


class ModManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Mod Manager")
        
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        self.center_window()
        
        self.minecraft_version = "1.21.5"
        
        self.style = ttk.Style()
        CustomTkTheme.apply_theme(root, self.style)
        
        self.mods_folder = self.get_default_mods_folder()
        
        self.create_ui()
        
        self.load_mods()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def get_default_mods_folder(self) -> str:
        home = Path.home()
        
        if sys.platform == "win32":
            return str(home / "AppData" / "Roaming" / ".minecraft" / "mods")
        elif sys.platform == "darwin":
            return str(home / "Library" / "Application Support" / "minecraft" / "mods")
        else:
            return str(home / ".minecraft" / "mods")
    
    def create_ui(self):
        container = tk.Frame(self.root, bg=CustomTkTheme.DARK_BG)
        container.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        self.create_header(container)
        
        self.create_folder_section(container)
        
        self.create_mods_section(container)
        
        self.create_actions_section(container)
        
        self.create_log_section(container)
    
    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg=CustomTkTheme.DARK_BG)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_label = tk.Label(header_frame, text="Minecraft Mod Manager", 
                              bg=CustomTkTheme.DARK_BG, 
                              fg=CustomTkTheme.TEXT_PRIMARY,
                              font=("Segoe UI", 28, "bold"))
        title_label.pack(side=tk.LEFT)
        
        version_frame = tk.Frame(header_frame, bg=CustomTkTheme.DARK_BG)
        version_frame.pack(side=tk.RIGHT, padx=10)
        
        version_label = tk.Label(version_frame, text="Minecraft Version:", 
                                bg=CustomTkTheme.DARK_BG, 
                                fg=CustomTkTheme.TEXT_SECONDARY,
                                font=("Segoe UI", 12))
        version_label.pack(side=tk.LEFT, padx=(0, 15))
        
        version_entry_frame = RoundedFrame(version_frame, 120, 40, bg_color=CustomTkTheme.DARK_TERTIARY)
        version_entry_frame.pack(side=tk.LEFT)
        
        self.version_var = tk.StringVar(value=self.minecraft_version)
        version_entry = tk.Entry(version_entry_frame.frame, 
                                textvariable=self.version_var, 
                                width=8,
                                bg=CustomTkTheme.DARK_TERTIARY,
                                fg=CustomTkTheme.TEXT_PRIMARY,
                                font=("Segoe UI", 12),
                                bd=0,
                                insertbackground=CustomTkTheme.TEXT_PRIMARY)
        version_entry.pack(fill=tk.BOTH, expand=True, padx=10)
    
    def create_folder_section(self, parent):
        folder_frame = RoundedFrame(parent, 1320, 90)
        folder_frame.pack(fill=tk.X, pady=(0, 30))
        
        inner_frame = tk.Frame(folder_frame.frame, bg=CustomTkTheme.DARK_SECONDARY)
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        folder_label = tk.Label(inner_frame, text="Mods Folder:", 
                               bg=CustomTkTheme.DARK_SECONDARY, 
                               fg=CustomTkTheme.TEXT_PRIMARY,
                               font=("Segoe UI", 12))
        folder_label.pack(side=tk.LEFT, padx=(0, 15))
        
        entry_frame = RoundedFrame(inner_frame, 900, 40, bg_color=CustomTkTheme.DARK_TERTIARY)
        entry_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        self.folder_var = tk.StringVar(value=self.mods_folder)
        folder_entry = tk.Entry(entry_frame.frame, 
                               textvariable=self.folder_var, 
                               bg=CustomTkTheme.DARK_TERTIARY,
                               fg=CustomTkTheme.TEXT_PRIMARY,
                               font=("Segoe UI", 12),
                               bd=0,
                               insertbackground=CustomTkTheme.TEXT_PRIMARY)
        folder_entry.pack(fill=tk.BOTH, expand=True, padx=10)
        
        browse_btn = RoundedButton(inner_frame, "Browse", 
                                  command=self.browse_folder,
                                  width=140,
                                  height=40)
        browse_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        refresh_btn = RoundedButton(inner_frame, "Refresh", 
                                   command=self.load_mods,
                                   width=140,
                                   height=40,
                                   bg_color=CustomTkTheme.DARK_TERTIARY,
                                   hover_color="#333333")
        refresh_btn.pack(side=tk.LEFT)
    
    def create_mods_section(self, parent):
        mods_label = tk.Label(parent, text="Installed Mods", 
                             bg=CustomTkTheme.DARK_BG, 
                             fg=CustomTkTheme.TEXT_PRIMARY,
                             font=("Segoe UI", 18, "bold"))
        mods_label.pack(anchor=tk.W, pady=(0, 15))
        
        mods_frame = RoundedFrame(parent, 1320, 450)
        mods_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 30))
        
        columns = ("name", "current_version", "latest_version", "status")
        self.mods_tree = ttk.Treeview(mods_frame.frame, columns=columns, show="headings")
        
        self.mods_tree.heading("name", text="Mod Name")
        self.mods_tree.heading("current_version", text="Current Version")
        self.mods_tree.heading("latest_version", text="Latest Version")
        self.mods_tree.heading("status", text="Status")
        
        self.mods_tree.column("name", width=600, minwidth=300)
        self.mods_tree.column("current_version", width=200, minwidth=150)
        self.mods_tree.column("latest_version", width=200, minwidth=150)
        self.mods_tree.column("status", width=200, minwidth=150)
        
        scrollbar = ttk.Scrollbar(mods_frame.frame, orient=tk.VERTICAL, command=self.mods_tree.yview)
        self.mods_tree.configure(yscrollcommand=scrollbar.set)
        
        self.mods_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_actions_section(self, parent):
        actions_frame = RoundedFrame(parent, 1320, 80)
        actions_frame.pack(fill=tk.X, pady=(0, 30))
        
        inner_frame = tk.Frame(actions_frame.frame, bg=CustomTkTheme.DARK_SECONDARY)
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        check_updates_btn = RoundedButton(inner_frame, "Check for Updates", 
                                         width=180,
                                         height=40,
                                         command=self.check_updates)
        check_updates_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        update_btn = RoundedButton(inner_frame, "Update Selected", 
                                  width=180,
                                  height=40,
                                  command=self.update_selected)
        update_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        downgrade_btn = RoundedButton(inner_frame, "Downgrade Selected", 
                                     width=180,
                                     height=40,
                                     command=self.downgrade_selected)
        downgrade_btn.pack(side=tk.LEFT)
    
    def create_log_section(self, parent):
        log_label = tk.Label(parent, text="Activity Log", 
                            bg=CustomTkTheme.DARK_BG, 
                            fg=CustomTkTheme.TEXT_PRIMARY,
                            font=("Segoe UI", 18, "bold"))
        log_label.pack(anchor=tk.W, pady=(0, 15))
        
        log_frame = RoundedFrame(parent, 1320, 180)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame.frame, 
                               height=8, 
                               bg=CustomTkTheme.DARK_SECONDARY, 
                               fg=CustomTkTheme.TEXT_PRIMARY,
                               font=("Consolas", 11),
                               bd=0,
                               padx=15,
                               pady=15,
                               insertbackground=CustomTkTheme.TEXT_PRIMARY)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        log_scrollbar = ttk.Scrollbar(log_frame.frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.config(state=tk.DISABLED)
        
        self.log(f"Application started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Default Minecraft version: {self.minecraft_version}")
    
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)
            self.mods_folder = folder
            self.load_mods()
    
    def log(self, message: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{formatted_message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        print(formatted_message)
    
    def load_mods(self):
        for item in self.mods_tree.get_children():
            self.mods_tree.delete(item)
        
        folder = self.folder_var.get()
        if not os.path.exists(folder):
            self.log(f"Folder not found: {folder}")
            return
        
        self.log(f"Loading mods from: {folder}")
        
        jar_files = [f for f in os.listdir(folder) if f.endswith('.jar')]
        
        if not jar_files:
            self.log("No mod files (.jar) found in the folder.")
            return
        
        self.log(f"Found {len(jar_files)} mod files.")
        
        for jar_file in jar_files:
            jar_path = os.path.join(folder, jar_file)
            mod_info = ModAnalyzer.get_mod_info_from_jar(jar_path)
            
            self.mods_tree.insert("", tk.END, values=(
                mod_info.get("name", jar_file),
                mod_info.get("version", "Unknown"),
                "Not checked",
                "Installed"
            ))
        
        self.log("Finished loading mods.")
    
    def check_updates(self):
        mods = self.mods_tree.get_children()
        if not mods:
            messagebox.showinfo("Info", "No mods loaded")
            return
        
        self.log("Checking  "No mods loaded")
            return
        
        self.log("Checking for updates for all mods...")
        
        self.root.config(cursor="wait")
        
        threading.Thread(target=self._check_updates_thread, args=(mods,), daemon=True).start()
    
    def _check_updates_thread(self, mods):
        for item in mods:
            values = self.mods_tree.item(item, "values")
            mod_name = values[0]
            
            self.log(f"Searching for updates for: {mod_name}")
            
            search_results = ModrinthAPI.search_mod(mod_name)
            if search_results:
                mod = search_results[0]
                self.log(f"Found mod: {mod.get('title')} (ID: {mod.get('project_id')})")
                
                versions = ModrinthAPI.get_mod_versions(
                    mod.get('project_id'), 
                    self.version_var.get()
                )
                
                if versions:
                    latest_version = versions[0].get('version_number', 'Unknown')
                    self.log(f"Latest version: {latest_version}")
                    
                    current_version = values[1]
                    if current_version == "Unknown":
                        status = "Unknown"
                    elif latest_version == current_version:
                        status = "Up to date"
                    else:
                        status = "Update available"
                    
                    self.root.after(0, lambda i=item, n=mod_name, c=current_version, l=latest_version, s=status: 
                        self.mods_tree.item(i, values=(n, c, l, s))
                    )
                else:
                    self.log(f"No versions found for {mod_name}")
            else:
                self.log(f"No results found for {mod_name}")
        
        self.log("Update check completed.")
        
        self.root.after(0, lambda: self.root.config(cursor=""))
    
    def update_selected(self):
        selected = self.mods_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No mods selected")
            return
        
        for item in selected:
            values = self.mods_tree.item(item, "values")
            mod_name = values[0]
            
            search_results = ModrinthAPI.search_mod(mod_name)
            if not search_results:
                self.log(f"No results found for {mod_name}")
                continue
            
            mod = search_results[0]
            
            versions = ModrinthAPI.get_mod_versions(
                mod.get('project_id'), 
                self.version_var.get()
            )
            
            if not versions:
                self.log(f"No versions found for {mod_name}")
                continue
            
            dialog = VersionSelectionDialog(self.root, f"Select version for {mod_name}", versions)
            
            if dialog.selected_version:
                selected_version = dialog.selected_version
                version_number = selected_version.get('version_number')
                
                self.log(f"Selected version {version_number} for {mod_name}")
                
                self.mods_tree.item(item, values=(
                    mod_name,
                    version_number,
                    version_number,
                    "Up to date"
                ))
                
                self.log(f"Updated {mod_name} to version {version_number}")
    
    def downgrade_selected(self):
        selected = self.mods_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No mods selected")
            return
        
        for item in selected:
            values = self.mods_tree.item(item, "values")
            mod_name = values[0]
            
            search_results = ModrinthAPI.search_mod(mod_name)
            if not search_results:
                self.log(f"No results found for {mod_name}")
                continue
            
            mod = search_results[0]
            
            versions = ModrinthAPI.get_mod_versions(mod.get('project_id'))
            
            if not versions:
                self.log(f"No versions found for {mod_name}")
                continue
            
            dialog = VersionSelectionDialog(self.root, f"Select version for {mod_name}", versions)
            
            if dialog.selected_version:
                selected_version = dialog.selected_version
                version_number = selected_version.get('version_number')
                
                self.log(f"Selected version {version_number} for {mod_name}")
                
                self.mods_tree.item(item, values=(
                    mod_name,
                    version_number,
                    values[2],
                    "Downgraded"
                ))
                
                self.log(f"Downgraded {mod_name} to version {version_number}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ModManagerApp(root)
    root.mainloop()