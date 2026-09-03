import base64
import re
import urllib.request
from pathlib import Path

OUT = Path("output")
OUT.mkdir(exist_ok=True)

SOURCES = {
    "v2rayroot_vless":
        "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/main/Config/vless.txt",

    "v2rayroot_vmess":
        "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/main/Config/vmess.txt",

    "v2rayroot_ss":
        "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/main/Config/shadowsocks.txt",

    "igareck_vless":
        "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",

    "igareck_ss":
        "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",

    "artembsk_vless":
        "https://raw.githubusercontent.com/artembsk/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",
}


def download(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "vpn-pool-collector/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def decode_possible_base64(data):
    text = data.decode("utf-8", errors="ignore")

    # Если это обычный текст с URI — оставляем как есть.
    if re.search(r"(vless|vmess|trojan|ss|ssr|hysteria|hy2|tuic)://", text, re.I):
        return text

    # Иногда subscription приходит как base64.
    compact = re.sub(r"\s+", "", text)

    try:
        padded = compact + "=" * (-len(compact) % 4)
        decoded = base64.b64decode(padded).decode(
            "utf-8",
            errors="ignore"
        )

        if re.search(
            r"(vless|vmess|trojan|ss|ssr|hysteria|hy2|tuic)://",
            decoded,
            re.I
        ):
            return decoded
    except Exception:
        pass

    return text


def extract_configs(text):
    pattern = re.compile(
        r"(?:vless|vmess|trojan|ss|ssr|hysteria2?|hy2|tuic)://[^\s]+",
        re.I
    )

    return pattern.findall(text)


all_configs = []
stats = []

for name, url in SOURCES.items():
    try:
        raw = download(url)
        text = decode_possible_base64(raw)
        configs = extract_configs(text)

        all_configs.extend(configs)

        stats.append(
            f"{name}: {len(configs)} configs"
        )

        print(f"[OK] {name}: {len(configs)}")

    except Exception as e:
        stats.append(
            f"{name}: ERROR: {e}"
        )

        print(f"[ERROR] {name}: {e}")


# Первичная дедупликация.
unique_configs = sorted(set(all_configs))

(OUT / "raw.txt").write_text(
    "\n".join(all_configs) + "\n",
    encoding="utf-8"
)

(OUT / "unique.txt").write_text(
    "\n".join(unique_configs) + "\n",
    encoding="utf-8"
)

(OUT / "stats.txt").write_text(
    "\n".join(stats) + "\n",
    encoding="utf-8"
)

print()
print(f"Total:  {len(all_configs)}")
print(f"Unique: {len(unique_configs)}")
