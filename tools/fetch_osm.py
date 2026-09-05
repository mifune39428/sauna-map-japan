#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenStreetMap(Overpass) から東北の入浴・宿泊系POIを取る。公式サイトURLの補完に使う。

サウナイキタイの一覧JSONには公式サイトのURLが入っていないため、
座標と名前で OSM のPOIに突き合わせて website タグを借りている。

Overpass は混んでいるとJSONではなくHTMLのエラーページを返す。
いったん別ファイルに落として中身を検めてから置き換える（前回のぶんを壊さないため）。
"""
import json, os, subprocess, sys, time

PREF_ISO = ["JP-02", "JP-03", "JP-04", "JP-05", "JP-06", "JP-07"]  # 青森〜福島
OUT = "cache/osm/osm.json"
MIN_ELEMENTS = 500          # これを下回るのは取得が欠けているとみなす
ENDPOINTS = ["https://overpass-api.de/api/interpreter",
             "https://overpass.kumi.systems/api/interpreter"]

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


def looks_ok(path):
    try:
        d = json.load(open(path))
    except Exception:
        return 0
    return len(d.get("elements") or [])


def main(force=False):
    have = looks_ok(OUT) if os.path.exists(OUT) else 0
    if have >= MIN_ELEMENTS and not force:
        print("キャッシュを使う: %s（%d件）" % (OUT, have))
        return 0

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    for i in range(4):
        url = ENDPOINTS[i % len(ENDPOINTS)]
        print("Overpass に問い合わせ中（%d回目 %s）…" % (i + 1, url), flush=True)
        subprocess.run(["curl", "-sS", "--max-time", "900", "-X", "POST",
                        "-d", QUERY, "-o", tmp, url], check=False)
        n = looks_ok(tmp)
        if n >= MIN_ELEMENTS:
            os.replace(tmp, OUT)
            print("POI %d件を取得した" % n)
            return 0
        print("  → JSONとして読めないか件数が少ない（%d件）。待って取り直す" % n, flush=True)
        time.sleep(30 * (i + 1))

    if os.path.exists(tmp):
        os.remove(tmp)
    if have >= MIN_ELEMENTS:
        # 公式サイトURLの補完に使うだけなので、前回のぶんで続けてよい
        print("!! Overpass から取れなかった。前回のキャッシュ（%d件）で続ける" % have)
        return 0
    print("!! Overpass から取れず、使えるキャッシュも無い", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main("--force" in sys.argv))
