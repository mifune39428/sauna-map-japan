#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenStreetMap(Overpass) から東北の入浴・宿泊系POIを取る。公式サイトURLの補完に使う。

サウナイキタイの一覧JSONには公式サイトのURLが入っていないため、
座標と名前で OSM のPOIに突き合わせて website タグを借りている。
"""
import json, os, subprocess, sys

PREF_ISO = ["JP-02", "JP-03", "JP-04", "JP-05", "JP-06", "JP-07"]  # 青森〜福島
OUT = "cache/osm/osm.json"

QUERY = """[out:json][timeout:600];
(%s)->.a;
(
  nwr(area.a)["leisure"="sauna"];
  nwr(area.a)["amenity"~"^(public_bath|love_hotel|spa)$"];
  nwr(area.a)["tourism"~"^(hotel|guest_house|hostel|motel|apartment|chalet|camp_site)$"]["name"];
  nwr(area.a)["leisure"~"^(fitness_centre|resort|water_park|golf_course)$"]["name"];
);
out center tags;
""" % " ".join('area["ISO3166-2"="%s"];' % p for p in PREF_ISO)


def main(force=False):
    if os.path.exists(OUT) and os.path.getsize(OUT) > 10000 and not force:
        print("キャッシュを使う:", OUT)
    else:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        print("Overpass に問い合わせ中（数分かかる）…", flush=True)
        subprocess.run(["curl", "-sS", "--max-time", "900", "-X", "POST",
                        "-d", QUERY, "-o", OUT,
                        "https://overpass-api.de/api/interpreter"], check=True)
    d = json.load(open(OUT))
    named = [e for e in d["elements"] if e.get("tags", {}).get("name")]
    web = [e for e in named if e["tags"].get("website") or e["tags"].get("contact:website")]
    print("POI %d件（名前あり %d件 / website %d件）" % (len(d["elements"]), len(named), len(web)))


if __name__ == "__main__":
    main("--force" in sys.argv)
