#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サウナイキタイの都道府県一覧を全ページ取得して、施設IDと一覧に出ている属性を拾う"""
import html as ih
import json, os, re, subprocess, sys, time

PREFS = [
    ("aomori", "青森県"), ("iwate", "岩手県"), ("miyagi", "宮城県"),
    ("akita", "秋田県"), ("yamagata", "山形県"), ("fukushima", "福島県"),
]
CACHE = os.environ.get("SAUNA_CACHE", "cache/list")
WAIT = float(os.environ.get("SAUNA_WAIT", "1.0"))

ITEM = re.compile(
    r'<div class="p-saunaItem p-saunaItem--list.*?'
    r'<a href="https://sauna-ikitai\.com/saunas/(\d+)"></a>(.*?)</address>', re.S)


def txt(s):
    return re.sub(r'\s+', ' ', ih.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def get(url, path, force=False):
    if force or not (os.path.exists(path) and os.path.getsize(path) > 3000):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        subprocess.run(["curl", "-sS", "--retry", "2", "-o", path, url], check=True)
        time.sleep(WAIT)
    return open(path, encoding="utf-8", errors="replace").read()


def crawl(slug, force=False):
    base = "https://sauna-ikitai.com/search?prefecture%5B%5D=" + slug
    first = get(base, os.path.join(CACHE, slug, "1.html"), force)
    m = re.search(r'([0-9,]+)件', first)
    total = int(m.group(1).replace(",", "")) if m else 0
    pages = max((re.findall(r'page=(\d+)', first) or ["1"]), key=lambda x: int(x))
    out, seen = [], set()
    for p in range(1, int(pages) + 1):
        h = first if p == 1 else get(base + "&page=%d" % p,
                                     os.path.join(CACHE, slug, "%d.html" % p), force)
        for mm in ITEM.finditer(h):
            sid, block = mm.group(1), mm.group(2)
            if sid in seen:
                continue
            seen.add(sid)
            name = re.search(r'<h3>\s*(.*?)\s*</h3>', block, re.S)
            addr = re.search(r'<address[^>]*>(.*?)$', block, re.S)
            tags = re.search(r'p-saunaItemName_tags">(.*?)</div>', block, re.S)
            out.append({
                "id": int(sid),
                "name": ih.unescape(txt(name.group(1))) if name else "",
                "area": txt(addr.group(1)) if addr else "",
                "tags": [t for t in txt(tags.group(1)).split(" ") if t] if tags else [],
            })
    return total, out


if __name__ == "__main__":
    force = "--force" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    data = {}
    if os.path.exists("list.json"):
        data = json.load(open("list.json"))
    for slug, jp in PREFS:
        if only and slug not in only:
            continue
        total, items = crawl(slug, force)
        data[slug] = {"pref": jp, "total": total, "items": items}
        print("%-10s 掲載 %4d 件 / 取得 %4d 件" % (jp, total, len(items)))
    json.dump(data, open("list.json", "w"), ensure_ascii=False, indent=1)
    tags = {}
    for v in data.values():
        for it in v["items"]:
            for t in it["tags"]:
                tags[t] = tags.get(t, 0) + 1
    print("一覧に出るタグ:", json.dumps(tags, ensure_ascii=False))
