import argparse
import subprocess
from pathlib import Path

from parser import parser


def client(server_ip, port=5201, bitrate=None):
    command = [
        "iperf3", "-c", server_ip,
        "-p", str(port),
        "-t", "10", "-i", "1", "-f", "m",
        "--connect-timeout", "3000",
    ]

    if bitrate:
        command.extend(["-b", bitrate])

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output, error = process.communicate(timeout=20)

    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
        return output, "iperf3 exceeded the 20-second timeout"

    except OSError as exc:
        return "", str(exc)

    if process.returncode and not error:
        error = f"iperf3 exit code: {process.returncode}"

    return output, error


if __name__ == "__main__":
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--server", default="10.0.0.1")
    arguments.add_argument("--port", type=int, default=5201)
    arguments.add_argument("--bitrate", default=None)
    arguments.add_argument("--output", default="python_tcp.txt")
    args = arguments.parse_args()

    output, error = client(args.server, args.port, args.bitrate)

    Path(args.output).write_text(output, encoding="utf-8")
    Path(args.output + ".stderr").write_text(
        error, encoding="utf-8"
    )

    if error:
        raise SystemExit("FAIL: " + error.strip())

    intervals = parser(output)

    if not intervals:
        raise SystemExit("FAIL: no intervals found")

    for item in intervals:
        print(
            f"{item['Interval']}: "
            f"Transfer={item['Transfer']:.2f} MBytes, "
            f"Bitrate={item['Bitrate']:.2f} Mbits/sec"
        )

    passed = all(
        item["Transfer"] > 2 and item["Bitrate"] > 20
        for item in intervals
    )

    print("Intervals:", len(intervals))
    print("PASS" if passed else "FAIL")
    raise SystemExit(0 if passed else 1)
