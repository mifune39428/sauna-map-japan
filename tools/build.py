#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""map_data.json + list.json + osm_match.json を1つにまとめて saunas.json を書く"""
import json, os, re, unicodedata

PREF_ORDER = ["青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県"]
ACCESS = {"one_day_visit": "day", "guests_only": "guests", "members_only": "members", "": "unknown"}


def clean(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r'[ \t]+', ' ', s)
    return re.sub(r'\n{2,}', '\n', s).strip()


def main():
    md = json.load(open("map_data.json"))
    lst = json.load(open("list.json"))
    osm = json.load(open("osm_match.json"))
    over = {}
    if os.path.exists("official_overrides.json"):
        over = json.load(open("official_overrides.json"))

    tags = {}
    for v in lst.values():
        for it in v["items"]:
            tags[str(it["id"])] = it["tags"]

    out, skipped = [], []
    for sid, s in md.items():
        if not s.get("geolat"):
            skipped.append(s["name"])
            continue
        t = tags.get(sid, [])
        official = (over.get(sid) or "").strip() or (osm.get(sid, {}).get("website") or "")
        r = {
            "id": int(sid),
            "name": clean(s["name"]),
            "pref": s["prefecture"],
            "city": s.get("address1") or "",
            "address": s["prefecture"] + (s.get("address1") or "") + (s.get("address2") or "")
                       + (s.get("address3") or ""),
            "lat": s["geolat"], "lng": s["geolong"],
            "type": s.get("facility_type_jp") or "その他",
            "sex": "both" if s.get("is_female_available") else "male",
            "access": ACCESS.get(s.get("guest_type") or "", "unknown"),
            "booking": bool(s.get("require_booking")),
            "ikitai": "https://sauna-ikitai.com/saunas/%s" % sid,
        }
        if official:
            r["official"] = official
            r["official_src"] = "手動" if over.get(sid) else "OSM"
        if s.get("booking_url"):
            r["booking_url"] = s["booking_url"]
        if s.get("min_fee"):
            r["fee_min"] = s["min_fee"]
        if clean(s.get("regular_holiday_text")):
            r["holiday"] = clean(s["regular_holiday_text"])
        if clean(s.get("business_hours")):
            r["hours"] = clean(s["business_hours"])
        for sex in ("male", "female"):
            o = s.get(sex) or {}
            if o.get("sauna_temperature") or o.get("water_baths_temperature"):
                r[sex + "_temp"] = [o.get("sauna_temperature"), o.get("water_baths_temperature"),
                                    bool(o.get("open_air"))]
        if "休業・短縮営業" in t:
            r["suspended"] = True
        if s.get("not_has_permanent_sauna"):
            r["no_permanent"] = True
        if s.get("open_at"):
            r["open_at"] = s["open_at"][:10]
        out.append(r)

    out.sort(key=lambda r: (PREF_ORDER.index(r["pref"]) if r["pref"] in PREF_ORDER else 9,
                            r["city"], r["name"]))
    meta = {
        "region": "東北",
        "prefs": PREF_ORDER,
        "types": sorted({r["type"] for r in out}),
        "updated": __import__("datetime").date.today().isoformat(),
        "count": len(out),
    }
    json.dump({"meta": meta, "saunas": out},
              open("../saunas.json", "w"), ensure_ascii=False, separators=(",", ":"))

    from collections import Counter
    print("収録 %d 件（座標なしで除外 %d 件: %s）"
          % (len(out), len(skipped), "／".join(skipped[:6])))
    print("県別      ", dict(Counter(r["pref"] for r in out)))
    print("だれが    ", dict(Counter(r["sex"] for r in out)))
    print("利用      ", dict(Counter(r["access"] for r in out)))
    print("公式サイト ", sum(1 for r in out if r.get("official")), "件")
    print("料金あり  ", sum(1 for r in out if r.get("fee_min")), "件")
    print("定休日あり", sum(1 for r in out if r.get("holiday")), "件")
    print("営業時間あり", sum(1 for r in out if r.get("hours")), "件")
    print("休業・短縮", sum(1 for r in out if r.get("suspended")), "件")
    print("ファイル  ", os.path.getsize("../saunas.json") // 1024, "KB")


if __name__ == "__main__":
    main()
