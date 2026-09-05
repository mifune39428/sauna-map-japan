#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サウナイキタイの施設に OSM のPOIを突き合わせて、公式サイトURLを借りる。

名前だけで突き合わせると別施設を拾うので、まず 200m 以内に絞り、
そのうえで名前の一致度で選ぶ。どちらも満たさないものは付けない。
"""
import json, math, re, unicodedata
from difflib import SequenceMatcher

MAX_M = 200          # これより遠いPOIは別施設とみなす
MIN_SIM = 0.55       # 名前の一致度の下限


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r'[\s\-–—ー・（）()【】\[\]「」『』,、。/&＆’\'"!！]', '', s)
    s = re.sub(r'(ホテル|温泉|旅館|の湯|スパ|サウナ)$', '', s)
    return s.lower()


def dist_m(a, b, c, d):
    dy = (a - c) * 111320.0
    dx = (b - d) * 111320.0 * math.cos(math.radians((a + c) / 2))
    return math.hypot(dx, dy)


def main():
    saunas = json.load(open("map_data.json"))
    osm = json.load(open("cache/osm/osm.json"))["elements"]

    pois = []
    for e in osm:
        t = e.get("tags", {})
        lat = e.get("lat", (e.get("center") or {}).get("lat"))
        lng = e.get("lon", (e.get("center") or {}).get("lon"))
        if lat is None or not t.get("name"):
            continue
        pois.append((lat, lng, t))

    # 0.02度（約2km）のグリッドに入れて近傍だけ見る
    grid = {}
    for p in pois:
        grid.setdefault((round(p[0] / 0.02), round(p[1] / 0.02)), []).append(p)

    out, hit, withweb = {}, 0, 0
    for sid, s in saunas.items():
        lat, lng = s.get("geolat"), s.get("geolong")
        if not lat:
            continue
        gy, gx = round(lat / 0.02), round(lng / 0.02)
        cands = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                cands += grid.get((gy + dy, gx + dx), [])
        best, bestscore = None, 0
        nm = norm(s["name"])
        for plat, plng, t in cands:
            d = dist_m(lat, lng, plat, plng)
            if d > MAX_M:
                continue
            sim = max(SequenceMatcher(None, nm, norm(n)).ratio()
                      for n in (t.get("name"), t.get("name:ja"), t.get("alt_name")) if n)
            if sim < MIN_SIM:
                continue
            score = sim - d / (MAX_M * 20)     # 名前優先、同点なら近いほう
            if score > bestscore:
                best, bestscore = (t, d, sim), score
        if not best:
            continue
        t, d, sim = best
        hit += 1
        web = t.get("website") or t.get("contact:website") or ""
        if web.startswith("http"):
            withweb += 1
        out[sid] = {"osm_name": t.get("name"), "dist_m": round(d),
                    "sim": round(sim, 2),
                    "website": web if web.startswith("http") else "",
                    "phone": t.get("phone") or t.get("contact:phone") or ""}
    json.dump(out, open("osm_match.json", "w"), ensure_ascii=False, indent=1)
    print("OSMと同定できた %d件 / %d件  うち公式サイトURLつき %d件"
          % (hit, len(saunas), withweb))


if __name__ == "__main__":
    main()
