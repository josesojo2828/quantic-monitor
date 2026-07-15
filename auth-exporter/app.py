#!/usr/bin/env python3
"""auth-exporter — parses auth.log and exposes SSH/security metrics for Prometheus."""

import os
import re
import time
from pathlib import Path

from prometheus_client import start_http_server, Counter, Gauge

PORT = int(os.getenv("PORT", "9101"))
LOG_PATH = os.getenv("LOG_PATH", "/var/log/auth.log")
LOG_PATH_ALT = "/var/log/secure"

# ─── Metrics ───────────────────────────────────────────────────────────

ssh_failed = Counter(
    "auth_ssh_failed_total", "Failed SSH login attempts",
    ["user", "ip", "auth_method"],
)
ssh_success = Counter(
    "auth_ssh_success_total", "Successful SSH logins",
    ["user", "ip", "auth_method"],
)
ssh_failed_by_ip = Gauge(
    "auth_ssh_failed_by_ip", "Failed attempts currently tracked per IP",
    ["ip"],
)
sudo_total = Counter(
    "auth_sudo_total", "Sudo command executions",
    ["user", "command"],
)
auth_lines_total = Counter(
    "auth_lines_processed_total", "Total auth log lines processed",
)

ip_tracker: dict[str, int] = {}

# ─── Patterns ──────────────────────────────────────────────────────────

RE_FAILED = re.compile(
    r"Failed (password|publickey|keyboard-interactive) for\s+"
    r"(?:invalid user\s+)?"
    r"(\S+) from (\S+) port"
)
RE_ACCEPTED = re.compile(
    r"Accepted (password|publickey) for\s+"
    r"(?:invalid user\s+)?"
    r"(\S+) from (\S+) port"
)
RE_SUDO = re.compile(
    r"sudo:\s+(\S+)\s+.*COMMAND=(.*)"
)

# ─── Log parser ───────────────────────────────────────────────────────

def parse_line(line: str):
    auth_lines_total.inc()

    if m := RE_FAILED.search(line):
        method, user, ip = m.group(1), m.group(2), m.group(3)
        ssh_failed.labels(user=user, ip=ip, auth_method=method).inc()
        ip_tracker[ip] = ip_tracker.get(ip, 0) + 1
        ssh_failed_by_ip.labels(ip=ip).set(ip_tracker[ip])

    elif m := RE_ACCEPTED.search(line):
        method, user, ip = m.group(1), m.group(2), m.group(3)
        ssh_success.labels(user=user, ip=ip, auth_method=method).inc()

    elif m := RE_SUDO.search(line):
        user, cmd = m.group(1), m.group(2).strip()
        sudo_total.labels(user=user, command=cmd[:120]).inc()


def follow(file):
    # Go to end, but parse last 100 lines first
    file.seek(0, 2)
    end = file.tell()
    # Read last ~100 lines from end
    chunk = 4096
    if end > chunk:
        file.seek(end - chunk)
        tail = file.readlines()
        for line in tail[-100:]:
            yield line
    file.seek(end)
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.5)
            continue
        yield line

# ─── Main ──────────────────────────────────────────────────────────────

def main():
    log_file = Path(LOG_PATH)
    if not log_file.exists():
        log_file = Path(LOG_PATH_ALT)

    start_http_server(PORT)
    print(f"auth-exporter listening on :{PORT}, watching {log_file}")

    while not log_file.exists():
        time.sleep(2)

    with open(log_file, "r", errors="replace") as f:
        for line in follow(f):
            try:
                parse_line(line.rstrip())
            except Exception as e:
                print(f"parse error: {e}")

if __name__ == "__main__":
    main()
