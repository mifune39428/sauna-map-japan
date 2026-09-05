#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取得済みの一覧ページHTMLから window.__MAP_DATA を取り出す。

一覧ページには地図表示用のJSONが埋まっていて、座標・住所・男女別の可否・
日帰り可否・料金・定休日・営業時間まで入っている。詳細ページを見に行く必要はない。
"""
import glob, json, os, re, sys

MAP_DATA = re.compile(r'window\.__MAP_DATA\s*=\s*(\[.*?\]);\s*\n', re.S)
DROP = {"attached_photos", "hotels", "ikitai_counts", "post_counts",
        "male_ikitai_anonymized_counts", "female_ikitai_anonymized_counts",
        "male_post_anonymized_counts", "female_post_anonymized_counts",
        "ikitai_post_counts", "is_sponsor", "additional_contents",
        "business_hour_schedules", "shared"}


def parse(cache="cache/list"):
    out, bad = {}, []
    files = sorted(glob.glob(os.path.join(cache, "*", "*.html")))
    for f in files:
        m = MAP_DATA.search(open(f, encoding="utf-8", errors="replace").read())
        if not m:
            bad.append(f)
            continue
        for x in json.loads(m.group(1)):
            out[x["id"]] = {k: v for k, v in x.items() if k not in DROP}
    return out, len(files), bad


def main():
    data, n, bad = parse()
    if bad:
        print("!! __MAP_DATA が読めない一覧ページ %d 枚: %s"
              % (len(bad), "／".join(bad[:5])), file=sys.stderr)
        return 1
    json.dump(data, open("map_data.json", "w"), ensure_ascii=False, indent=1)
    print("一覧ページ %d 枚 → %d 施設" % (n, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
