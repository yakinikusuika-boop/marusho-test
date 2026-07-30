/* ===== アクセス解析（GA4）：反響につながる操作の計測 =====
   訪問数だけでなく「実際に問い合わせようとした動き」を記録します。
   記録するイベント：
     tel_tap        … 電話番号のタップ／クリック（ページ内のどの位置から掛けたかも記録）
     contact_submit … お問い合わせフォームの送信成功（index.html の送信処理から呼び出し）
     contact_mailto … メールソフト起動方式での送信（フォーム送信サービスが使えない場合の予備動線）
     coupon_view    … 割引券ページの表示
   GA4の管理画面で、これらを「キーイベント」に登録すると、
   チラシ経由の訪問から何件の反響が出たかまで紐づいて見られます。
*/
(function () {
  // 広告ブロッカー等でgtag.jsが読み込めなかった場合でも、サイト本体が壊れないようにする
  function track(name, params) {
    if (typeof window.gtag === 'function') {
      window.gtag('event', name, params || {});
    }
  }
  window.msTrack = track;

  // ----- 電話タップ -----
  // 電話リンクはヘッダー・CTA・本文・会社概要・スマホ追尾ボタンに分散しているため、
  // 個別に付けず、document側でまとめて監視する（リンクを増やしても計測が漏れない）
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || typeof t.closest !== 'function') return;
    var a = t.closest('a[href^="tel:"]');
    if (!a) return;
    track('tel_tap', {
      phone_number: a.getAttribute('href').replace('tel:', ''),
      link_location: telLocation(a)
    });
  });

  // どの位置の電話リンクが押されたかを、日本語のラベルで残す
  // （どの導線が電話につながっているかが分かるので、改善の判断材料になる）
  var TEL_PLACES = [
    ['.sticky-phone', 'スマホ追尾ボタン'],
    ['.hero-phone', 'ファーストビュー'],
    ['.cta-phone', '中間CTA'],
    ['#contact', 'お問い合わせ欄'],
    ['.access-info', '会社概要・アクセス']
  ];
  function telLocation(a) {
    for (var i = 0; i < TEL_PLACES.length; i++) {
      if (a.closest(TEL_PLACES[i][0])) return TEL_PLACES[i][1];
    }
    return 'その他';
  }

  // ----- 割引券ページの表示 -----
  // 割引券まで見た人は検討度が高いため、通常のページ表示とは別に数える
  if (/coupon\.html$/.test(location.pathname)) {
    track('coupon_view');
  }
})();
