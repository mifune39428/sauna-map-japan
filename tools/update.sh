#!/bin/sh
# 月1回の更新。サウナイキタイの都道府県一覧を取り直して saunas.json を作り直す。
#   ./update.sh          … 一覧とOSMを取り直す
#   ./update.sh --quick  … 手元のキャッシュから作り直すだけ（取得しない）
set -e
cd "$(dirname "$0")"

if [ "$1" != "--quick" ]; then
  # 一覧は58ページ。間隔を空けて取る（詰めて叩くとCAPTCHAが出る）
  SAUNA_WAIT="${SAUNA_WAIT:-1.5}" python3 fetch_list.py --force
  python3 fetch_osm.py --force
fi

python3 parse_map_data.py
python3 match_osm.py
python3 build.py
echo "更新おわり: $(cd .. && pwd)/saunas.json"
