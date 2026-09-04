from pathlib import Path
from urllib.parse import urlsplit, parse_qs

INPUT = Path("output/unique.txt")
OUTPUT = Path("output/clean.txt")
STATS = Path("output/filter_stats.txt")

ALLOWED = {
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

configs = [
    x.strip()
    for x in INPUT.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()
    if x.strip()
]

clean = []
removed = []

for config in configs:

    try:
        parsed = urlsplit(config)
        scheme = parsed.scheme.lower()

        # Неизвестный протокол
        if scheme not in ALLOWED:
            removed.append((config, "unsupported_scheme"))
            continue

        # Нет host
        if not parsed.hostname:
            removed.append((config, "no_host"))
            continue

        # Нет порта
        if parsed.port is None:
            removed.append((config, "no_port"))
            continue

        # Невалидный/нулевой порт
        if not (1 <= parsed.port <= 65535):
            removed.append((config, "bad_port"))
            continue

        # VLESS / VMess / Trojan требуют идентификатор
        if scheme in {"vless", "vmess", "trojan"}:
            if not parsed.username:
                removed.append((config, "no_user"))
                continue

        clean.append(config)

    except Exception as e:
        removed.append((config, "parse_error"))


clean = sorted(set(clean))

OUTPUT.write_text(
    "\n".join(clean) + ("\n" if clean else ""),
    encoding="utf-8"
)

stats = [
    f"Input: {len(configs)}",
    f"Clean: {len(clean)}",
    f"Removed: {len(configs) - len(clean)}",
]

STATS.write_text(
    "\n".join(stats) + "\n",
    encoding="utf-8"
)

print("\n".join(stats))
