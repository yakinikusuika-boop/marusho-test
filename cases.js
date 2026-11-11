/* ============================================================
   施工事例のデータ

   ■ このファイルは自動で作られています。直接編集しないでください。
     次回の自動反映のときに、ここでの手直しは消えてしまいます。

   ■ 内容を直すところ：施工事例台帳（スプレッドシート）

   ■ 作り直しているもの：tools/施工事例台帳_生成.py
     （.github/workflows/news-from-sheet.yml が定期的に実行します）
     /works/ のカードも、続けて tools/施工事例一覧作成.py が作り直します。
   ============================================================ */

const CASE_ITEMS = [
  // ---- 1件目（台帳 2行目） ----
  {
    category: "橋の拡張・補修工事",
    type:     "外構・その他",
    before: "lp_image_assets_png/cases/web/bridge_before.jpg",
    after:  "lp_image_assets_png/cases/web/bridge_after.jpg",
    spec:   { location: "農道の橋（水路横断部）", period: "約7日間", cost: "65万円〜（目安）", building: "屋外・土木工事" },
    detail: {
      problem: "橋の幅が狭く、路肩に寄ると水路側に落ちそうで通行が不安",
      work:    "橋の路盤を拡張し、水路側にコンクリート縁石を新設。取合いの土間も打ち直し",
      change:  "有効幅が広がり、軽トラックでも安心して渡れるようになりました。",
      comment: "水路をまたぐ部分のため、通行止めの期間を最小限にして施工しました。"
    },
    link: ""
  },
  // ---- 2件目（台帳 3行目） ----
  {
    category: "外壁塗装（クリーム色）",
    type:     "外壁塗装",
    before: "lp_image_assets_png/cases/web/exterior_cream_before.jpg",
    after:  "lp_image_assets_png/cases/web/exterior_cream_after.jpg",
    spec:   { location: "外壁・付帯部", period: "約14日間", cost: "155万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "外壁の白さがくすみ、破風や軒まわりの傷みも気になる",
      work:    "足場を組み、高圧洗浄・下地補修のうえ外壁をクリーム色に塗装。破風・軒天などの付帯部もあわせて塗り替え",
      change:  "既存の瓦屋根に合う落ち着いた色合いになり、家全体が明るくなりました。",
      comment: "付帯部を濃い色で締めることで、クリーム色の外壁が引き立つよう仕上げました。"
    },
    link: ""
  },
  // ---- 3件目（台帳 4行目） ----
  {
    category: "外壁塗装（ツートン）",
    type:     "外壁塗装",
    before: "lp_image_assets_png/cases/web/exterior_navy_before.jpg",
    after:  "lp_image_assets_png/cases/web/exterior_navy_after.jpg",
    spec:   { location: "外壁", period: "14日間", cost: "約155万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "外壁全体の色あせが進み、家の印象が古く見えてしまう",
      work:    "高圧洗浄・下地補修のうえ、濃紺と白のツートンで全面塗装",
      change:  "2色の塗り分けで外観の印象が大きく変わり、汚れも目立ちにくくなりました。",
      comment: "既存の瓦屋根に合う濃紺をお選びいただき、引き締まった外観に仕上げました。"
    },
    link: ""
  },
  // ---- 4件目（台帳 5行目） ----
  {
    category: "外壁塗装（付帯部含む）",
    type:     "外壁塗装",
    before: "lp_image_assets_png/cases/web/exterior_twotone_before.jpg",
    after:  "lp_image_assets_png/cases/web/exterior_twotone_after.jpg",
    spec:   { location: "外壁・付帯部", period: "15日間", cost: "約145万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "外壁のひび・クラックが気になり、雨樋や破風の傷みも心配",
      work:    "ストーンカラーで外壁を丁寧に塗装し、雨樋・破風などの付帯部もあわせて施工",
      change:  "全体が明るく引き締まり、細部まで新しくなりました。",
      comment: "施主様のお好みをヒヤリングし、色をご提案しました。"
    },
    link: ""
  },
  // ---- 5件目（台帳 6行目） ----
  {
    category: "玄関ドア交換",
    type:     "内装・建具",
    before: "lp_image_assets_png/cases/web/entrance_door_before.jpg",
    after:  "lp_image_assets_png/cases/web/entrance_door_after.jpg",
    spec:   { location: "玄関", period: "1日間", cost: "約55万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "カギがかかりにくく、防犯面が心配",
      work:    "3重ロックのカギ付きで、断熱性のある玄関ドアへ交換",
      change:  "開け閉めが軽くなり、玄関まわりの印象も明るくなりました。",
      comment: "玄関は家の顔とのご主人のご要望におこたえしました。"
    },
    link: ""
  },
  // ---- 6件目（台帳 7行目） ----
  {
    category: "内窓・間仕切り（インプラス）",
    type:     "内装・建具",
    before: "lp_image_assets_png/cases/web/innerwindow_before.jpg",
    after:  "lp_image_assets_png/cases/web/innerwindow_after.jpg",
    spec:   { location: "居室", period: "1日間", cost: "約25万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "建具の老朽化で、開け閉めのたびにガタガタ音がする",
      work:    "4カ所にインプラス（内窓）を取付",
      change:  "採光を保ちながら断熱性が上がり、冷暖房も効きやすくなりました。",
      comment: "断熱効果もあります。"
    },
    link: ""
  },
  // ---- 7件目（台帳 8行目） ----
  {
    category: "キッチン改修",
    type:     "水回り",
    before: "lp_image_assets_png/cases/web/kitchen_before.jpg",
    after:  "lp_image_assets_png/cases/web/kitchen_after.jpg",
    spec:   { location: "キッチン", period: "5日間", cost: "約120万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "古くなった水まわりを、使いやすくしたい",
      work:    "収納力を高めた最新システムキッチンへ交換",
      change:  "作業スペースと収納が増え、毎日の料理が快適になりました。",
      comment: "限られたスペースでも使いやすくなるようプランを工夫しました。"
    },
    link: ""
  },
  // ---- 8件目（台帳 9行目） ----
  {
    category: "ユニットバス交換",
    type:     "水回り",
    before: "lp_image_assets_png/cases/web/bath_unit_before.jpg",
    after:  "lp_image_assets_png/cases/web/bath_unit_after.jpg",
    spec:   { location: "浴室", period: "4日間", cost: "約125万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "冬場の浴室が寒く、掃除もしづらい",
      work:    "断熱性の高い最新ユニットバスへ交換し、床・壁も一新",
      change:  "ヒートショックの不安が減り、お掃除もぐんと楽になりました。",
      comment: "暖房乾燥機を追加し、一年中快適にご入浴いただけるようにしました。"
    },
    link: ""
  },
  // ---- 9件目（台帳 10行目） ----
  {
    category: "浴室改修（バランス釜→ポリバス）",
    type:     "水回り",
    before: "lp_image_assets_png/cases/web/bath_polybath_before.jpg",
    after:  "lp_image_assets_png/cases/web/bath_polybath_after.jpg",
    spec:   { location: "浴室", period: "3日間", cost: "約42万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "バランス釜で浴槽が狭く、浴室全体の傷みや汚れも気になる",
      work:    "バランス釜を撤去してポリバスへ入れ替え、浴室窓のガラスサッシもあわせて交換",
      change:  "ゆったり入れる浴槽になり、窓まわりも一新して明るく清潔な浴室になりました。",
      comment: "ユニットバスより費用を抑えられるポリバス施工で、工期も3日間で仕上げました。"
    },
    link: ""
  },
  // ---- 10件目（台帳 11行目） ----
  {
    category: "外壁塗装",
    type:     "外壁塗装",
    before: "lp_image_assets_png/cases/web/exterior_paint_before.jpg",
    after:  "lp_image_assets_png/cases/web/exterior_paint_after.jpg",
    spec:   { location: "外壁", period: "12日間", cost: "約185万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "外壁の色あせやヨゴレが気になる",
      work:    "高圧洗浄と下地補修のうえ、下塗り〜上塗りまで丁寧に塗装",
      change:  "見違えるほど美しくなり、防水性もしっかり回復しました。",
      comment: "傷みやすい部分を補修し、長持ちする塗膜に仕上げました。"
    },
    link: ""
  },
  // ---- 11件目（台帳 12行目） ----
  {
    category: "内装リフォーム（畳→フローリング）",
    type:     "内装・建具",
    before: "lp_image_assets_png/cases/web/floor_before.jpg",
    after:  "lp_image_assets_png/cases/web/floor_after.jpg",
    spec:   { location: "居室", period: "2日間", cost: "約22万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "畳が傷み、掃除や家具の配置がしづらい",
      work:    "畳を撤去し、お手入れしやすいフローリングへ張り替え",
      change:  "明るく使いやすい洋室になり、家具も置きやすくなりました。",
      comment: "下地を調整し、段差なくきれいに仕上げました。"
    },
    link: ""
  },
  // ---- 12件目（台帳 13行目） ----
  {
    category: "外構・庭工事",
    type:     "外構・その他",
    before: "lp_image_assets_png/cases/web/garden_before.jpg",
    after:  "lp_image_assets_png/cases/web/garden_after.jpg",
    spec:   { location: "庭・外構", period: "8日間", cost: "約120万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "庭の手入れが大変で、使いにくい",
      work:    "整地・土間などを行い、手入れしやすい外構へ整備",
      change:  "雑草対策で日々のお手入れが楽になり、見た目もすっきり。",
      comment: "使い方に合わせて、動線と水はけを考えて設計しました。"
    },
    link: ""
  }
];
