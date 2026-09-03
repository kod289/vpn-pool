from pathlib import Path
from urllib.parse import urlsplit, parse_qsl
import hashlib
import re

INPUT = Path("output/raw.txt")
OUTPUT = Path("output/unique.txt")
STATS = Path("output/dedup_stats.txt")


SCHEMES = {
    "vless",
    "vmess",
    "trojan",
    "ss",
    "ssr",
    "hysteria",
    "hysteria2",
    "hy2",
    "tuic",
}


# Эти параметры обычно не делают отдельный сервер.
IGNORED_PARAMS = {
    "fp",
    "fingerprint",
}


def normalize(value):
    return value.strip().lower()


def make_fingerprint(config):
    try:
        parsed = urlsplit(config)

        scheme = normalize(parsed.scheme)
        host = normalize(parsed.hostname or "")
        port = parsed.port or ""

        username = parsed.username or ""
        password = parsed.password or ""

        params = parse_qsl(
            parsed.query,
            keep_blank_values=True
        )

        normalized_params = []

        for key, value in params:
            key = normalize(key)

            if key in IGNORED_PARAMS:
                continue

            normalized_params.append(
                (
                    key,
                    value.strip()
                )
            )

        normalized_params.sort()

        identity = [
            scheme,
            host,
            str(port),
            username,
            password,
        ]

        identity.extend(
            f"{key}={value}"
            for key, value in normalized_params
        )

        raw_identity = "|".join(identity)

        return hashlib.sha256(
            raw_identity.encode()
        ).hexdigest()

    except Exception:
        return hashlib.sha256(
            config.encode()
        ).hexdigest()


configs = []

for line in INPUT.read_text(
    encoding="utf-8",
    errors="ignore"
).splitlines():

    line = line.strip()

    if not line:
        continue

    if not re.match(
        r"^(vless|vmess|trojan|ss|ssr|hysteria|hysteria2|hy2|tuic)://",
        line,
        re.IGNORECASE
    ):
        continue

    configs.append(line)


groups = {}

for config in configs:
    key = make_fingerprint(config)

    if key not in groups:
        groups[key] = config


unique = sorted(groups.values())


OUTPUT.write_text(
    "\n".join(unique) + "\n",
    encoding="utf-8"
)


stats = [
    f"Input configs: {len(configs)}",
    f"Unique endpoints: {len(unique)}",
    f"Removed duplicates: {len(configs) - len(unique)}",
]

STATS.write_text(
    "\n".join(stats) + "\n",
    encoding="utf-8"
)

print("\n".join(stats))
        
