import shlex
import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
from datetime import datetime

AUTO_EXIT_DELAY = 5000  # 5 seconds


# ------------------ Utility ------------------

def run_command(command, log_widget, cwd=None):
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd
        )

        for line in process.stdout:
            log_widget.insert(tk.END, line)
            log_widget.see(tk.END)

        process.wait()

        if process.returncode != 0:
            log_widget.insert(tk.END, f"\n[!] Error running: {command}\n")
            log_widget.insert(tk.END, process.stderr.read())
            return False

        return True

    except Exception as e:
        log_widget.insert(tk.END, f"[!] Exception: {str(e)}\n")
        return False


def sanitize_domain(domain):
    domain = domain.replace("http://", "").replace("https://", "")
    return domain.strip().rstrip("/")


# ------------------ Main Pipeline ------------------

def start_recon(domain, log_widget, start_button, root):
    if not domain:
        messagebox.showerror("Error", "Domain cannot be empty.")
        return

    start_button.config(state=tk.DISABLED)
    log_widget.delete(1.0, tk.END)

    def pipeline():
        clean_domain = sanitize_domain(domain)
        safe_domain = shlex.quote(clean_domain)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(os.getcwd(), f"{clean_domain}_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)

        log_widget.insert(tk.END, f"[+] Target: {clean_domain}\n")
        log_widget.insert(tk.END, f"[+] Output Folder: {output_dir}\n\n")

        # ---------------- Subfinder ----------------
        log_widget.insert(tk.END, "[+] Running subfinder...\n")
        if not run_command(
            f"subfinder -d {safe_domain} -silent > subfinder.txt",
            log_widget,
            cwd=output_dir
        ):
            return

        # ---------------- Assetfinder ----------------
        log_widget.insert(tk.END, "[+] Running assetfinder...\n")
        if not run_command(
            f"assetfinder --subs-only {safe_domain} > assetfinder.txt",
            log_widget,
            cwd=output_dir
        ):
            return

        # ---------------- Merge & Deduplicate ----------------
        log_widget.insert(tk.END, "[+] Merging results...\n")

        subfinder_path = os.path.join(output_dir, "subfinder.txt")
        assetfinder_path = os.path.join(output_dir, "assetfinder.txt")

        combined = set()

        for file_path in [subfinder_path, assetfinder_path]:
            if os.path.exists(file_path):
                with open(file_path) as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            combined.add(line)

        final_domains_path = os.path.join(output_dir, "final_domains.txt")

        with open(final_domains_path, "w") as f:
            for d in sorted(combined):
                f.write(d + "\n")

        log_widget.insert(tk.END, f"[+] Total unique subdomains: {len(combined)}\n")

        # ---------------- Httpx ----------------
        log_widget.insert(tk.END, "[+] Probing with httpx...\n")

        if not run_command(
            "httpx -l final_domains.txt -silent -no-color -status-code > alive_raw.txt",
            log_widget,
            cwd=output_dir
        ):
            return

        # ---------------- Process Alive / Dead ----------------
        log_widget.insert(tk.END, "[+] Processing alive and dead domains...\n")

        alive_raw_path = os.path.join(output_dir, "alive_raw.txt")

        alive_set = set()
        status_map = {}

        if os.path.exists(alive_raw_path):
            with open(alive_raw_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        url = parts[0]
                        code = parts[-1].replace("[", "").replace("]", "")

                        domain_only = url.replace("http://", "").replace("https://", "")
                        domain_only = domain_only.split("/")[0]

                        alive_set.add(domain_only)

                        if code not in status_map:
                            status_map[code] = set()
                        status_map[code].add(domain_only)

        # Write alive domains
        alive_domains_path = os.path.join(output_dir, "alive_domains.txt")
        with open(alive_domains_path, "w") as f:
            for d in sorted(alive_set):
                f.write(d + "\n")

        # Write dead domains
        dead_domains_path = os.path.join(output_dir, "dead_domains.txt")
        dead_set = combined - alive_set

        with open(dead_domains_path, "w") as f:
            for d in sorted(dead_set):
                f.write(d + "\n")

        # Write status code files
        for code, domains in status_map.items():
            status_file_path = os.path.join(output_dir, f"{code}.txt")
            with open(status_file_path, "w") as f:
                for d in sorted(domains):
                    f.write(d + "\n")

        # ---------------- Summary ----------------
        log_widget.insert(tk.END, "\n[✔] Recon Completed Successfully!\n")
        log_widget.insert(tk.END, f"[+] Alive: {len(alive_set)}\n")
        log_widget.insert(tk.END, f"[+] Dead: {len(dead_set)}\n")
        log_widget.insert(tk.END, f"[+] Status codes found: {', '.join(status_map.keys())}\n")
        log_widget.insert(tk.END, f"[+] Auto exiting in {AUTO_EXIT_DELAY // 1000} seconds...\n")

        root.after(AUTO_EXIT_DELAY, root.destroy)

    threading.Thread(target=pipeline).start()


# ------------------ GUI ------------------

root = tk.Tk()
root.title("Recon Automation Tool - Clean Version")
root.geometry("800x520")
root.resizable(False, False)

tk.Label(root, text="Enter Target Domain:", font=("Arial", 12)).pack(pady=5)

domain_entry = tk.Entry(root, width=50, font=("Arial", 11))
domain_entry.pack(pady=5)

log_area = scrolledtext.ScrolledText(root, width=95, height=24)
log_area.pack(pady=10)

start_btn = tk.Button(
    root,
    text="Start Recon",
    font=("Arial", 11),
    bg="#222",
    fg="white",
    command=lambda: start_recon(domain_entry.get(), log_area, start_btn, root)
)
start_btn.pack(pady=5)

root.mainloop()
