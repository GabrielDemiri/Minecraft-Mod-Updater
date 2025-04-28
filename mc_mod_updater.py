import os
import sys
import time
import json
import requests
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

MODRINTH_API = "https://api.modrinth.com/v2/search"
MINECRAFT_VERSION = "1.21.5"
CURSEFORGE_API = "https://api.curseforge.com/v1/mods/search"
CURSEFORGE_API_KEY = "COOMING_SOON"
DEFAULT_MODS_DIR = os.path.expandvars(r"%AppData%\\.minecraft\\mods")
TEMP_DIR = os.path.expandvars(r"%TEMP%\\mc_mods_updater_logs")


os.makedirs(TEMP_DIR, exist_ok=True)

def log_message(message, level="info"):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    color = {"info": "yellow", "error": "red", "normal": "white"}.get(level, "white")
    log_text.config(state='normal')
    log_text.insert(tk.END, f"{timestamp} {message}\n", (color,))
    log_text.see(tk.END)
    log_text.config(state='disabled')
    try:
        log_file_path = os.path.join(TEMP_DIR, "mc_mods_updater.log")
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {message}\n")
    except Exception as e:
        print("Failed saving log:", e)


def check_internet():
    try:
        requests.get("https://modrinth.com", timeout=5)
        return True
    except:
        return False


def search_curseforge(mod_name):
    headers = {"x-api-key": CURSEFORGE_API_KEY}
    params = {"gameId": 432, "searchFilter": mod_name, "pageSize": 1}
    try:
        r = requests.get(CURSEFORGE_API, params=params, headers=headers)
        if r.status_code == 200:
            results = r.json().get("data", [])
            if results:
                return results[0]
    except:
        pass
    return None


def search_modrinth(mod_name):
    params = {"query": mod_name, "limit": 1}
    try:
        r = requests.get(MODRINTH_API, params=params)
        if r.status_code == 200:
            results = r.json().get("hits", [])
            if results:
                return results[0]
    except:
        pass
    return None


def update_mods():
    mods_path = mods_dir.get()
    if not os.path.exists(mods_path):
        messagebox.showerror("Error", "Mods directory not found.")
        return

    mods = [f for f in os.listdir(mods_path) if f.endswith(".jar")]
    if not mods:
        log_message("No mods found.", "warning")
        return

    total = len(mods)
    done = 0

    for mod in mods:
        mod_base = os.path.splitext(mod)[0]
        log_message(f"Searching updates for {mod_base}...", "normal")

        data = search_modrinth(mod_base)
        if not data:
            data = search_curseforge(mod_base)

        if not data:
            log_message(f"⚠️ Skipped: {mod_base} (Not found)", "warning")
        else:
            log_message(f"✅ No updates needed for {mod_base}", "normal")

        done += 1
        progress_var.set(int((done / total) * 100))
        window.update_idletasks()

    log_message(f"Logs saved in: {TEMP_DIR}", "info")
    messagebox.showinfo("Done", "Mods checked.")


def clear_logs():
    log_text.config(state='normal')
    log_text.delete(1.0, tk.END)
    log_text.config(state='disabled')
    try:
        for file in os.listdir(TEMP_DIR):
            os.remove(os.path.join(TEMP_DIR, file))
        log_message("Logs cleared.", "info")
    except Exception as e:
        log_message(f"Error clearing logs: {e}", "error")


def browse_folder():
    path = filedialog.askdirectory()
    if path:
        mods_dir.set(path)



window = tk.Tk()
window.title("Minecraft Mods Updater")
window.geometry("700x500")
window.configure(bg="#1e1e1e")

mods_dir = tk.StringVar(value=DEFAULT_MODS_DIR)
progress_var = tk.IntVar()

frame = tk.Frame(window, bg="#1e1e1e")
frame.pack(pady=10)

entry = tk.Entry(frame, textvariable=mods_dir, width=60, bg="#2e2e2e", fg="white", insertbackground='white')
entry.pack(side=tk.LEFT, padx=5)

browse_btn = tk.Button(frame, text="📁", command=browse_folder, bg="#3e3e3e", fg="white")
browse_btn.pack(side=tk.LEFT)

update_btn = tk.Button(window, text="Update Mods", command=lambda: threading.Thread(target=update_mods).start(), bg="#0078d7", fg="white")
update_btn.pack(pady=5)

clear_btn = tk.Button(window, text="Clear Logs", command=clear_logs, bg="#d77f00", fg="white")
clear_btn.pack(pady=5)

style = ttk.Style()
style.theme_use('clam')
style.configure("TProgressbar", troughcolor="#2e2e2e", background="#00ff00", bordercolor="#2e2e2e", lightcolor="#2e2e2e", darkcolor="#2e2e2e")

progress = ttk.Progressbar(window, variable=progress_var, maximum=100, style="TProgressbar")
progress.pack(fill=tk.X, padx=20, pady=10)

log_text = tk.Text(window, state='disabled', bg="#2e2e2e", fg="white")
log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

for level, color in {"yellow": "#f0e130", "red": "#ff5555", "white": "#ffffff"}.items():
    log_text.tag_config(level, foreground=color)

if not check_internet():
    messagebox.showerror("No Internet", "Internet connection is required!")
    window.destroy()
    sys.exit()

try:
    log_file_path = os.path.join(TEMP_DIR, "mc_mods_updater.log")
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8") as f:
            old_logs = f.read()
        log_text.config(state='normal')
        log_text.insert(tk.END, old_logs)
        log_text.config(state='disabled')
except:
    pass

window.mainloop()