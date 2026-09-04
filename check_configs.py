from pathlib import Path
from urllib.parse import urlsplit
import socket
import concurrent.futures
import time

INPUT = Path("output/unique.txt")
ALIVE = Path("output/reachable.txt")
DEAD = Path("output/unreachable.txt")
STATS = Path("output/check_stats.txt")

TIMEOUT = 3
WORKERS = 50
RETRIES = 2


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


def check_once(host, port):
    started = time.perf_counter()

    try:
        with socket.create_connection(
            (host, port),
            timeout=TIMEOUT
        ):
            latency = (time.perf_counter() - started) * 1000
            return True, latency, "tcp_ok"

    except socket.timeout:
        return False, None, "timeout"

    except OSError as e:
        return False, None, type(e).__name__

    except Exception as e:
        return False, None, type(e).__name__


def check(config):
    endpoint = get_endpoint(config)

    if not endpoint:
        return config, False, None, "invalid"

    host, port = endpoint

    best_latency = None
    last_reason = "unknown"

    for attempt in range(RETRIES + 1):
        ok, latency, reason = check_once(host, port)

        if ok:
            if best_latency is None or latency < best_latency:
                best_latency = latency

            # Одного успешного соединения достаточно,
            # но продолжаем не нужно.
            return config, True, best_latency, "tcp_ok"

        last_reason = reason

    return config, False, None, last_reason


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
results = []

print(
    f"Checking {len(configs)} endpoints "
    f"(timeout={TIMEOUT}s, retries={RETRIES})..."
)

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
        config, ok, latency, reason = future.result()

        results.append(
            (config, ok, latency, reason)
        )

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
    "\n".join(alive) + ("\n" if alive else ""),
    encoding="utf-8"
)

DEAD.write_text(
    "\n".join(dead) + ("\n" if dead else ""),
    encoding="utf-8"
)


latencies = [
    latency
    for _, ok, latency, _ in results
    if ok and latency is not None
]

latencies.sort()

if latencies:
    avg_latency = sum(latencies) / len(latencies)
    min_latency = latencies[0]
    max_latency = latencies[-1]
else:
    avg_latency = 0
    min_latency = 0
    max_latency = 0


stats = [
    f"Input endpoints: {len(configs)}",
    f"TCP reachable: {len(alive)}",
    f"TCP unreachable: {len(dead)}",
    (
        f"Reachable percentage: "
        f"{(len(alive) / len(configs) * 100):.1f}%"
        if configs
        else
        "Reachable percentage: 0%"
    ),
    f"Average latency: {avg_latency:.0f} ms",
    f"Minimum latency: {min_latency:.0f} ms",
    f"Maximum latency: {max_latency:.0f} ms",
]

STATS.write_text(
    "\n".join(stats) + "\n",
    encoding="utf-8"
)

print()
print("\n".join(stats))
