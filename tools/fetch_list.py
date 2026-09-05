#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サウナイキタイの都道府県一覧を全ページ取得する。

一覧ページには地図表示用の JSON（window.__MAP_DATA）が埋まっていて、
座標・住所・男女別の可否・日帰り可否・料金・定休日・営業時間まで入っている。
施設詳細ページ（/saunas/<id>）は CAPTCHA が出るので使わない。

詰めて叩くと CAPTCHA を返してくるので、間隔を空けて取り、
中身を検めてからキャッシュに置き換える（前回のぶんを壊さないため）。
"""
import html as ih
import json, os, re, subprocess, sys, time

PREFS = [
    ("aomori", "青森県"), ("iwate", "岩手県"), ("miyagi", "宮城県"),
    ("akita", "秋田県"), ("yamagata", "山形県"), ("fukushima", "福島県"),
]
CACHE = os.environ.get("SAUNA_CACHE", "cache/list")
WAIT = float(os.environ.get("SAUNA_WAIT", "1.5"))
MARK = "window.__MAP_DATA"     # これが無いページは CAPTCHA か取得失敗
MAX_STALE = 3                  # 取り直せなかったページがこれを超えたら失敗にする

ITEM = re.compile(
    r'<div class="p-saunaItem p-saunaItem--list.*?'
    r'<a href="https://sauna-ikitai\.com/saunas/(\d+)"></a>(.*?)</address>', re.S)

stale = []


def txt(s):
    return re.sub(r'\s+', ' ', ih.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def read(p):
    return open(p, encoding="utf-8", errors="replace").read()


def get(url, path, force=False):
    """取れたら新しい中身、取れなければ前回のぶん。どちらも無ければ例外。"""
    if not force and os.path.exists(path) and MARK in read(path):
        return read(path)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    for i in range(3):
        subprocess.run(["curl", "-sS", "--retry", "2", "--max-time", "60",
                        "-o", tmp, url], check=False)
        if os.path.exists(tmp) and MARK in read(tmp):
            os.replace(tmp, path)
            time.sleep(WAIT)
            return read(path)
        # CAPTCHA を返されている。間隔を広げて取り直す
        print("   取り直す（%d回目）: %s" % (i + 1, url), flush=True)
        time.sleep(WAIT * (i + 1) * 5)

    if os.path.exists(tmp):
        os.remove(tmp)
    if os.path.exists(path) and MARK in read(path):
        stale.append(url)
        print("   !! 取れないので前回のぶんを使う: %s" % url, flush=True)
        return read(path)
    raise RuntimeError("一覧ページを取得できない: " + url)


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
            tg = re.search(r'p-saunaItemName_tags">(.*?)</div>', block, re.S)
            out.append({
                "id": int(sid),
                "name": ih.unescape(txt(name.group(1))) if name else "",
                "area": txt(addr.group(1)) if addr else "",
                "tags": [t for t in txt(tg.group(1)).split(" ") if t] if tg else [],
            })
    return total, out


def main():
    force = "--force" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    data = json.load(open("list.json")) if os.path.exists("list.json") else {}
    for slug, jp in PREFS:
        if only and slug not in only:
            continue
        total, items = crawl(slug, force)
        data[slug] = {"pref": jp, "total": total, "items": items}
        mark = "" if len(items) == total else "  ← 掲載件数と合わない"
        print("%-10s 掲載 %4d 件 / 取得 %4d 件%s" % (jp, total, len(items), mark))
    json.dump(data, open("list.json", "w"), ensure_ascii=False, indent=1)
    n = sum(len(v["items"]) for v in data.values())
    print("合計 %d 施設" % n)
    if stale:
        print("!! 取り直せず前回のぶんを使ったページ: %d 枚" % len(stale))
        if len(stale) > MAX_STALE:
            print("!! 多すぎる。CAPTCHA で弾かれている可能性が高い", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
