# 東北サウナマップ

東北6県のサウナ施設 **1,082 か所** を地図にまとめたものです。
全国版の第一弾として、まず東北から作りました。スマホのブラウザでそのまま開けます。

ピンをタップすると、**女性も入れるか・日帰りで入れるか・宿泊者限定か・料金・定休日・営業時間**と、
男湯／女湯それぞれのサウナ温度と水風呂温度が出ます。

## 使い方

- **ピンの色** … 日帰りOK（青緑）／宿泊者限定（紫）／会員のみ（グレー）／要確認（薄グレー）
- **青い縁のピン** … 男性専用
- **うすいピン** … 休業・短縮営業中
- **絞り込み** … だれが入れるか／利用のしかた／都道府県／施設タイプ、施設名・市町村での検索
- **📍** … 現在地を表示。近い順のリストから施設に飛べます

iPhone は Safari の共有ボタンから**「ホーム画面に追加」**にすると全画面で使えます。

## 収録内容

| 項目 | 件数 |
|---|---|
| 収録施設 | 1,082 |
| 男女とも利用できる | 1,031 |
| 男性専用 | 51 |
| 日帰りで入れる | 765 |
| 宿泊者限定 | 188 |
| 会員のみ | 96 |
| 利用条件が要確認 | 33 |
| 料金の記載あり | 780 |
| 定休日の記載あり | 1,014 |
| 営業時間の記載あり | 704 |
| 公式サイトのURLあり | 117 |

県別は 青森202／岩手153／宮城200／秋田163／山形127／福島237。

## 出典

- **施設の一覧・座標・住所・男女別の可否・日帰り可否・料金・定休日・営業時間**
  … [サウナイキタイ](https://sauna-ikitai.com/) の都道府県別一覧ページ。
  一覧ページには地図表示用の JSON（`window.__MAP_DATA`）が埋まっていて、必要な項目がすべて入っている。
- **公式サイトのURL** … [OpenStreetMap](https://www.openstreetmap.org/copyright)。
  サウナイキタイの一覧JSONには公式サイトのURLが無いため、
  200m以内かつ名前が一致するPOIの `website` タグを借りている。**そのため117件にしか付いていない。**
  付いていない施設は「公式サイトを検索」ボタン（施設名＋市町村での検索）になる。

**料金・定休日・営業時間は変わります。お出かけ前に必ず公式情報でご確認ください。**

### 詳細ページは使っていない

サウナイキタイの施設詳細ページ（`/saunas/<id>`）は AWS WAF の CAPTCHA が出るようになっており、
自動取得できない（`robots.txt` では許可されているが、実際には 405 とCAPTCHAが返る）。
**CAPTCHAは回避しない。** 幸い必要な項目は一覧ページの JSON に揃っているので、そちらだけを使っている。
一覧ページと OSM の Overpass API は通常どおり取得できる。

## 更新

月1回、`tools/update.sh` を実行すると一覧を取り直して `saunas.json` を作り直します。

```bash
tools/update.sh          # 一覧58ページとOSMを取り直す（3分ほど）
tools/update.sh --quick  # 取得せずキャッシュから作り直すだけ
```

一覧ページは間隔を空けて取ります（`SAUNA_WAIT`、既定1.5秒）。詰めて叩くとCAPTCHAが出ます。

### 公式サイトのURLを足す

`tools/official_overrides.json` に `{"施設ID": "https://..."}` の形で書くと、OSM より優先して使われます。
毎月の更新のたびに少しずつ足していけば、カバー率を上げられます。

## 構成

```
index.html      地図本体（HTML/CSS/JS 一体）
saunas.json     施設データ（build.py が生成）
vendor/         Leaflet 1.9.4 + Leaflet.markercluster 1.5.3（CDN 不要）
tools/
  fetch_list.py           都道府県一覧を全ページ取得 → list.json
  parse_map_data.py       一覧HTMLの __MAP_DATA を取り出す → map_data.json
  fetch_osm.py            Overpass で東北のPOIを取る → cache/osm/osm.json
  match_osm.py            距離200m＋名前で突き合わせ → osm_match.json
  build.py                ぜんぶ合わせて ../saunas.json
  official_overrides.json 公式サイトURLの手動指定
  update.sh               月1回の更新用
```

## 全国へ広げるとき

`tools/fetch_list.py` の `PREFS` と `tools/fetch_osm.py` の `PREF_ISO` に県を足し、
`tools/build.py` の `PREF_ORDER` を並べ替えるだけで他地方も同じ手順で作れます。
ただし全国だと施設が1万件を超えるので、`saunas.json` は地方別に分ける必要があります。

地図タイルは [OpenStreetMap](https://www.openstreetmap.org/copyright) を利用しています。
