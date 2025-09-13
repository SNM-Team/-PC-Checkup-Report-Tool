#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
import argparse

OUT_ROOT = Path.cwd() / ("pc_check_" + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))

def ensure_out():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    return OUT_ROOT

def write(path, data, mode="w", binary=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8", errors="ignore")

def safe_run(cmd, shell=False):
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, text=True, timeout=120)
        return r.returncode, r.stdout + "\n" + r.stderr
    except Exception as e:
        return 255, str(e)

def collect_basic_info(out):
    info = {}
    info["platform"] = platform.platform()
    info["system"] = platform.system()
    info["node"] = platform.node()
    info["release"] = platform.release()
    info["version"] = platform.version()
    info["machine"] = platform.machine()
    info["processor"] = platform.processor()
    info["python_version"] = platform.python_version()
    try:
        uname = os.uname()
        info["uname"] = {k: getattr(uname, k) for k in ("sysname","nodename","release","version","machine") if hasattr(uname, k)}
    except Exception:
        pass
    write(out / "basic_info.json", json.dumps(info, indent=2))

def collect_env(out):
    env = dict(os.environ)
    write(out / "env.json", json.dumps(env, indent=2))

def collect_processes(out):
    proc_out = out / "processes.txt"
    try:
        import psutil
        lines = []
        for p in psutil.process_iter(attrs=["pid","name","username","cpu_percent","memory_info","exe","cmdline"]):
            info = p.info
            if "memory_info" in info and info["memory_info"] is not None:
                info["memory_rss"] = getattr(info["memory_info"], "rss", None)
                del info["memory_info"]
            lines.append(info)
        write(proc_out, json.dumps(lines, indent=2))
    except Exception:
        if platform.system() == "Windows":
            code, outp = safe_run(["tasklist", "/V"])
        else:
            code, outp = safe_run(["ps", "aux"])
        write(proc_out, outp)

def collect_services(out):
    svc_out = out / "services.txt"
    if platform.system() == "Windows":
        code, outp = safe_run(["sc", "query", "type=", "service", "state=", "all"])
        write(svc_out, outp)
    else:
        code, outp = safe_run(["systemctl", "list-units", "--type=service", "--all"])
        if code != 0:
            code, outp = safe_run(["service", "--status-all"], shell=False)
        write(svc_out, outp)

def collect_startup_items(out):
    start_out = out / "startup_items.txt"
    lines = []
    if platform.system() == "Windows":
        try:
            import winreg
            roots = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            ]
            for root, path in roots:
                try:
                    k = winreg.OpenKey(root, path)
                    i = 0
                    while True:
                        name, val, _ = winreg.EnumValue(k, i)
                        lines.append({"key": path, "name": name, "value": val})
                        i += 1
                except OSError:
                    pass
        except Exception:
            pass
        code, outp = safe_run(["schtasks", "/Query", "/FO", "LIST", "/V"])
        lines.append({"scheduled_tasks": outp})
    elif platform.system() == "Darwin":
        code, outp = safe_run(["osascript", "-e", 'tell application "System Events" to get the name of every login item'])
        lines.append({"login_items": outp})
        for p in ("/Library/LaunchAgents","/Library/LaunchDaemons", str(Path.home()/ "Library/LaunchAgents")):
            try:
                items = os.listdir(p)
                lines.append({p: items})
            except Exception:
                pass
    else:
        cron = safe_run(["crontab", "-l"])[1]
        lines.append({"crontab": cron})
        for d in ("/etc/cron.daily","/etc/cron.hourly","/etc/cron.weekly","/etc/cron.d"):
            try:
                lines.append({d: os.listdir(d)})
            except Exception:
                pass
    write(start_out, json.dumps(lines, indent=2))

def collect_network(out):
    net_out = out / "network.txt"
    if shutil.which("ss"):
        code, outp = safe_run(["ss", "-tulpen"])
    else:
        code, outp = safe_run(["netstat", "-ano"])
    write(net_out, outp)
    conn_out = out / "connections.txt"
    try:
        import psutil
        conns = []
        for c in psutil.net_connections(kind='inet'):
            conns.append({"fd": c.fd, "family": str(c.family), "type": str(c.type), "laddr": c.laddr._asdict() if c.laddr else None, "raddr": c.raddr._asdict() if c.raddr else None, "status": c.status, "pid": c.pid})
        write(conn_out, json.dumps(conns, indent=2))
    except Exception:
        write(conn_out, "")

def collect_installed(out):
    inst_out = out / "installed_packages.txt"
    lines = {}
    if platform.system() == "Windows":
        code, outp = safe_run(["wmic", "product", "get", "name,version"], shell=False)
        lines["wmic"] = outp
    elif platform.system() == "Darwin":
        code, outp = safe_run(["brew", "list", "--versions"])
        lines["brew"] = outp
    else:
        if shutil.which("dpkg"):
            code, outp = safe_run(["dpkg-query", "-W", "-f=${Package} ${Version}\n"])
            lines["dpkg"] = outp
        elif shutil.which("rpm"):
            code, outp = safe_run(["rpm", "-qa"])
            lines["rpm"] = outp
    try:
        import pkg_resources
        pkgs = sorted([(d.project_name, d.version) for d in pkg_resources.working_set])
        lines["python_packages"] = pkgs
    except Exception:
        pass
    write(inst_out, json.dumps(lines, indent=2, default=str))

def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def collect_recent_hashes(out, max_files=500, max_size=200*1024*1024):
    hits = []
    home = Path.home()
    candidates = []
    for p in ("Downloads","Desktop"):
        d = home / p
        if d.exists():
            for fp in d.rglob("*"):
                if fp.is_file():
                    candidates.append(fp)
    candidates = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[:max_files]
    for fp in candidates:
        try:
            size = fp.stat().st_size
            if size > max_size:
                continue
            h = hash_file(fp)
            hits.append({"path": str(fp), "size": size, "sha256": h, "mtime": datetime.utcfromtimestamp(fp.stat().st_mtime).isoformat()+"Z"})
        except Exception:
            pass
    write(out / "recent_file_hashes.json", json.dumps(hits, indent=2))

def try_external_scanners(out, deep=False):
    scanners = []
    if shutil.which("clamscan"):
        scanners.append("clamscan")
    if shutil.which("clamtk"):
        scanners.append("clamtk")
    results = {}
    for s in scanners:
        if s == "clamscan":
            args = ["clamscan", "-r", "--no-summary", str(Path.home())] if deep else ["clamscan", "-r", "--no-summary", str(Path.home()/ "Downloads")]
            code, outp = safe_run(args)
            results["clamscan"] = {"code": code, "output": outp[:20000]}
    write(out / "external_scans.json", json.dumps(results, indent=2))

def create_zip(out):
    zip_path = Path(str(out) + ".zip")
    shutil.make_archive(str(out), 'zip', root_dir=str(out))
    return zip_path

def main():
    parser = argparse.ArgumentParser(description="PC checkup collector")
    parser.add_argument("--out", "-o", help="Output folder", default=str(OUT_ROOT))
    parser.add_argument("--deep", action="store_true", help="Run deeper/longer scans if available")
    parser.add_argument("--zip", action="store_true", help="Produce zip of results")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    collect_basic_info(out)
    collect_env(out)
    collect_processes(out)
    collect_services(out)
    collect_startup_items(out)
    collect_network(out)
    collect_installed(out)
    collect_recent_hashes(out)
    try_external_scanners(out, deep=args.deep)
    if args.zip:
        z = create_zip(out)
        write(out / "zip_created.txt", str(z))

if __name__ == "__main__":
    main()
