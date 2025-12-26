"""
日本語テキスト描画用のヘルパーモジュール
OpenCVのputTextは日本語を表示できないため、PIL/Pillowを使用
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import glob

# 日本語フォントのパスを探す
def find_japanese_font():
    """システムにインストールされている日本語フォントを探す"""
    # よくある日本語フォントのパス
    font_paths = [
        # Notoフォント（Raspberry Pi OSに標準インストールされていることが多い）
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        # DejaVuフォント（フォールバック）
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        # その他の一般的なパス
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf',
    ]
    
    # パスから検索
    for path in font_paths:
        if os.path.exists(path):
            return path
    
    # ワイルドカードで検索
    search_patterns = [
        '/usr/share/fonts/**/*NotoSansCJK*.ttc',
        '/usr/share/fonts/**/*NotoSansCJK*.ttf',
        '/usr/share/fonts/**/*Noto*CJK*.ttc',
        '/usr/share/fonts/**/*.ttc',
        '/usr/share/fonts/**/*.ttf',
    ]
    
    for pattern in search_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return matches[0]
    
    # フォントが見つからない場合はNoneを返す（デフォルトフォントを使用）
    return None


# グローバルにフォントをキャッシュ
_cached_font = None
_cached_font_path = None

def get_font(size=20, font_path=None):
    """フォントを取得（キャッシュを使用）"""
    global _cached_font, _cached_font_path
    
    if font_path is None:
        font_path = find_japanese_font()
    
    # 同じフォントパスとサイズの場合はキャッシュを使用
    if _cached_font is not None and _cached_font_path == font_path:
        try:
            # サイズが異なる場合は再作成
            if hasattr(_cached_font, 'size') and _cached_font.size == size:
                return _cached_font
        except:
            pass
    
    try:
        if font_path and os.path.exists(font_path):
            # TTCファイル（TrueType Collection）の場合は、index=0で最初のフォントを使用
            # PILのImageFont.truetypeはTTCファイルも直接サポート
            if font_path.endswith('.ttc'):
                font = ImageFont.truetype(font_path, size, index=0)
            else:
                font = ImageFont.truetype(font_path, size)
            _cached_font = font
            _cached_font_path = font_path
            return font
    except Exception as e:
        print(f"Warning: Could not load font {font_path}: {e}")
    
    # フォントが見つからない場合はデフォルトフォントを使用
    try:
        font = ImageFont.load_default()
        _cached_font = font
        _cached_font_path = None
        return font
    except:
        return None


def put_japanese_text(img, text, pos, font_scale=1.0, color=(255, 255, 255), thickness=1):
    """
    OpenCV画像に日本語テキストを描画
    
    Args:
        img: OpenCV画像（BGR形式）
        text: 描画するテキスト（日本語可）
        pos: 位置 (x, y)
        font_scale: フォントサイズのスケール（OpenCVのfont_scaleと互換性を保つ）
        color: 色 (B, G, R)
        thickness: 線の太さ
    
    Returns:
        描画後の画像
    """
    # font_scaleをピクセルサイズに変換（OpenCVのfont_scale 0.6 ≈ 20px）
    font_size = int(font_scale * 33)  # OpenCVのFONT_HERSHEY_SIMPLEXのスケールに合わせる
    if font_size < 10:
        font_size = 10
    if font_size > 100:
        font_size = 100
    
    # PILで使用するフォントを取得
    font = get_font(font_size)
    
    # OpenCV画像（BGR）をPIL画像（RGB）に変換
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)
    
    # テキストを描画
    try:
        if font:
            draw.text(pos, text, font=font, fill=color[::-1])  # BGR→RGBに変換
        else:
            # フォントが見つからない場合はデフォルトフォントで描画
            draw.text(pos, text, fill=color[::-1])
    except Exception as e:
        # エラーが発生した場合は、テキストをASCII文字に置き換え
        try:
            ascii_text = text.encode('ascii', 'replace').decode('ascii')
            if font:
                draw.text(pos, ascii_text, font=font, fill=color[::-1])
            else:
                draw.text(pos, ascii_text, fill=color[::-1])
        except:
            pass
    
    # PIL画像（RGB）をOpenCV画像（BGR）に変換
    img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return img_bgr


def get_text_size_japanese(text, font_scale=1.0):
    """
    日本語テキストのサイズを取得
    
    Args:
        text: テキスト
        font_scale: フォントサイズのスケール
    
    Returns:
        (width, height), baseline
    """
    # font_scaleをピクセルサイズに変換
    font_size = int(font_scale * 33)
    if font_size < 10:
        font_size = 10
    if font_size > 100:
        font_size = 100
    
    # PILで使用するフォントを取得
    font = get_font(font_size)
    
    try:
        if font:
            # PILのgetbboxを使用してテキストサイズを取得
            from PIL import Image, ImageDraw
            dummy_img = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(dummy_img)
            bbox = draw.textbbox((0, 0), text, font=font)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            baseline = height  # 簡易的なbaseline
            return (width, height), baseline
        else:
            # フォントが見つからない場合は、OpenCVのgetTextSizeを使用（日本語は正確ではない）
            return cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)[0], 0
    except Exception as e:
        # エラーが発生した場合は、OpenCVのgetTextSizeを使用
        return cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)[0], 0

