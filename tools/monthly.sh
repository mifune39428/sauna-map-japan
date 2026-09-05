#!/bin/bash
# 月1回の自動更新。launchd（com.miffy.saunamap）から毎月1日に呼ばれる。手で叩いてもよい。
#
#   tools/monthly.sh          通常
#   tools/monthly.sh --dry    作り直すだけで push しない
#
# サウナイキタイの都道府県一覧を取り直して saunas.json を作り直し、
# 中身が変わっていたら GitHub Pages へ push する。
set -uo pipefail
cd "$(dirname "$0")/.."

export PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin
LOG_TAG="[$(date '+%Y-%m-%d %H:%M')]"
log() { echo "$LOG_TAG $*"; }
notify() { osascript -e "display notification \"$1\" with title \"東北サウナマップ\"" 2>/dev/null || true; }

log "更新をはじめる"
if ! tools/update.sh 2>&1 | sed "s/^/$LOG_TAG /"; then
  log "取得か組み立てに失敗した（上の行に理由が出ている）"
  notify "更新に失敗しました。ログを確認してください"
  exit 1
fi

# 施設が極端に減っていたら取得が途中で失敗している。上書きせず止める。
COUNT=$(python3 -c "import json;print(json.load(open('saunas.json'))['meta']['count'])" 2>/dev/null || echo 0)
if [ "$COUNT" -lt 800 ]; then
  log "施設が $COUNT 件しかない。取得に失敗しているとみて中止する"
  git checkout -- saunas.json 2>/dev/null || true
  notify "施設が $COUNT 件しか取れませんでした。中止しました"
  exit 1
fi

if git diff --quiet -- saunas.json; then
  log "中身に変化なし（$COUNT 件）。push はしない"
  exit 0
fi

# サウナイキタイの温度は利用者の報告で日々変わるので、毎回どこかしら差分は出る。
# 何が変わったのかを残しておく。
SUMMARY=$(python3 tools/diff_summary.py 2>/dev/null || echo "$COUNT 件")
python3 tools/diff_summary.py -v 2>/dev/null | tail -n +2 | sed "s/^/$LOG_TAG /"
log "更新: $SUMMARY"

if [ "${1:-}" = "--dry" ]; then
  log "--dry なので push しない"
  exit 0
fi

git add saunas.json tools/list.json tools/map_data.json tools/osm_match.json
git commit -q -m "施設データを更新（$(date '+%Y-%m-%d')）

$SUMMARY"
if ! git push -q origin main; then
  log "push に失敗した"
  notify "push に失敗しました。ログを確認してください"
  exit 1
fi
log "push した https://mifune39428.github.io/sauna-map-japan/"
