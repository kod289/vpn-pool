from pathlib import Path
from urllib.parse import urlsplit
import socket
import concurrent.futures
import re

INPUT = Path("output/unique.txt")
ALIVE = Path("output/reachable.txt")
DEAD = Path("output/unreachable.txt")
STATS = Path("output/check_stats.txt")

TIMEOUT = 5
WORKERS = 30


def get_endpoint(config):
    try:
        parsed = urlsplit(config)

        host = parsed.hostname
        port = parsed.port

        if not host or not port:
            return None

        return host, port

    except Exception:
        return None


def check(config):
    endpoint = get_endpoint(config)

    if not endpoint:
        return config, False, "invalid"

    host, port = endpoint

    try:
        with socket.create_connection(
            (host, port),
            timeout=TIMEOUT
        ):
            return config, True, "tcp_ok"

    except socket.timeout:
        return config, False, "timeout"

    except OSError as e:
        return config, False, type(e).__name__

    except Exception as e:
        return config, False, type(e).__name__


configs = [
    x.strip()
    for x in INPUT.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()
    if x.strip()
]

alive = []
dead = []

print(f"Checking {len(configs)} endpoints...")

with concurrent.futures.ThreadPoolExecutor(
    max_workers=WORKERS
) as executor:

    futures = [
        executor.submit(check, config)
        for config in configs
    ]

    for i, future in enumerate(
        concurrent.futures.as_completed(futures),
        start=1
    ):
        config, ok, reason = future.result()

        if ok:
            alive.append(config)
        else:
            dead.append(config)

        if i % 50 == 0 or i == len(configs):
            print(
                f"{i}/{len(configs)} "
                f"alive={len(alive)} "
                f"dead={len(dead)}"
            )


alive.sort()
dead.sort()

ALIVE.write_text(
    "\n".join(alive) + "\n",
    encoding="utf-8"
)

DEAD.write_text(
    "\n".join(dead) + "\n",
    encoding="utf-8"
)

stats = [
    f"Input endpoints: {len(configs)}",
    f"TCP reachable: {len(alive)}",
    f"TCP unreachable: {len(dead)}",
    f"Reachable percentage: "
    f"{(len(alive) / len(configs) * 100):.1f}%"
    if configs else
    "Reachable percentage: 0%",
]

STATS.write_text(
    "\n".join(stats) + "\n",
    encoding="utf-8"
)

print()
print("\n".join(stats))
          
