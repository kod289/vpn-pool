from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import base64
import re

INPUT = Path("output/clean.txt")
OUTPUT = Path("output/quality.txt")
STATS = Path("output/quality_stats.txt")

SUPPORTED = {
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

HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


def valid_port(port):
    return port is not None and 1 <= port <= 65535


def has_query(config):
    try:
        return bool(urlsplit(config).query)
    except Exception:
        return False


def check_config(config):
    try:
        p = urlsplit(config)
        scheme = p.scheme.lower()

        if scheme not in SUPPORTED:
            return False, "unsupported"

        if not p.hostname:
            return False, "no_host"

        if not valid_port(p.port):
            return False, "bad_port"

        if scheme in {"vless", "vmess", "trojan"}:
            if not p.username:
                return False, "no_user"

        # VLESS
        if scheme == "vless":
            q = parse_qs(p.query)

            security = q.get("security", [""])[0].lower()
            transport = q.get("type", [""])[0].lower()

            if security not in {
                "",
                "none",
                "tls",
                "reality"
            }:
                return False, "bad_security"

            if transport not in {
                "",
                "tcp",
                "ws",
                "grpc",
                "http",
                "h2",
                "xhttp"
            }:
                return False, "bad_transport"

            if security == "reality":
                if not q.get("pbk"):
                    return False, "reality_no_pbk"

                if not q.get("sni"):
                    return False, "reality_no_sni"

        # Trojan
        elif scheme == "trojan":
            q = parse_qs(p.query)

            security = q.get("security", ["tls"])[0].lower()
            transport = q.get("type", ["tcp"])[0].lower()

            if security not in {
                "",
                "tls",
                "none"
            }:
                return False, "bad_security"

            if transport not in {
                "",
                "tcp",
                "ws",
                "grpc"
            }:
                return False, "bad_transport"

        # Shadowsocks
        elif scheme == "ss":
            if not p.username:
                return False, "ss_no_user"

        # Hysteria2
        elif scheme in {"hysteria2", "hy2"}:
            if not p.username:
                return False, "hy2_no_user"

        return True, "ok"

    except Exception:
        return False, "parse_error"


configs = [
    x.strip()
    for x in INPUT.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()
    if x.strip()
]


good = []
bad = {}

seen = set()

for config in configs:

    # Полный дубликат
    if config in seen:
        continue

    seen.add(config)

    ok, reason = check_config(config)

    if ok:
        good.append(config)
    else:
        bad[reason] = bad.get(reason, 0) + 1


good = sorted(set(good))

OUTPUT.write_text(
    "\n".join(good) + ("\n" if good else ""),
    encoding="utf-8"
)


removed = len(configs) - len(good)

stats = [
    f"Input: {len(configs)}",
    f"Quality OK: {len(good)}",
    f"Removed: {removed}",
    "",
    "Reasons:"
]

for reason, count in sorted(bad.items()):
    stats.append(f"{reason}: {count}")


STATS.write_text(
    "\n".join(stats) + "\n",
    encoding="utf-8"
)

print("\n".join(stats))
              
