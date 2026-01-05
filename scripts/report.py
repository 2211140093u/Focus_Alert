import argparse
import os
import io
import base64
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_context("talk")


def b64_png(fig, dpi=400):
    """高解像度でPNG画像をBase64エンコード"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


essential_cols = [
    "ts","row_type","session","participant","task","phase","block_id",
    "ear","ear_base","ear_thr","blink_count","is_closed","long_close",
    "gaze","gaze_thr","gaze_bias","gaze_offlvl","risk","alert","event","info"
]


def load_log(path: str):
    df = pd.read_csv(path)
    missing = [c for c in essential_cols if c not in df.columns]
    if missing:
        print(f"[WARN] Missing columns in {path}: {missing}")
    df["source"] = str(path)
    df.sort_values("ts", inplace=True)
    frames = df[df["row_type"] == "frame"].copy()
    events = df[df["row_type"] == "event"].copy()
    # 型を数値/整数にそろえる
    for c in ["risk","ear","ear_base","ear_thr","gaze","gaze_thr","gaze_bias","gaze_offlvl"]:
        if c in frames:
            frames[c] = pd.to_numeric(frames[c], errors="coerce")
    for c in ["alert","is_closed","long_close"]:
        if c in frames:
            frames[c] = frames[c].fillna(0).astype(int)
    if "block_id" in frames:
        frames["block_id"] = frames["block_id"].fillna(-1).astype(int)
    # 注意分散（distractor）区間のタイムラインを復元
    frames["distractor_active"] = False
    ev = events.sort_values("ts")
    active = False
    idx = 0
    ev_list = ev.to_dict("records")
    for i, row in frames.iterrows():
        ts = row["ts"]
        while idx < len(ev_list) and ev_list[idx]["ts"] <= ts:
            e = ev_list[idx]
            if e.get("event") == "distractor_start":
                active = True
            elif e.get("event") == "distractor_end":
                active = False
            idx += 1
        frames.at[i, "distractor_active"] = active
    return frames, events


def figure_concentration(frames: pd.DataFrame, title: str, dpi=400):
    """集中度スコアの時系列グラフ（個別画像）"""
    fig, ax = plt.subplots(figsize=(12, 6), dpi=dpi)
    t = frames["ts"].values
    # リスクスコアを集中度スコアに変換（1.0 - risk）
    concentration = 1.0 - frames["risk"]
    ax.plot(t, concentration, label="Concentration", color="#1f77b4", linewidth=1.5)
    if "alert" in frames:
        a = frames[frames["alert"] > 0]
        if len(a):
            # アラート時の集中度スコアも変換
            alert_concentration = 1.0 - a["risk"]
            ax.scatter(a["ts"], alert_concentration, color="red", s=20, label="Alert", zorder=5)
    # 注意分散区間を縦線でマーキング
    if "distractor_active" in frames:
        dmask = frames["distractor_active"].values
        for i in range(1, len(dmask)):
            if dmask[i] and not dmask[i-1]:
                start = frames["ts"].iloc[i]
                ax.axvline(start, color="orange", alpha=0.3, linestyle=":")
            if not dmask[i] and dmask[i-1]:
                end = frames["ts"].iloc[i]
                ax.axvline(end, color="orange", alpha=0.3, linestyle=":")
    ax.set_xlabel("Timestamp (s)", fontsize=12)
    ax.set_ylabel("Concentration Score", fontsize=12)
    ax.set_title(f"Concentration Score Time Series - {title}", fontsize=14, fontweight='bold')
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)
    # Y軸の範囲を0-1に設定（集中度スコアは0-1の範囲）
    ax.set_ylim(0, 1)
    fig.tight_layout()
    return fig

def figure_ear(frames: pd.DataFrame, title: str, dpi=400):
    """EAR（Eye Aspect Ratio）の時系列グラフ（個別画像）"""
    fig, ax = plt.subplots(figsize=(12, 6), dpi=dpi)
    t = frames["ts"].values
    if "ear" in frames:
        ax.plot(t, frames["ear"], label="EAR", color="#2ca02c", linewidth=1.5)
    if "ear_base" in frames:
        ax.plot(t, frames["ear_base"], label="EAR baseline", color="#98df8a", alpha=0.8, linewidth=1.2)
    if "ear_thr" in frames:
        ax.plot(t, frames["ear_thr"], label="EAR threshold", color="#d62728", alpha=0.6, linestyle="--", linewidth=1.2)
    # 注意分散区間を縦線でマーキング
    if "distractor_active" in frames:
        dmask = frames["distractor_active"].values
        for i in range(1, len(dmask)):
            if dmask[i] and not dmask[i-1]:
                start = frames["ts"].iloc[i]
                ax.axvline(start, color="orange", alpha=0.3, linestyle=":")
            if not dmask[i] and dmask[i-1]:
                end = frames["ts"].iloc[i]
                ax.axvline(end, color="orange", alpha=0.3, linestyle=":")
    ax.set_xlabel("Timestamp (s)", fontsize=12)
    ax.set_ylabel("EAR (Eye Aspect Ratio)", fontsize=12)
    ax.set_title(f"EAR Time Series - {title}", fontsize=14, fontweight='bold')
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig

def figure_gaze(frames: pd.DataFrame, title: str, dpi=400):
    """視線（Gaze）の時系列グラフ（個別画像）"""
    fig, ax = plt.subplots(figsize=(12, 6), dpi=dpi)
    t = frames["ts"].values
    if "gaze" in frames:
        ax.plot(t, frames["gaze"], label="Gaze (horizontal)", color="#9467bd", linewidth=1.5)
    if "gaze_thr" in frames:
        try:
            thr = np.nanmedian(frames["gaze_thr"].values)
            ax.axhline(thr, color="#c5b0d5", linestyle="--", label="Gaze threshold", linewidth=1.2)
            ax.axhline(-thr, color="#c5b0d5", linestyle="--", linewidth=1.2)
        except Exception:
            pass
    # 注意分散区間を縦線でマーキング
    if "distractor_active" in frames:
        dmask = frames["distractor_active"].values
        for i in range(1, len(dmask)):
            if dmask[i] and not dmask[i-1]:
                start = frames["ts"].iloc[i]
                ax.axvline(start, color="orange", alpha=0.3, linestyle=":")
            if not dmask[i] and dmask[i-1]:
                end = frames["ts"].iloc[i]
                ax.axvline(end, color="orange", alpha=0.3, linestyle=":")
    ax.set_xlabel("Timestamp (s)", fontsize=12)
    ax.set_ylabel("Gaze Offset (normalized)", fontsize=12)
    ax.set_title(f"Gaze Time Series - {title}", fontsize=14, fontweight='bold')
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig

def figure_timeseries(frames: pd.DataFrame, title: str, dpi=200):
    """後方互換性のための関数（使用されない可能性があるが、念のため保持）"""
    # この関数は使用されないが、後方互換性のため保持
    fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True, dpi=dpi)
    t = frames["ts"].values
    # リスク
    axes[0].plot(t, frames["risk"], label="Risk", color="#1f77b4")
    if "alert" in frames:
        a = frames[frames["alert"] > 0]
        if len(a):
            axes[0].scatter(a["ts"], a["risk"], color="red", s=12, label="Alert")
    axes[0].set_ylabel("Risk")
    axes[0].legend(loc="upper right")
    # EAR
    if "ear" in frames:
        axes[1].plot(t, frames["ear"], label="EAR", color="#2ca02c")
    if "ear_base" in frames:
        axes[1].plot(t, frames["ear_base"], label="EAR base", color="#98df8a", alpha=0.8)
    if "ear_thr" in frames:
        axes[1].plot(t, frames["ear_thr"], label="EAR thr", color="#d62728", alpha=0.6, linestyle="--")
    axes[1].set_ylabel("EAR")
    axes[1].legend(loc="upper right")
    # 視線（Gaze）
    if "gaze" in frames:
        axes[2].plot(t, frames["gaze"], label="Gaze", color="#9467bd")
    if "gaze_thr" in frames:
        try:
            thr = np.nanmedian(frames["gaze_thr"].values)
            axes[2].axhline(thr, color="#c5b0d5", linestyle="--", label="Gaze thr")
            axes[2].axhline(-thr, color="#c5b0d5", linestyle="--")
        except Exception:
            pass
    axes[2].set_ylabel("Gaze")
    axes[2].set_xlabel("Timestamp (s)")
    axes[2].legend(loc="upper right")
    # 注意分散区間を縦線でマーキング（軽量化のためおよそ1fpsで処理）
    if "distractor_active" in frames:
        y0, y1 = axes[0].get_ylim()
        dmask = frames["distractor_active"].values
        for i in range(1, len(dmask)):
            if dmask[i] and not dmask[i-1]:
                start = frames["ts"].iloc[i]
                axes[0].axvline(start, color="orange", alpha=0.3)
            if not dmask[i] and dmask[i-1]:
                end = frames["ts"].iloc[i]
                axes[0].axvline(end, color="orange", alpha=0.3)
    fig.suptitle(title)
    fig.tight_layout()
    return fig

def figure_gaze_scatter(frames: pd.DataFrame, title: str):
    fig, ax = plt.subplots(figsize=(6,6))
    gx = frames.get('gaze', pd.Series(dtype=float))
    gy = frames.get('gaze_y', pd.Series(dtype=float))
    ax.scatter(gx, gy, s=4, alpha=0.3)
    # 閾値の補助線
    if 'gaze_thr' in frames:
        thr = np.nanmedian(frames['gaze_thr'])
        ax.axvline(thr, color='gray', ls='--', lw=1)
        ax.axvline(-thr, color='gray', ls='--', lw=1)
    if 'gaze_y_thr' in frames:
        thry = np.nanmedian(frames['gaze_y_thr'])
        ax.axhline(thry, color='gray', ls='--', lw=1)
        ax.axhline(-thry, color='gray', ls='--', lw=1)
    ax.set_xlabel('Gaze X')
    ax.set_ylabel('Gaze Y')
    ax.set_title(f'Gaze XY scatter — {title}')
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect('equal', adjustable='box')
    fig.tight_layout()
    return fig

def figure_gaze_heatmap(frames: pd.DataFrame, title: str, bins=50):
    fig, ax = plt.subplots(figsize=(6,6))
    gx = frames.get('gaze', pd.Series(dtype=float)).to_numpy()
    gy = frames.get('gaze_y', pd.Series(dtype=float)).to_numpy()
    gx = gx[np.isfinite(gx)]
    gy = gy[np.isfinite(gy)]
    if len(gx) and len(gy):
        h, xedges, yedges = np.histogram2d(gx, gy, bins=bins, range=[[-1.2,1.2],[-1.2,1.2]])
        im = ax.imshow(h.T, origin='lower', extent=[-1.2,1.2,-1.2,1.2], cmap='viridis', aspect='equal')
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xlabel('Gaze X')
    ax.set_ylabel('Gaze Y')
    ax.set_title(f'Gaze XY heatmap — {title}')
    fig.tight_layout()
    return fig


def figure_histograms(frames: pd.DataFrame, title: str):
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))
    # リスクスコアを集中度スコアに変換（1.0 - risk）
    concentration = 1.0 - frames["risk"]
    sns.histplot(concentration, bins=40, ax=axes[0], color="#1f77b4")
    axes[0].set_title("Concentration distribution")
    if "ear" in frames:
        sns.histplot(frames["ear"], bins=40, ax=axes[1], color="#2ca02c")
        axes[1].set_title("EAR distribution")
    if "gaze" in frames:
        sns.histplot(frames["gaze"], bins=40, ax=axes[2], color="#9467bd")
        axes[2].set_title("Gaze distribution")
    fig.suptitle(title)
    fig.tight_layout()
    return fig


def summarize(frames: pd.DataFrame):
    s = {}
    s["frames"] = len(frames)
    # リスクスコアを集中度スコアに変換（1.0 - risk）
    risk_series = frames.get("risk", pd.Series(dtype=float))
    concentration_series = 1.0 - risk_series
    s["concentration_mean"] = float(np.nanmean(concentration_series))
    s["concentration_p95"] = float(np.nanpercentile(concentration_series, 95)) if len(concentration_series) > 0 else np.nan
    # 後方互換性のため、risk_meanとrisk_p95も保持（集中度スコアから逆算）
    s["risk_mean"] = 1.0 - s["concentration_mean"]
    s["risk_p95"] = 1.0 - s["concentration_p95"] if not np.isnan(s["concentration_p95"]) else np.nan
    if "blink_count" in frames:
        s["blink_count_max"] = int(frames["blink_count"].max())
    s["long_close_count"] = int(frames.get("long_close", pd.Series([0])).sum()) if "long_close" in frames else 0
    # 視線逸脱レベルの平均（オフ滞留の近似）
    s["off_level_mean"] = float(np.nanmean(frames.get("gaze_offlvl", pd.Series(dtype=float)))) if "gaze_offlvl" in frames else np.nan
    # 注意分散の割合
    if "distractor_active" in frames:
        s["distractor_ratio"] = float(frames["distractor_active"].mean())
    else:
        s["distractor_ratio"] = np.nan
    return s


def save_report_images(sections, image_dir, html_path):
    """レポートの各グラフを個別画像として保存し、メタデータを生成"""
    import json
    import base64
    
    html_name = Path(html_path).stem
    # レポートベース名（ファイル名のみ、拡張子なし）
    report_base_name = html_name.replace('.html', '')
    
    # 最初のセクションのみ処理（複数セクション対応は将来の拡張）
    if not sections:
        return
    
    section = sections[0]
    pages = []
    
    # メタ情報ページ
    if section.get('meta'):
        pages.append({
            'type': 'meta',
            'title': f"{section['title']} - 情報",
            'data': section['meta']
        })
    
    # サマリ統計ページ
    if section.get('summary'):
        pages.append({
            'type': 'summary',
            'title': f"{section['title']} - 統計",
            'data': section['summary']
        })
    
    # 画像ページ（各グラフを1ページずつ）
    image_b64_list = section.get('images', [])
    # 時系列グラフは3つに分割されているので、タイトルも3つに分ける
    image_types = ['Concentration Time Series', 'EAR Time Series', 'Gaze Time Series', 'Distribution Histograms', 'Gaze Scatter', 'Gaze Heatmap']
    
    for img_idx, img_b64 in enumerate(image_b64_list):
        if img_idx < len(image_types):
            img_title_base = f"{section['title']} - {image_types[img_idx]}"
        else:
            img_title_base = f"{section['title']} - Graph {img_idx + 1}"
        
        # Base64デコード
        try:
            img_data = base64.b64decode(img_b64)
            import io
            from PIL import Image
            import numpy as np
            
            # PILで画像を読み込み
            pil_img = Image.open(io.BytesIO(img_data))
            
            # 高解像度画像として保存（DPI=400相当の解像度を維持）
            img_filename = f"{report_base_name}_p{len(pages)}.png"
            img_path = os.path.join(image_dir, img_filename)
            
            # 高解像度で保存（元の解像度を維持）
            pil_img.save(img_path, 'PNG', quality=95)
            
            # 相対パスで保存
            rel_path = os.path.relpath(img_path, image_dir) if os.path.isabs(img_path) else img_filename
            pages.append({
                'type': 'image',
                'title': img_title_base,
                'path': rel_path
            })
        except Exception as e:
            print(f"Error saving image {img_idx}: {e}")
            import traceback
            traceback.print_exc()
    
    # メタデータを保存
    meta_filename = f"{report_base_name}_meta.json"
    meta_file = os.path.join(image_dir, meta_filename)
    meta_data = {
        'title': section['title'],
        'meta': section.get('meta', {}),
        'pages': pages
    }
    
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved report images to {image_dir}")
    print(f"Saved metadata to {meta_file}")


def html_report(sections, title="Focus Alert Session Report"):
    html = [
        "<html><head><meta charset='utf-8'><title>{}</title>".format(title),
        "<style>body{font-family:Segoe UI,Arial; margin:20px;} h2{margin-top:30px;} .sec{margin-bottom:40px;} table{border-collapse:collapse;} td,th{border:1px solid #ddd;padding:6px 10px;} .kv td{border:none;padding:2px 6px;} .img{margin:8px 0;}</style>",
        "</head><body>",
        f"<h1>{title}</h1>",
    ]
    for sec in sections:
        html.append("<div class='sec'>")
        html.append(f"<h2>{sec['title']}</h2>")
        if "meta" in sec and sec["meta"]:
            html.append("<table class='kv'>")
            for k,v in sec["meta"].items():
                html.append(f"<tr><td><b>{k}</b></td><td>{v}</td></tr>")
            html.append("</table>")
        if "summary" in sec and sec["summary"]:
            html.append("<table>")
            html.append("<tr>" + "".join([f"<th>{k}</th>" for k in sec["summary"].keys()]) + "</tr>")
            html.append("<tr>" + "".join([f"<td>{v}</td>" for v in sec["summary"].values()]) + "</tr>")
            html.append("</table>")
        for img in sec.get("images", []):
            html.append(f"<div class='img'><img src='data:image/png;base64,{img}'/></div>")
        html.append("</div>")
    html.append("</body></html>")
    return "\n".join(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True, nargs="+", help="CSV ログのパス（複数可）")
    ap.add_argument("--out", required=True, help="出力HTMLのパス")
    ap.add_argument("--title", default="Focus Alert Session Report")
    ap.add_argument("--save-images", action="store_true", help="グラフを個別画像ファイルとして保存（アプリ内表示用）")
    ap.add_argument("--image-dir", default=None, help="画像保存ディレクトリ（--save-images使用時）")
    args = ap.parse_args()

    sections = []
    for lp in args.log:
        frames, events = load_log(lp)
        # CSV内のメタ行（row_type=meta）を取得
        meta_row = None
        try:
            dfm = pd.read_csv(lp)
            meta = dfm[dfm["row_type"]=="meta"].tail(1)
            meta_row = meta.iloc[0].to_dict() if len(meta) else {}
        except Exception:
            meta_row = {}
        sess_title = f"{Path(lp).name}"
        # 図表の生成（高解像度で生成：dpi=400）
        # 時系列グラフを3つの別々の画像として生成
        concentration_fig = figure_concentration(frames, title=sess_title, dpi=400)
        concentration_b64 = b64_png(concentration_fig, dpi=400)
        ear_fig = figure_ear(frames, title=sess_title, dpi=400)
        ear_b64 = b64_png(ear_fig, dpi=400)
        gaze_fig = figure_gaze(frames, title=sess_title, dpi=400)
        gaze_b64 = b64_png(gaze_fig, dpi=400)
        
        hist_fig = figure_histograms(frames, title=sess_title)
        hist_b64 = b64_png(hist_fig, dpi=400)
        # 視線の2次元表示
        imgs = [concentration_b64, ear_b64, gaze_b64, hist_b64]
        if 'gaze_y' in frames.columns:
            scat = b64_png(figure_gaze_scatter(frames, title=sess_title), dpi=400)
            heat = b64_png(figure_gaze_heatmap(frames, title=sess_title), dpi=400)
            imgs.extend([scat, heat])
        # サマリ統計
        summ = summarize(frames)
        sections.append({
            "title": sess_title,
            "meta": {
                "session": frames["session"].iloc[0] if "session" in frames and len(frames) else meta_row.get("session"),
                "participant": frames["participant"].iloc[0] if "participant" in frames and len(frames) else meta_row.get("participant"),
                "task": frames["task"].iloc[0] if "task" in frames and len(frames) else meta_row.get("task"),
                "phase": frames["phase"].iloc[0] if "phase" in frames and len(frames) else meta_row.get("phase"),
                "blocks": int(frames["block_id"].replace(-1, np.nan).nunique()) if "block_id" in frames else None,
                "rows": len(frames),
            },
            "summary": summ,
            "images": imgs,
        })

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    html = html_report(sections, title=args.title)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved report to {args.out}")
    
    # アプリ内表示用の画像とメタデータを保存
    if args.save_images:
        image_dir = args.image_dir if args.image_dir else out_dir
        save_report_images(sections, image_dir, args.out)


if __name__ == "__main__":
    main()
