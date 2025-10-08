import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
import sys
import psutil
from datetime import datetime

api_process = None
stop_reading = False


# --- Helper: Update Status Indicator ---
def update_status(is_running):
    if is_running:
        status_label.config(text="🟢 API Running", fg="green")
    else:
        status_label.config(text="🔴 API Stopped", fg="red")


# --- Log helper with timestamp ---
def add_log(message, prefix="ℹ️", separator=False):
    """Insert timestamped log entry at the top (newest first)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {prefix} {message}\n"

    if separator:
        formatted = (
            "\n" + "-" * 60 + f"\n[{timestamp}] {prefix} {message}\n" + "-" * 60 + "\n"
        )

    log_box.insert("1.0", formatted)  # Insert newest log at top
    log_box.see("1.0")  # Keep view at top


# --- Run API ---
def run_api():
    global api_process, stop_reading

    if api_process and api_process.poll() is None:
        messagebox.showinfo("Info", "API is already running.")
        return

    stop_reading = False
    add_log("Starting FastAPI server...", "🚀", separator=True)
    update_status(False)

    def start():
        global api_process
        try:
            # Detect if running from PyInstaller EXE
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
                python_executable = "python"  # system Python
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                python_executable = sys.executable

            main_path = os.path.join(base_dir, "main.py")

            # If main.py not found → show readable error
            if not os.path.exists(main_path):
                add_log(f"Cannot find main.py at {main_path}", "❌", separator=True)
                return

            api_process = subprocess.Popen(
                [python_executable, "-m", "uvicorn", f"{main_path}:app", "--host", "0.0.0.0", "--port", "8001"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=base_dir  # important — ensures working directory consistency
            )

            update_status(True)
            add_log("Opening Swagger UI at http://127.0.0.1:8001/docs", "🌐")
            threading.Timer(2, lambda: os.system("start http://127.0.0.1:8001/docs")).start()
            read_logs()

        except Exception as e:
            add_log(f"Failed to start API: {e}", "❌", separator=True)
            update_status(False)

    threading.Thread(target=start, daemon=True).start()


# --- Read Logs (non-blocking) ---
def read_logs():
    global api_process, stop_reading

    def _read():
        if not api_process:
            return
        for line in iter(api_process.stdout.readline, ''):
            if stop_reading:
                break
            if line.strip():
                add_log(line.strip(), "📜")
        api_process.stdout.close()

    threading.Thread(target=_read, daemon=True).start()


# --- Stop API (cross-platform, using psutil) ---
def stop_api():
    global api_process, stop_reading
    if not api_process or api_process.poll() is not None:
        messagebox.showinfo("Info", "API is not running.")
        update_status(False)
        return

    add_log("Stopping FastAPI server...", "🛑", separator=True)

    try:
        stop_reading = True
        process = psutil.Process(api_process.pid)

        # Terminate child processes (like uvicorn workers)
        for child in process.children(recursive=True):
            child.terminate()

        process.terminate()
        gone, still_alive = psutil.wait_procs([process], timeout=5)
        for p in still_alive:
            p.kill()

        api_process = None
        add_log("API stopped successfully.", "✅")
        update_status(False)

    except Exception as e:
        add_log(f"Error stopping API: {e}", "❌")
        update_status(False)


# --- Restart API ---
def restart_api():
    add_log("Restarting API...", "🔁", separator=True)
    stop_api()
    run_api()


# --- Settings Placeholder ---
def open_settings():
    messagebox.showinfo("Settings", "Settings menu placeholder — coming soon!")


# --- GUI Layout ---
root = tk.Tk()
root.title("FastAPI Control Panel")
root.geometry("700x520")
root.resizable(False, False)

title = tk.Label(root, text="🚀 FastAPI Local Server Controller", font=("Segoe UI", 16, "bold"))
title.pack(pady=10)

# --- Button Row ---
frame = tk.Frame(root)
frame.pack(pady=5)

btn_run = tk.Button(frame, text="▶️ Run API", width=15, command=run_api)
btn_run.grid(row=0, column=0, padx=5)

btn_restart = tk.Button(frame, text="🔁 Restart", width=15, command=restart_api)
btn_restart.grid(row=0, column=1, padx=5)

btn_stop = tk.Button(frame, text="⏹️ Stop", width=15, command=stop_api)
btn_stop.grid(row=0, column=2, padx=5)

btn_settings = tk.Button(frame, text="⚙️ Settings", width=15, command=open_settings)
btn_settings.grid(row=0, column=3, padx=5)

# --- Status Indicator ---
status_label = tk.Label(root, text="🔴 API Stopped", font=("Segoe UI", 12, "bold"), fg="red")
status_label.pack(pady=10)

# --- Log output area ---
log_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20, font=("Consolas", 10))
log_box.pack(padx=10, pady=10)
add_log("Ready.", "✅", separator=True)

# --- Initialize ---
update_status(False)

root.mainloop()