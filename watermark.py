from __future__ import annotations
from pathlib import Path
from typing import Iterable, Tuple

import argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps


# ────────────────────────── フォントロード ──────────────────────────
def load_font(size: int, font_path: str | None = None) -> ImageFont.FreeTypeFont:
    """日本語テキストを描画できる TTF/TTC フォントを返す。"""
    candidates = [
        font_path,  # --font 指定が最優先
        Path("fonts/NotoSansJP-Regular.ttfa"),
    ]
    for fp in filter(None, candidates):
        try:
            return ImageFont.truetype(fp, size=size)
        except OSError:
            continue
    raise FileNotFoundError("日本語対応フォントが見つかりません。--font で直接指定してください。")


# ────────── 影＋ストローク付きテキスト描画ユーティリティ ──────────
def paint_shadowed_text(
    base: Image.Image,
    pos: Tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int, int],
    *,
    stroke_width: int = 0,
    shadow_offset: Tuple[int, int] = (2, 2),
    shadow_alpha: int = 180,
    shadow_blur: int = 0,
) -> None:
    """ドロップシャドウ＋ストロークを付けてテキストを描画"""
    x, y = pos

    if shadow_alpha and shadow_offset != (0, 0):
        shadow_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow_layer)
        shadow_fill = (0, 0, 0, shadow_alpha)
        s_draw.text(
            (x + shadow_offset[0], y + shadow_offset[1]),
            text,
            font=font,
            fill=shadow_fill,
            stroke_width=stroke_width,
            stroke_fill=shadow_fill,
        )
        if shadow_blur > 0:
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
        base.alpha_composite(shadow_layer)

    draw = ImageDraw.Draw(base)
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=fill,
    )

# ──────────────── ウォーターマーク合成 ────────────────
def add_watermark_to_image(
    img: Image.Image,
    *,
    text: str,
    font: ImageFont.FreeTypeFont,
    mode: str = "bottom-right",
    opacity: int = 128,
    margin: int = 20,
    stroke_width: int = 0,
    shadow_offset: Tuple[int, int] = (2, 2),
    shadow_alpha: int = 180,
    shadow_blur: int = 0,
    tile_step: Tuple[float, float] = (1.0, 1.0),
    diag_step: float = 1.5,
) -> Image.Image:
    """img にウォーターマークを合成して新しい Image を返す"""
    w, h = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    tmp_draw = ImageDraw.Draw(overlay)
    tw, th = tmp_draw.textbbox((0, 0), text, font=font)[2:]  # text width/height
    fill = (255, 255, 255, opacity)

    def add_at(x: int, y: int) -> None:
        paint_shadowed_text(
            overlay,
            (x, y),
            text,
            font,
            fill,
            stroke_width=stroke_width,
            shadow_offset=shadow_offset,
            shadow_alpha=shadow_alpha,
            shadow_blur=shadow_blur,
        )

    if mode == "bottom-right":
        add_at(w - tw - margin, h - th - margin)

    elif mode == "center":
        add_at((w - tw) // 2, (h - th) // 2)

    elif mode == "tile":
        step_x = int((tw + margin) * tile_step[0])
        step_y = int((th + margin) * tile_step[1])
        for yy in range(0, h, step_y):
            for xx in range(0, w, step_x):
                add_at(xx, yy)

    elif mode == "diagonal-tile":
        tile_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        step = int(max(tw, th) * diag_step)
        for yy in range(-h, h * 2, step):
            for xx in range(-w, w * 2, step):
                paint_shadowed_text(
                    tile_layer,
                    (xx, yy),
                    text,
                    font,
                    fill,
                    stroke_width=stroke_width,
                    shadow_offset=shadow_offset,
                    shadow_alpha=shadow_alpha,
                    shadow_blur=shadow_blur,
                )
        overlay = Image.alpha_composite(overlay, tile_layer.rotate(45, expand=False))

    else:
        raise ValueError(f"unknown mode: {mode}")

    return Image.alpha_composite(img.convert("RGBA"), overlay)

# ──────────────────── バッチ処理 ────────────────────
def iter_image_files(
    directory: Path,
    exts: Iterable[str] = (".png", ".jpg", ".jpeg", ".webp", ".bmp"),
):
    yield from (p for p in directory.iterdir() if p.suffix.lower() in exts)

def process_directory(
    directory: Path,
    *,
    text: str,
    mode: str,
    font_size: int | None,
    font_ratio: float,
    fit: str,
    opacity: int,
    margin_ratio: float,
    font_path: str | None,
    stroke_width: int,
    shadow_offset: Tuple[int, int],
    shadow_alpha: int,
    shadow_blur: int,
    tile_step: Tuple[float, float],
    diag_step: float,
) -> None:
    directory = directory.expanduser().resolve()
    if not directory.is_dir():
        raise NotADirectoryError(directory)

    files = list(iter_image_files(directory))
    if not files:
        print("⚠️  対象画像が見つかりませんでした。")
        return

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    for img_path in files:
        img = Image.open(img_path)
        img = ImageOps.exif_transpose(img) # スマホやカメラで撮った JPEG には EXIF Orientation 回転情報が含まれることがあるので、正しい向きに変換
        w, h = img.size

        # フォントサイズ計算
        if font_size:
            size = font_size
        else:
            base = {
                "width": w,
                "height": h,
                "long": max(w, h),
                "short": min(w, h),
                "diag": int((w**2 + h**2) ** 0.5),
            }[fit]
            size = int(base * font_ratio)

        font = load_font(size, font_path)

        wm_img = add_watermark_to_image(
            img,
            text=text,
            font=font,
            mode=mode,
            opacity=opacity,
            margin=int(max(w, h) * margin_ratio),
            stroke_width=stroke_width,
            shadow_offset=shadow_offset,
            shadow_alpha=shadow_alpha,
            shadow_blur=shadow_blur,
            tile_step=tile_step,
            diag_step=diag_step,
        )

        out_path = out_dir / f"{img_path.stem}_wm{img_path.suffix}"
        wm_img.convert("RGB").save(out_path, quality=95)
        print(f"✅  {out_path.name} 生成完了")

# ──────────────────── CLI ────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="フォルダ内画像に影付きウォーターマークを一括挿入"
    )
    p.add_argument("-d", "--dir", default=Path("pics"), type=Path, help="入力ディレクトリ")

    p.add_argument(
        "-m",
        "--mode",
        choices=["bottom-right", "center", "tile", "diagonal-tile"],
        default="bottom-right",
        help="配置モード",
    )
    p.add_argument("--text", default="sample", help="表示テキスト")
    p.add_argument("--font-size", type=int, help="固定フォントサイズ(px)")
    p.add_argument("--font-ratio", type=float, default=0.05, help="基準値×比率")
    p.add_argument(
        "--fit",
        choices=["long", "short", "width", "height", "diag"],
        default="diag",
        help="フォントサイズ算出基準",
    )
    p.add_argument("--opacity", type=int, default=128, help="不透明度 0–255")
    p.add_argument("--margin-ratio", type=float, default=0.02, help="余白倍率")
    p.add_argument("--font", dest="font_path", help="TTF/TTC フォントファイル")

    # スタイル
    p.add_argument("--stroke-width", type=int, default=0, help="ストローク幅(px)")
    p.add_argument(
        "--shadow-offset",
        nargs=2,
        type=int,
        metavar=("X", "Y"),
        default=(2, 2),
        help="影オフセット(px)",
    )
    p.add_argument("--shadow-alpha", type=int, default=180, help="影不透明度0–255")
    p.add_argument("--shadow-blur", type=int, default=0, help="影ぼかし半径(px)")

    # タイル間隔調整
    p.add_argument(
        "--tile-step",
        nargs=2,
        type=float,
        metavar=("X_FACTOR", "Y_FACTOR"),
        default=(1.0, 1.0),
        help="tile モードのステップ倍率（文字+余白 に掛ける）",
    )
    p.add_argument(
        "--diag-step",
        type=float,
        default=1.5,
        help="diagonal‐tile のステップ倍率（デフォ 1.5）",
    )

    return p.parse_args()

# ──────────────────── main ────────────────────
if __name__ == "__main__":
    args = parse_args()
    process_directory(
        directory=args.dir,
        text=args.text,
        mode=args.mode,
        font_size=args.font_size,
        font_ratio=args.font_ratio,
        fit=args.fit,
        opacity=args.opacity,
        margin_ratio=args.margin_ratio,
        font_path=args.font_path,
        stroke_width=args.stroke_width,
        shadow_offset=tuple(args.shadow_offset),
        shadow_alpha=args.shadow_alpha,
        shadow_blur=args.shadow_blur,
        tile_step=tuple(args.tile_step),
        diag_step=args.diag_step,
    )