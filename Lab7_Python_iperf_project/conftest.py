import os
import time
from pathlib import Path

import paramiko
import pytest

from client import client as run_client


def pytest_addoption(parser):
    parser.addoption("--bitrate", default=None)
    parser.addoption("--client-port", type=int, default=5201)
    parser.addoption("--result-name", default="pytest_tcp")


@pytest.fixture
def server():
    password = os.environ.get("LAB_SSH_PASSWORD")
    if not password:
        pytest.fail("Set LAB_SSH_PASSWORD before running pytest")

    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    pid = None

    try:
        ssh.connect(
            "10.0.0.1",
            username="vlad",
            password=password,
            look_for_keys=False,
            allow_agent=False,
            timeout=10,
            banner_timeout=10,
            auth_timeout=10,
        )

        _, output, error = ssh.exec_command(
            "echo $$; exec iperf3 -s -p 5201",
            timeout=10,
        )
        pid = int(output.readline().strip())

        for _ in range(30):
            if output.channel.exit_status_ready():
                pytest.fail(
                    "Server failed: " + error.read().decode()
                )

            _, ready, _ = ssh.exec_command(
                "ss -ltnH 'sport = :5201'",
                timeout=5,
            )
            if ready.read().strip():
                break

            time.sleep(0.1)
        else:
            pytest.fail("Server did not start")

        print("SETUP: iperf3 server started through SSH")
        yield "10.0.0.1"

    finally:
        try:
            if pid is not None:
                _, done, _ = ssh.exec_command(
                    f"kill -INT {pid}",
                    timeout=5,
                )
                done.channel.recv_exit_status()
                print("TEARDOWN: iperf3 server stopped")
        finally:
            ssh.close()


@pytest.fixture
def client(server, request):
    config = request.config
    output, error = run_client(
        server,
        port=config.getoption("--client-port"),
        bitrate=config.getoption("--bitrate"),
    )

    folder = Path("results")
    folder.mkdir(exist_ok=True)
    name = config.getoption("--result-name")

    (folder / (name + ".txt")).write_text(
        output, encoding="utf-8"
    )
    (folder / (name + ".stderr")).write_text(
        error, encoding="utf-8"
    )

    return output, error
