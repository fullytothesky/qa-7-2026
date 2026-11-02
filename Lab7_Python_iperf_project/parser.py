import re
from pathlib import Path


PATTERN = re.compile(
    r"^\s*\[\s*\d+\]\s+([\d.]+-[\d.]+)\s+sec\s+"
    r"([\d.]+)\s+([KMGT]?Bytes)\s+"
    r"([\d.]+)\s+([KMGT]?bits/sec)\s+"
    r"(\d+)\s+([\d.]+)\s+([KMGT]?Bytes)\s*$"
)

SIZE = {
    "Bytes": 1,
    "KBytes": 1024,
    "MBytes": 1024**2,
    "GBytes": 1024**3,
    "TBytes": 1024**4,
}

RATE = {
    "bits/sec": 1,
    "Kbits/sec": 1000,
    "Mbits/sec": 1000**2,
    "Gbits/sec": 1000**3,
    "Tbits/sec": 1000**4,
}


def parser(output):
    results = []

    for line in output.splitlines():
        match = PATTERN.match(line)
        if not match:
            continue

        interval, transfer, tu, bitrate, bu, retr, cwnd, cu = (
            match.groups()
        )

        results.append({
            "Interval": interval,
            "Transfer": float(transfer) * SIZE[tu] / 1024**2,
            "Bitrate": float(bitrate) * RATE[bu] / 1000**2,
            "Retr": int(retr),
            "Cwnd": float(cwnd) * SIZE[cu] / 1024,
        })

    return results


if __name__ == "__main__":
    output = Path("manual_tcp.txt").read_text()
    intervals = parser(output)

    if not intervals:
        raise SystemExit("ERROR: no intervals found")

    for item in intervals:
        print(item)

    print("Intervals:", len(intervals))
