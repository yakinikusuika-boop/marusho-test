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
    category: "外壁・屋根塗装",
    before: "lp_image_assets_png/cases/web/exterior_wallroof_before.jpg",
    after:  "lp_image_assets_png/cases/web/exterior_wallroof_after.jpg",
    spec:   { location: "外壁・屋根", period: "18日間", cost: "約120万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "外壁の色あせと屋根の傷みを、まとめてきれいにしたい",
      work:    "足場を一度で設置し、外壁塗装と屋根塗装を同時に施工",
      change:  "白い外壁と引き締まった屋根色で、新築のような外観に。",
      comment: "足場を有効活用し、別々に行うより費用を抑えられました。"
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
    spec:   { location: "浴室", period: "4日間", cost: "約95万円〜（目安）", building: "戸建て" },
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
    spec:   { location: "外壁", period: "12日間", cost: "約90万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "外壁の色あせやチョーキング（白い粉）が気になる",
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
    spec:   { location: "居室", period: "3日間", cost: "約22万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "畳が傷み、掃除や家具の配置がしづらい",
      work:    "畳を撤去し、お手入れしやすいフローリングへ張り替え",
      change:  "明るく使いやすい洋室になり、家具も置きやすくなりました。",
      comment: "下地を調整し、段差なくきれいに仕上げました。"
    },
    link: ""
  },
  {
    category: "屋根塗装",
    before: "lp_image_assets_png/cases/web/roof_before.jpg",
    after:  "lp_image_assets_png/cases/web/roof_after.jpg",
    spec:   { location: "屋根", period: "7日間", cost: "約45万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "屋根の色あせやサビ、防水性の低下が心配",
      work:    "高圧洗浄・下塗りのうえ、耐久性の高い塗料で塗装",
      change:  "屋根がよみがえり、雨風から住まいを守る機能も回復しました。",
      comment: "傷みやすい屋根を長持ちさせる仕様でご提案しました。"
    },
    link: ""
  },
  {
    category: "浴室改修（在来→ユニットバス）",
    before: "lp_image_assets_png/cases/web/bath_before.jpg",
    after:  "lp_image_assets_png/cases/web/bath_after.jpg",
    spec:   { location: "浴室", period: "6日間", cost: "約110万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "タイル張りの在来浴室が寒く、ひび割れも心配",
      work:    "在来浴室を解体し、暖かく掃除しやすいユニットバスを新設",
      change:  "保温性が上がり、日々のお掃除もぐっと楽になりました。",
      comment: "見えない下地の防水までしっかり施工しました。"
    },
    link: ""
  },
  {
    category: "店舗改修",
    before: "lp_image_assets_png/cases/web/store_before.jpg",
    after:  "lp_image_assets_png/cases/web/store_after.jpg",
    spec:   { location: "店舗", period: "10日間", cost: "約80万円〜（目安）", building: "店舗・事務所" },
    detail: {
      problem: "店舗の外観が古く、印象を新しくしたい",
      work:    "傷んだ箇所を補修し、外観を一新するリフォームを実施",
      change:  "清潔感のある新しい印象になり、集客面でも好評です。",
      comment: "営業への影響を抑えながら、工程を組んで施工しました。"
    },
    link: ""
  },
  {
    category: "外壁塗装（和風住宅）",
    before: "lp_image_assets_png/cases/web/paint_before.jpg",
    after:  "lp_image_assets_png/cases/web/paint_after.jpg",
    spec:   { location: "外壁", period: "13日間", cost: "約100万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "和風住宅の外壁の傷みを、雰囲気を残して直したい",
      work:    "既存の風合いに合う色で、外壁を丁寧に塗装",
      change:  "落ち着いた仕上がりで、建物の趣を保ちながら美しくなりました。",
      comment: "瓦屋根との調和を考え、色をご提案しました。"
    },
    link: ""
  },
  {
    category: "洗面化粧台リフォーム",
    before: "lp_image_assets_png/cases/web/washstand_before.jpg",
    after:  "lp_image_assets_png/cases/web/washstand_after.jpg",
    spec:   { location: "洗面所", period: "2日間", cost: "約28万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "洗面台が古く、収納も足りない",
      work:    "収納力のある使いやすい洗面化粧台へ交換",
      change:  "清潔感が増し、朝の身支度もしやすくなりました。",
      comment: "限られたスペースに合わせて無駄なく交換しました。"
    },
    link: ""
  },
  {
    category: "外壁塗装",
    before: "lp_image_assets_png/cases/web/exterior_wall_before.jpg",
    after:  "lp_image_assets_png/cases/web/exterior_wall_after.jpg",
    spec:   { location: "外壁", period: "12日間", cost: "約95万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "築年数が経ち、外壁の色あせが目立ってきた",
      work:    "高圧洗浄・下地補修のうえ、外壁を全面塗装",
      change:  "落ち着いた色合いで、住まい全体の印象が引き締まりました。",
      comment: "周囲の環境になじむ色をご提案しました。"
    },
    link: ""
  },
  {
    category: "外構・庭工事",
    before: "lp_image_assets_png/cases/web/garden_before.jpg",
    after:  "lp_image_assets_png/cases/web/garden_after.jpg",
    spec:   { location: "庭・外構", period: "8日間", cost: "約60万円〜（目安）", building: "戸建て" },
    detail: {
      problem: "庭の手入れが大変で、使いにくい",
      work:    "整地・土間などを行い、手入れしやすい外構へ整備",
      change:  "雑草対策で日々のお手入れが楽になり、見た目もすっきり。",
      comment: "使い方に合わせて、動線と水はけを考えて設計しました。"
    },
    link: ""
  }
];
