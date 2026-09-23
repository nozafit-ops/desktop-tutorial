# Welcome to GitHub Desktop!

This is your README. READMEs are where you can communicate what your project is and how to use it.

Write your name on line 6, save it, and then head back to GitHub Desktop.

## トーキョー・チェイス

`tokyo-chase/index.html` は、スクウェア・エニックスの「チェイスチェイス」（スコットランドヤード系）に着想を得た、東京の路線図で遊ぶ追跡ボードゲームです。ブラウザで開くだけで遊べます（ビルド不要）。

- ターゲット2人、チェイサー3人。役割を選び、もう一方はCPUが動かします。
- ターゲットの居場所は秘密。使った交通手段（電車・地下鉄・バス）だけが公開されます。
- ラウンド 3・7・11・15・19 の移動後は居場所が公開されます。
- 捕まったターゲットは「エージェント」になり、チェイサーが入れない駅を作ります。
- ターゲットは交通手段を隠せる「シークレット切符」を3枚持っています。
- 20ラウンド逃げ切ればターゲットの勝ち、2人とも捕まえればチェイサーの勝ちです。

駅や路線は `STATIONS` と `LINES` の配列を書き換えるだけで変更できます。
