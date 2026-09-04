from pathlib import Path
from urllib.parse import urlsplit
import base64
import re

INPUT = Path("output/clean.txt")
OUT = Path("output/subscriptions")

OUT.mkdir(parents=True, exist_ok=True)


PROTOCOLS = {
    "vless": "vless",
    "vmess": "vmess",
    "trojan": "trojan",
    "ss": "shadowsocks",
    "ssr": "ssr",
    "hysteria": "hysteria",
    "hysteria2": "hysteria2",
    "hy2": "hysteria2",
    "tuic": "tuic",
}


def get_scheme(config):
    try:
        return urlsplit(config).scheme.lower()
    except Exception:
        return ""


configs = []

for line in INPUT.read_text(
    encoding="utf-8",
    errors="ignore"
).splitlines():

    line = line.strip()

    if not line:
        continue

    if "://" not in line:
        continue

    configs.append(line)


groups = {
    "all": [],
    "vless": [],
    "vmess": [],
    "trojan": [],
    "shadowsocks": [],
    "ssr": [],
    "hysteria": [],
    "hysteria2": [],
    "tuic": [],
}


for config in configs:

    scheme = get_scheme(config)

    if scheme in PROTOCOLS:
        groups["all"].append(config)
        groups[PROTOCOLS[scheme]].append(config)


def write_subscription(name, items):

    items = sorted(set(items))

    path = OUT / f"{name}.txt"

    path.write_text(
        "\n".join(items) + ("\n" if items else ""),
        encoding="utf-8"
    )

    print(f"{name}: {len(items)}")


for name, items in groups.items():
    write_subscription(name, items)
  
