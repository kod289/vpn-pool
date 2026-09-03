from urllib.parse import urlsplit, parse_qs, unquote
from pathlib import Path
import hashlib
import re

INPUT = Path("output/raw.txt")
OUTPUT = Path("output/unique.txt")
STATS = Path("output/dedup_stats.txt")


def normalize_host(host):
    host = host.strip().lower()

    # IPv6 в URL может быть записан в квадратных скобках.
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]

    return host


def fingerprint(config):
    """
    Создаём идентификатор endpoint'а.

    Нам важно не считать разными серверами варианты,
    отличающиеся только второстепенными параметрами.
    """

    try:
        parsed = urlsplit(config)

        scheme = parsed.scheme.lower()
        host = normalize_host(parsed.hostname or "")
        port = parsed.port or ""

        query = parse_qs(parsed.query)

        # Параметры, которые часто меняют внешний вид URI,
        # но не обязательно означают другой endpoint.
        ignored = {
            "fp",
            "fingerprint",
            "remark",
            "name",
            "ps",
            "comment",
        }

        normalized_query = []

        for key in sorted(query):
            if key.lower() in ignored:
                continue

            values = sorted(
                unquote(v).strip()
                for v in query[key]
            )

            for value in values:
                normalized_query.append(
                    f"{key.lower()}={value}"
                )

        # Userinfo сохраняем, потому что UUID/password
        # обычно является частью идентичности конфигурации.
        username = parsed.username or ""
        password = parsed.password or ""

        identity = "|".join([
            scheme,
            username,
            password,
            host,
            str(port),
            "&".join(normalized_query),
        ])

        return hashlib.sha256(
            identity.encode("utf-8")
        ).hexdigest()

    except Exception:
        # Если URI не удалось разобрать,
        # оставляем его уникальным по полной строке.
        return hashlib.sha256(
            config.encode("utf-8")
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
        r"^(vless|vmess|trojan|ss|ssr|hysteria2?|hy2|tuic)://",
        line,
        re.I
    ):
        continue

    configs.append(line)


groups = {}

for config in configs:
    key = fingerprint(config)

    if key not in groups:
        groups[key] = config


unique = list(groups.values())

unique.sort()

OUTPUT.write_text(
    "\n".join(unique) + "\n",
    encoding="utf-8"
)

stats = [
    f"Input configs: {len(configs)}",
    f"Unique endpoints: {len(unique)}",
    f"Removed as duplicates: {len(configs) - len(unique)}",
]

STATS.write_text(
    "\n".join(stats) + "\n",
    encoding="utf-8"
)

print("\n".join(stats))
      
