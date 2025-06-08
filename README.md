# example
```bash
python watermark.py --font .\fonts\KiwiMaru-Regular.ttf --mode center --fit diag --stroke-width 4 --shadow-blur 6 --text "@maccha"
```

## 出力
生成画像は自動的に output/ フォルダへ。
元ファイル photo1.jpg → output/photo1_wm.jpg のように _wm が付きます。

## 主なオプション一覧
| オプション                 | 既定値            | 説明                                             |
| --------------------- | -------------- | ---------------------------------------------- |
| `-d, --dir`           | `pics`         | 入力ディレクトリ                                       |
| `-m, --mode`          | `bottom-right` | `bottom-right / center / tile / diagonal-tile` |
| `--text`              | `sample`       | 表示テキスト                                         |
| **フォントサイズ**           |                |                                                |
| `--font-size`         | ―              | 固定 px 指定（優先）                                   |
| `--font-ratio`        | `0.05`         | `基準値 × 比率` で算出                                 |
| `--fit`               | `diag`         | フォントサイズ算出基準 `long / short / width / height / diag`|
| **フォントファイル**          |                |                                                |
| `--font`              | ―              | TTF/TTC を明示指定                                  |
| **装飾**                |                |                                                |
| `--stroke-width`      | `0`            | ストローク（疑似太字）                                    |
| `--shadow-offset X Y` | `2 2`          | 影オフセット                                         |
| `--shadow-alpha`      | `180`          | 影の不透明度                                         |
| `--shadow-blur`       | `0`            | 影のガウスぼかし半径                                     |
| **タイル間隔**             |                |                                                |
| `--tile-step X Y`     | `1.0 1.0`      | tile の横・縦倍率                                    |
| `--diag-step`         | `1.5`          | 斜めタイルのステップ倍率                                   |
