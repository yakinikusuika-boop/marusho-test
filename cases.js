/* ============================================================
   施工事例のデータ（ここだけ編集すればOK）

   トップページの「施工事例」は、このファイルを書き換えるだけで
   自動で更新されます。HTMLを触る必要はありません。

   ■ 新しい事例の追加方法
     下の [ ] の中に、{ ... } のかたまりを1件追加してください。
     表示は「上に書いたものから順」に並びます。

   ■ 写真について
     before … ビフォー写真のファイルパス
     after  … アフター写真のファイルパス
     ・写真は「lp_image_assets_png/cases/web/」に、Web用として
       軽量化（横4：縦3・800×600）したものを入れています。
     ・元の高解像度写真は「lp_image_assets_png/cases/」に残しています。

   ■ 各項目の意味
     category … 事例の種別（見出しの緑バッジに表示）
     spec     … 施工箇所 / 工期 / 費用目安 / 建物種別
     detail   … 工事前の悩み / 施工内容 / 施工後の変化 / 担当者コメント
     link     … 「この事例を詳しく見る」のリンク先（空 "" ならお問い合わせへ）

   ■ 注意
     ・各行の終わりのカンマ「,」を消さないでください。
     ・文字は必ず " " （ダブルクォート）で囲んでください。
     ・工期・費用目安は参考値です。実際の内容に合わせて書き換えてください。
   ============================================================ */

const CASE_ITEMS = [
  {
    category: "外壁塗装（ツートン）",
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
  {
    category: "外壁塗装（付帯部含む）",
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
  {
    category: "玄関ドア交換",
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
  {
    category: "内窓・間仕切り（インプラス）",
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
  {
    category: "キッチン改修",
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
  {
    category: "ユニットバス交換",
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
  {
    category: "外壁塗装",
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
  {
    category: "内装リフォーム（畳→フローリング）",
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
  {
    category: "浴室改修（在来→ユニットバス）",
    before: "lp_image_assets_png/cases/web/bath_before.jpg",
    after:  "lp_image_assets_png/cases/web/bath_after.jpg",
    spec:   { location: "浴室", period: "7日間", cost: "約148万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "タイル張りの在来浴室が寒く、ひび割れも心配",
      work:    "在来浴室を解体し、暖かく掃除しやすいユニットバスを新設",
      change:  "保温性が上がり、日々のお掃除もぐっと楽になりました。",
      comment: "見えない下地の防水までしっかり施工しました。"
    },
    link: ""
  },
  {
    category: "外構・庭工事",
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
