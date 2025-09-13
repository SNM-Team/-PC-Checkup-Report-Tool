# 🖥️ PC Checkup & Report Tool

A cross-platform **Python utility** that performs a full **system checkup** and saves the results in a structured report.  
It collects useful diagnostics (processes, services, startup items, network connections, installed software, hashes of recent downloads, and more) to help you inspect your machine for unusual activity or troubleshoot issues.  

> ⚠️ This tool **does not hack, modify, or delete** anything on your computer.  
> It only **collects information and runs optional antivirus checks** (ClamAV, etc. if installed).  

---

## ✨ Features

- 📋 Collects **system info** (OS, hardware, Python version).  
- ⚙️ Lists **running processes, services, startup items**.  
- 🌐 Captures **network connections & open ports**.  
- 📦 Exports a list of **installed packages/software**.  
- 🔒 Generates **SHA-256 hashes of recent files** (e.g. Downloads).  
- 🛡️ Optionally runs **external scanners** (ClamAV if available).  
- 📂 Saves everything as **JSON / TXT reports**.  
- 📦 Can export results as a single **.zip archive** for easy sharing.  

---

## 📸 Screenshots / Preview

<p align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" width="120" alt="System Check Icon"/>
  <img src="https://cdn-icons-png.flaticon.com/512/3135/3135714.png" width="120" alt="Report Icon"/>
  <img src="https://cdn-icons-png.flaticon.com/512/3135/3135716.png" width="120" alt="Security Icon"/>
</p>

---

## 🚀 Installation

1. Clone this repo:
   ```bash
   git clone https://github.com/your-username/pc-checkup.git
   cd pc-checkup
Install requirements (optional, only needed for extended functionality):

bash
Kopijuoti kodą
pip install psutil
▶️ Usage
Basic run:

bash
Kopijuoti kodą
python3 pc_check.py
Save to a custom folder:

bash
Kopijuoti kodą
python3 pc_check.py --out /path/to/save/report
Run deeper scans (if ClamAV available):

bash
Kopijuoti kodą
python3 pc_check.py --deep
Export results to a ZIP archive:

bash
Kopijuoti kodą
python3 pc_check.py --zip
Combine options:

bash
Kopijuoti kodą
python3 pc_check.py --deep --zip --out ~/pc_report
🧾 Example Output Structure
pgsql
Kopijuoti kodą
pc_check_20250913/
├── basic_info.json
├── env.json
├── processes.txt
├── services.txt
├── startup_items.txt
├── network.txt
├── connections.txt
├── installed_packages.txt
├── recent_file_hashes.json
├── external_scans.json
└── zip_created.txt
🛡️ Notes
On Windows, run inside an elevated (Administrator) PowerShell.

On Linux/macOS, run with sudo for more complete results.

If ClamAV is installed, the script can trigger scans automatically.

The tool is designed for diagnostics and transparency, not for automatic virus removal.

📜 License
MIT License © 2025 SNM-TEAM

<p align="center"> <img src="https://cdn-icons-png.flaticon.com/512/1827/1827504.png" width="80" alt="Done Icon"/> <br> Made with ❤️ for safer computing. </p> ```
