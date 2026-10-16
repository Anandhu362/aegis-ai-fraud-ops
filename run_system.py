"""Unified Orchestrator for Aegis AI Fraud Ops.

Launches and monitors all ecosystem microservices and frontend concurrently:
1. Actuator Service        (port 8070)
2. Multi-Agent Engine      (port 8090)
3. API Gateway             (port 8080)
4. React SOC Dashboard     (port 5173)
5. [Optional] Live Traffic Simulator (--traffic / --simulate)

Handles automatic port checking, health readiness probes, consolidated logging,
and graceful signal termination on Windows and POSIX systems.
"""

# ruff: noqa: S603, S607, S602, S605, S110, S310, SIM105, PLR0915, E501

import argparse
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import dotenv

# Force UTF-8 encoding on standard streams to avoid Windows charmap errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ANSI Terminal Colors
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

WORKSPACE_ROOT = Path(__file__).resolve().parent
dotenv.load_dotenv(WORKSPACE_ROOT / ".env", override=True)

# Locate Python executable in .venv if available
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)


SERVICES = [
    {
        "name": "Actuator Service",
        "tag": "ACTUATOR",
        "color": CYAN,
        "port": 8070,
        "health_url": "http://127.0.0.1:8070/healthz",
        "cwd": WORKSPACE_ROOT,
        "cmd": [
            str(VENV_PYTHON),
            "-m",
            "uvicorn",
            "aegis_actuator.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8070",
        ],
    },
    {
        "name": "Multi-Agent Engine",
        "tag": "ENGINE",
        "color": "\033[95m",  # Magenta
        "port": 8090,
        "health_url": "http://127.0.0.1:8090/healthz",
        "cwd": WORKSPACE_ROOT,
        "cmd": [
            str(VENV_PYTHON),
            "-m",
            "uvicorn",
            "aegis_engine.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8090",
        ],
    },
    {
        "name": "API Gateway",
        "tag": "GATEWAY",
        "color": "\033[94m",  # Blue
        "port": 8080,
        "health_url": "http://127.0.0.1:8080/healthz",
        "cwd": WORKSPACE_ROOT,
        "cmd": [
            str(VENV_PYTHON),
            "-m",
            "uvicorn",
            "aegis_gateway.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8080",
        ],
    },
    {
        "name": "React SOC Dashboard",
        "tag": "FRONTEND",
        "color": GREEN,
        "port": 5173,
        "health_url": "http://127.0.0.1:5173",
        "cwd": WORKSPACE_ROOT / "frontend",
        "cmd": ["npm", "run", "dev"],
        "is_npm": True,
    },
]


def check_url(url: str, timeout: float = 1.0) -> bool:
    """Return True if URL responds with HTTP 200 or 304."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AegisRunner/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 304)
    except Exception:
        return False


def stream_pipe(stream: object, tag: str, color: str) -> None:
    """Continuously drain child process stdout stream to prevent OS pipe buffer deadlocks."""
    if stream is None:
        return
    try:
        readline = getattr(stream, "readline", None)
        if not readline:
            return
        for line in iter(readline, ""):
            if not line:
                break
            sys.stdout.write(f"  {color}[{tag}]{RESET} {line}")
            sys.stdout.flush()
    except Exception:
        pass


def kill_process_tree(pid: int) -> None:
    """Gracefully or forcefully kill process and its children on Windows/Unix."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass


def free_port_if_stale(port: int) -> None:
    """Check if port is already listening. If so, attempt to free it on Windows."""
    if os.name == "nt":
        try:
            out = subprocess.check_output(
                f"netstat -ano | findstr :{port}",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            for line in out.strip().splitlines():
                if "LISTENING" in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    if pid.isdigit() and int(pid) != os.getpid():
                        print(
                            f"{YELLOW}[!] Port {port} occupied by PID {pid}. Terminating...{RESET}"
                        )
                        subprocess.run(
                            ["taskkill", "/F", "/PID", pid],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                        )
        except Exception:
            pass


def main() -> None:
    """Entrypoint for the combined system runner."""
    parser = argparse.ArgumentParser(description="Aegis AI Fraud Ops - System Runner")
    parser.add_argument(
        "--traffic",
        "--simulate",
        action="store_true",
        help="Also launch continuous live transaction traffic simulation in the background",
    )
    parser.add_argument(
        "--fraud-ratio",
        type=float,
        default=0.15,
        help="Adversarial attack ratio for simulator (default: 0.15 for active Gemini calls)",
    )
    parser.add_argument(
        "--no-frontend",
        action="store_true",
        help="Run backend microservices only (exclude frontend Vite server)",
    )
    args = parser.parse_args()

    # Clear terminal screen
    os.system("cls" if os.name == "nt" else "clear")

    print(
        f"{BOLD}{CYAN}========================================================================{RESET}"
    )
    print(
        f"{BOLD}{CYAN}            AEGIS AI FRAUD OPS - UNIFIED ECOSYSTEM RUNNER               {RESET}"
    )
    print(
        f"{BOLD}{CYAN}========================================================================{RESET}"
    )
    print(f"{DIM}Python Environment: {VENV_PYTHON}{RESET}")
    print(f"{DIM}Workspace Root:     {WORKSPACE_ROOT}{RESET}\n")

    services_to_run = [s for s in SERVICES if not (args.no_frontend and s.get("is_npm"))]

    # Pre-flight: Check and clear stale ports
    print(f"{BOLD}[1/3] Checking Port Availability...{RESET}")
    for svc in services_to_run:
        port = svc["port"]
        if check_url(svc["health_url"], timeout=0.4):
            print(f"  {YELLOW}* Port {port} ({svc['name']}) is currently active.{RESET}")
        else:
            free_port_if_stale(port)
            print(f"  {GREEN}[OK] Port {port} available for {svc['name']}.{RESET}")

    # Launch subprocesses
    print(f"\n{BOLD}[2/3] Booting Up Microservices & UI...{RESET}")
    processes: list[tuple[dict, subprocess.Popen]] = []

    for svc in services_to_run:
        name = svc["name"]
        cmd = svc["cmd"]
        cwd = svc["cwd"]
        is_npm = svc.get("is_npm", False)

        use_shell = os.name == "nt" and is_npm
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=dict(os.environ),
            )
            processes.append((svc, proc))
            threading.Thread(
                target=stream_pipe,
                args=(proc.stdout, svc["tag"], svc["color"]),
                daemon=True,
            ).start()
            print(f"  {CYAN}[>] Started {name} (PID {proc.pid}) on port {svc['port']}...{RESET}")
        except Exception as exc:
            print(f"  {RED}[X] Failed to start {name}: {exc}{RESET}")
            sys.exit(1)

    # Optional Traffic Simulator
    traffic_proc = None
    if args.traffic:
        print(
            f"  {CYAN}[>] Launching Live Traffic Streamer (Fraud Ratio: {args.fraud_ratio})...{RESET}"
        )
        sim_cmd = [
            str(VENV_PYTHON),
            "-u",
            "simulation/src/aegis_sim/stream_live_traffic.py",
            "--delay",
            "2.5",
            "--fraud-ratio",
            str(args.fraud_ratio),
        ]
        traffic_proc = subprocess.Popen(
            sim_cmd,
            cwd=str(WORKSPACE_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=dict(os.environ),
        )
        threading.Thread(
            target=stream_pipe,
            args=(traffic_proc.stdout, "TRAFFIC", YELLOW),
            daemon=True,
        ).start()

    # Health polling
    print(f"\n{BOLD}[3/3] Awaiting System Readiness...{RESET}")
    ready: dict[str, bool] = {s["name"]: False for s in services_to_run}
    max_wait = 30
    start_time = time.time()

    while time.time() - start_time < max_wait:
        all_ready = True
        for svc in services_to_run:
            name = svc["name"]
            if not ready[name]:
                if check_url(svc["health_url"]):
                    ready[name] = True
                    print(
                        f"  {GREEN}[OK] {name} is ONLINE and healthy! ({svc['health_url']}){RESET}"
                    )
                else:
                    all_ready = False
        if all_ready:
            break
        time.sleep(1.0)

    # Display operational endpoints
    print(
        f"\n{BOLD}{GREEN}========================================================================{RESET}"
    )
    print(
        f"{BOLD}{GREEN}                 AEGIS AI FRAUD OPS IS FULLY OPERATIONAL!               {RESET}"
    )
    print(
        f"{BOLD}{GREEN}========================================================================{RESET}"
    )
    print(f"  {BOLD}* SOC Web Dashboard:{RESET}   {CYAN}http://localhost:5173{RESET}")
    print(f"  {BOLD}* API Gateway & Docs:{RESET}  {CYAN}http://127.0.0.1:8080/docs{RESET}")
    print(f"  {BOLD}* Multi-Agent Engine:{RESET}  {CYAN}http://127.0.0.1:8090/health{RESET}")
    print(f"  {BOLD}* Bank Actuator API:{RESET}   {CYAN}http://127.0.0.1:8070/health{RESET}")
    if args.traffic and traffic_proc:
        print(
            f"  {BOLD}* Traffic Simulator:{RESET}   {YELLOW}STREAMING ACTIVE (PID {traffic_proc.pid}){RESET}"
        )
    print(f"{DIM}Press Ctrl+C anytime to cleanly shut down all services.{RESET}\n")

    # Monitor and stream consolidated logs
    def shutdown_all(*_: object) -> None:
        print(f"\n{YELLOW}[*] Received termination signal. Gracefully shutting down...{RESET}")
        if traffic_proc:
            kill_process_tree(traffic_proc.pid)
        for svc, proc in processes:
            print(f"  {DIM}Stopping {svc['name']} (PID {proc.pid})...{RESET}")
            kill_process_tree(proc.pid)
        print(f"{GREEN}[OK] All Aegis services stopped cleanly.{RESET}")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_all)
    signal.signal(signal.SIGTERM, shutdown_all)

    try:
        # Keep process alive and monitor child states
        while True:
            for svc, proc in processes:
                if proc.poll() is not None:
                    print(
                        f"{RED}[!] Service {svc['name']} exited prematurely (Code {proc.returncode}).{RESET}"
                    )
            time.sleep(2.0)
    except KeyboardInterrupt:
        shutdown_all()


if __name__ == "__main__":
    main()
