# Welcome to GitHub Desktop!

This is your README. READMEs are where you can communicate what your project is and how to use it.

Write your name on line 6, save it, and then head back to GitHub Desktop.

## トーキョー・ヤード

`tokyo-chase/index.html` は、スコットランドヤード（とスクウェア・エニックスの「チェイスチェイス」）に着想を得た、東京の路線図で遊ぶ追跡ボードゲームです。ブラウザで開くだけで遊べます（ビルド不要）。

### ルール
- 怪盗X 1人 対 刑事4人。怪盗Xの居場所は秘密で、使った切符（電車・地下鉄・バス・黒）だけが公開されます。
- 3・8・13・18手目の移動後は怪盗Xが姿を現します。18手逃げ切れば怪盗Xの勝ち。
- 刑事の切符は有限（電車10・バス8・地下鉄4）。怪盗Xは黒チケット5枚（手段を隠す／水上バスに乗れる）と2倍移動3枚を持っています。
- 刑事が怪盗Xのいる駅に入れば逮捕。刑事全員が動けなくなると怪盗Xの勝ち。

### モード
- **ひとりで遊ぶ**：怪盗X側か刑事側を選び、残りはCPUが動かします。
- **オンライン対戦**：claude.ai 上で開くと、ロビーでルームを作って友だちと対戦できます（Artifact の共有データベースを使用）。空いた刑事の席はCPUが担当し、怪盗Xの現在地はX本人だけが読める領域に保存されます。

駅や路線は `STATIONS` と `LINES`、ルールの数値は `MAX_MOVES` などの定数で変更できます。
