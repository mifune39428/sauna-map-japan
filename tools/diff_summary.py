#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前回コミットの saunas.json と今回のぶんを比べて、変化を1行にまとめる。

サウナイキタイの温度は利用者の報告で日々変わるので、毎回どこかしら差分が出る。
「何件になったか」だけでなく「何が増えて何が変わったか」を残したいので分けて数える。
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KEY_FIELDS = ("name", "sex", "access", "fee_min", "holiday", "hours",
              "official", "booking", "address", "suspended")


def load_head():
    try:
        out = subprocess.run(["git", "-C", ROOT, "show", "HEAD:saunas.json"],
                             capture_output=True, check=True).stdout
        return {x["id"]: x for x in json.loads(out)["saunas"]}
    except Exception:
        return None


def main():
    new = {x["id"]: x for x in json.load(open(os.path.join(ROOT, "saunas.json")))["saunas"]}
    old = load_head()
    if old is None:
        print("%d 件" % len(new))
        return 0
    added = set(new) - set(old)
    gone = set(old) - set(new)
    same = set(new) & set(old)
    important = [i for i in same
                 if any(old[i].get(k) != new[i].get(k) for k in KEY_FIELDS)]
    other = [i for i in same if old[i] != new[i] and i not in important]

    bits = ["%d 件" % len(new)]
    if added:
        bits.append("新規 %d" % len(added))
    if gone:
        bits.append("掲載終了 %d" % len(gone))
    if important:
        bits.append("料金や営業の変更 %d" % len(important))
    if other:
        bits.append("温度などの変更 %d" % len(other))
    print("・".join(bits))

    if "-v" in sys.argv:
        for i in list(added)[:10]:
            print("  + %s（%s%s）" % (new[i]["name"], new[i]["pref"], new[i]["city"]))
        for i in list(gone)[:10]:
            print("  - %s（%s%s）" % (old[i]["name"], old[i]["pref"], old[i]["city"]))
        for i in important[:10]:
            ch = [k for k in KEY_FIELDS if old[i].get(k) != new[i].get(k)]
            print("  * %s: %s" % (new[i]["name"], "／".join(ch)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
