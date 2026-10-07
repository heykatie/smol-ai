"""Run tests against a newly created private Postgres cluster, never an app DB."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", required=True, type=Path)
    parser.add_argument("--work-dir", type=Path, default=Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())))
    args = parser.parse_args()
    root = Path(tempfile.mkdtemp(prefix="smolstuff-ci-", dir=str(args.work_dir)))
    socket = Path(tempfile.mkdtemp(prefix="smolstuff-migrations-", dir="/tmp"))
    database = root / "pgdata"
    tools = {name: str(args.pg_bin / name) for name in ("initdb", "pg_ctl")}
    env = dict(os.environ)
    env.update(PGHOST=str(socket), PGPORT="55473", PGUSER=__import__("getpass").getuser(),
               SMOL_TEST_PG_SOCKET=str(socket), DATABASE_URL="", SMOL_SPONSOR_CALLS="0")
    # Explicit empties prevent dotenv from restoring private configuration.
    for key in ("NOVITA_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
                "TAVILY_API_KEY", "ZOOWORK_API_KEY", "ZOOWORK_AGENT_ID"):
        env[key] = ""
    started = False
    try:
        subprocess.run([tools["initdb"], "-D", str(database), "-A", "trust",
                        "--no-locale", "-E", "UTF8"], check=True, env=env)
        subprocess.run([tools["pg_ctl"], "-D", str(database), "-l", str(root / "postgres.log"),
                        "-o", "-k " + str(socket) + " -p 55473 -h '' -c unix_socket_permissions=0700",
                        "start"], check=True, env=env)
        started = True
        report = root / "tests.xml"
        result = subprocess.run([sys.executable, "-m", "pytest", "-q",
                                 "--basetemp", str(root / "pytest"),
                                 "--junitxml", str(report)], env=env)
        if result.returncode:
            return result.returncode
        suites = ET.parse(str(report)).getroot().iter("testsuite")
        if any(int(suite.get("skipped", "0")) for suite in suites):
            print("Full database check requires zero skipped tests.", file=sys.stderr)
            return 1
        return 0
    finally:
        if started:
            subprocess.run([tools["pg_ctl"], "-D", str(database), "-m", "fast", "stop"],
                           check=True, env=env)
        socket.rmdir()
        print("Synthetic test logs and results:", root)


if __name__ == "__main__":
    raise SystemExit(main())
