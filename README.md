# Welcome to GitHub Desktop!

This is your README. READMEs are where you can communicate what your project is and how to use it.

Write your name on line 6, save it, and then head back to GitHub Desktop.

## トーキョー・チェイス

`tokyo-chase/index.html` は、スクウェア・エニックスの「チェイスチェイス」（スコットランドヤード系）に着想を得た、東京の路線図で遊ぶ追跡ボードゲームです。ブラウザで開くだけで遊べます（ビルド不要）。

- 泥棒（ターゲット）2人と警官（チェイサー）3人。役割を選び、もう一方はCPUが動かします。
- 泥棒の居場所は秘密。使った交通手段（電車・地下鉄・バス）だけが公開されます。
- ラウンド 3・7・11・15・19 の移動後は居場所が公開されます。
- 捕まった泥棒は「エージェント」になり、警官が入れない駅を作ります。
- 泥棒は交通手段を隠せる「シークレット切符」を3枚持っています。
- 20ラウンド逃げ切れば泥棒の勝ち、2人とも捕まえれば警察の勝ちです。
- 背景は東京湾・隅田川・皇居などを描いたSVGの街地図。線の形は電車＝枕木模様、地下鉄＝二重線、バス＝点線で区別します。

駅や路線は `STATIONS` と `LINES` の配列を書き換えるだけで変更できます。
