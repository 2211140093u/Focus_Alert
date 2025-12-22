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


def b64_png(fig, dpi=120):
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


def figure_timeseries(frames: pd.DataFrame, title: str):
    fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
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
    sns.histplot(frames["risk"], bins=40, ax=axes[0], color="#1f77b4")
    axes[0].set_title("Risk distribution")
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
    s["risk_mean"] = float(np.nanmean(frames.get("risk", pd.Series(dtype=float))))
    s["risk_p95"] = float(np.nanpercentile(frames.get("risk", pd.Series(dtype=float)), 95)) if "risk" in frames else np.nan
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
        # 図表の生成
        ts_fig = figure_timeseries(frames, title=sess_title)
        ts_b64 = b64_png(ts_fig)
        hist_fig = figure_histograms(frames, title=sess_title)
        hist_b64 = b64_png(hist_fig)
        # 視線の2次元表示
        imgs = [ts_b64, hist_b64]
        if 'gaze_y' in frames.columns:
            scat = b64_png(figure_gaze_scatter(frames, title=sess_title))
            heat = b64_png(figure_gaze_heatmap(frames, title=sess_title))
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


if __name__ == "__main__":
    main()
