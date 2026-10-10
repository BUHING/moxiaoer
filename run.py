"""Start the GrindBuddy development preview."""

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start GrindBuddy backend and frontend services.")
    parser.add_argument("--host", default="127.0.0.1", help="Address on which both services listen.")
    parser.add_argument("--backend-port", type=int, default=8000, help="Django server port.")
    parser.add_argument("--frontend-port", type=int, default=5173, help="Vite server port.")
    return parser.parse_args()


def load_environment_file(path: Path, environment: dict[str, str]) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
            continue
        key, value = stripped_line.split("=", maxsplit=1)
        environment.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def port_is_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.2)
        return connection.connect_ex((host, port)) == 0


def run_command(command: list[str], environment: dict[str, str]) -> None:
    subprocess.run(command, cwd=ROOT_DIR, env=environment, check=True)


def stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def main() -> int:
    arguments = parse_arguments()
    uv_command = shutil.which("uv")
    npm_command = shutil.which("npm.cmd") or shutil.which("npm")
    if uv_command is None or npm_command is None:
        missing_commands = []
        if uv_command is None:
            missing_commands.append("uv")
        if npm_command is None:
            missing_commands.append("npm")
        print(f"Missing required command(s): {', '.join(missing_commands)}", file=sys.stderr)
        return 1
    if port_is_in_use(arguments.host, arguments.backend_port):
        print(f"Backend port {arguments.host}:{arguments.backend_port} is already in use.", file=sys.stderr)
        return 1
    if port_is_in_use(arguments.host, arguments.frontend_port):
        print(f"Frontend port {arguments.host}:{arguments.frontend_port} is already in use.", file=sys.stderr)
        return 1

    environment = os.environ.copy()
    load_environment_file(BACKEND_DIR / ".env", environment)
    load_environment_file(FRONTEND_DIR / ".env", environment)
    environment["DJANGO_SETTINGS_MODULE"] = "config.settings.development"
    proxy_host = "127.0.0.1" if arguments.host in {"0.0.0.0", "::"} else arguments.host
    environment["VITE_API_BASE_URL"] = "/api/v1"
    environment["VITE_DEV_API_ORIGIN"] = f"http://{proxy_host}:{arguments.backend_port}"

    try:
        run_command([uv_command, "--directory", "backend", "sync"], environment)
        run_command([npm_command, "--prefix", "frontend", "install"], environment)
        run_command(
            [uv_command, "--directory", "backend", "run", "python", "manage.py", "migrate"],
            environment,
        )
    except subprocess.CalledProcessError as error:
        return error.returncode

    backend_process = subprocess.Popen(
        [
            uv_command,
            "--directory",
            "backend",
            "run",
            "python",
            "manage.py",
            "runserver",
            f"{arguments.host}:{arguments.backend_port}",
        ],
        cwd=ROOT_DIR,
        env=environment,
    )
    frontend_process = subprocess.Popen(
        [
            npm_command,
            "--prefix",
            "frontend",
            "run",
            "dev",
            "--",
            "--host",
            arguments.host,
            "--port",
            str(arguments.frontend_port),
            "--strictPort",
        ],
        cwd=ROOT_DIR,
        env=environment,
    )
    browser_host = "127.0.0.1" if arguments.host in {"0.0.0.0", "::"} else arguments.host
    frontend_url = f"http://{browser_host}:{arguments.frontend_port}/"
    print(f"\nGrindBuddy is starting at {frontend_url}")
    print("Press Ctrl+C to stop both services.")

    try:
        while True:
            if backend_process.poll() is not None:
                return backend_process.returncode or 1
            if frontend_process.poll() is not None:
                return frontend_process.returncode or 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 0
    finally:
        stop_process(frontend_process)
        stop_process(backend_process)


if __name__ == "__main__":
    raise SystemExit(main())