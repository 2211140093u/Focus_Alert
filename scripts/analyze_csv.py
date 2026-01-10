#!/usr/bin/env python3
"""
CSVログファイルを分析するスクリプト
ブロックごとの統計情報を出力します。
"""
import argparse
import pandas as pd
import numpy as np
from pathlib import Path


def load_log(path: str):
    """CSVログファイルを読み込む"""
    df = pd.read_csv(path)
    # メタ情報を取得
    meta_row = df[df["row_type"] == "meta"].iloc[0] if len(df[df["row_type"] == "meta"]) > 0 else None
    
    # フレームデータとイベントデータを分離
    frames = df[df["row_type"] == "frame"].copy()
    events = df[df["row_type"] == "event"].copy()
    
    # 数値列を変換
    numeric_cols = ["ts", "ear", "ear_base", "ear_thr", "blink_count", "gaze", 
                    "gaze_thr", "gaze_bias", "gaze_y", "gaze_y_thr", "gaze_bias_y",
                    "gaze_offlvl", "risk", "alert", "is_closed", "long_close", "block_id",
                    "has_face", "has_iris"]
    for col in numeric_cols:
        if col in frames.columns:
            frames[col] = pd.to_numeric(frames[col], errors="coerce")
    
    if "block_id" in frames:
        frames["block_id"] = frames["block_id"].fillna(-1).astype(int)
    
    # 顔検出に失敗したフレームを除外
    if "has_face" in frames.columns:
        original_count = len(frames)
        frames = frames[frames["has_face"] == 1].copy()
        excluded_count = original_count - len(frames)
        if excluded_count > 0:
            print(f"Note: Excluded {excluded_count} frames where face detection failed (out of {original_count} total frames)")
    
    return frames, events, meta_row


def analyze_by_block(frames: pd.DataFrame, events: pd.DataFrame):
    """ブロックごとの統計を計算"""
    # ブロックの開始・終了時刻を取得
    block_starts = events[events["event"] == "block_start"].copy()
    block_ends = events[events["event"] == "block_end"].copy()
    
    results = []
    
    # 各ブロックについて分析
    unique_blocks = sorted(frames["block_id"].unique())
    unique_blocks = [b for b in unique_blocks if b > 0]  # -1（未分類）を除外
    
    for block_id in unique_blocks:
        block_frames = frames[frames["block_id"] == block_id].copy()
        if len(block_frames) == 0:
            continue
        
        # ブロックの開始・終了時刻
        block_start_ts = block_frames["ts"].min()
        block_end_ts = block_frames["ts"].max()
        duration = block_end_ts - block_start_ts
        
        # 集中度スコア（1.0 - risk）
        concentration = 1.0 - block_frames["risk"]
        
        # 統計情報
        stats = {
            "block_id": int(block_id),
            "duration_sec": float(duration),
            "duration_min": float(duration / 60.0),
            "frame_count": len(block_frames),
            # 集中度スコア
            "concentration_mean": float(np.nanmean(concentration)),
            "concentration_std": float(np.nanstd(concentration)),
            "concentration_min": float(np.nanmin(concentration)),
            "concentration_max": float(np.nanmax(concentration)),
            "concentration_median": float(np.nanmedian(concentration)),
            # まばたき
            "blink_count_max": int(block_frames["blink_count"].max()) if "blink_count" in block_frames else 0,
            "blink_count_final": int(block_frames["blink_count"].iloc[-1]) if "blink_count" in block_frames else 0,
            # 長時間閉眼
            "long_close_count": int(block_frames["long_close"].sum()) if "long_close" in block_frames else 0,
            # EAR
            "ear_mean": float(np.nanmean(block_frames["ear"])) if "ear" in block_frames else np.nan,
            "ear_std": float(np.nanstd(block_frames["ear"])) if "ear" in block_frames else np.nan,
            # 視線逸脱
            "gaze_offlvl_mean": float(np.nanmean(block_frames["gaze_offlvl"])) if "gaze_offlvl" in block_frames else np.nan,
            "gaze_offlvl_max": float(np.nanmax(block_frames["gaze_offlvl"])) if "gaze_offlvl" in block_frames else np.nan,
            # アラート
            "alert_count": int(block_frames["alert"].sum()) if "alert" in block_frames else 0,
        }
        
        results.append(stats)
    
    return results


def print_summary(results: list, meta_row: dict = None):
    """結果を整形して出力"""
    print("=" * 80)
    print("CSV Analysis Summary")
    print("=" * 80)
    
    if meta_row is not None:
        print("\nSession Information:")
        for key in ["session", "participant", "task", "phase"]:
            if key in meta_row and pd.notna(meta_row[key]):
                print(f"  {key}: {meta_row[key]}")
    
    print(f"\nTotal Blocks: {len(results)}")
    print("\n" + "=" * 80)
    print("Block-by-Block Statistics")
    print("=" * 80)
    
    for stats in results:
        print(f"\nBlock {stats['block_id']}:")
        print(f"  Duration: {stats['duration_min']:.2f} min ({stats['duration_sec']:.2f} sec)")
        print(f"  Frame Count: {stats['frame_count']}")
        print(f"  Concentration Score:")
        print(f"    Mean: {stats['concentration_mean']:.4f}")
        print(f"    Std:  {stats['concentration_std']:.4f}")
        print(f"    Min:  {stats['concentration_min']:.4f}")
        print(f"    Max:  {stats['concentration_max']:.4f}")
        print(f"    Median: {stats['concentration_median']:.4f}")
        print(f"  Blink Count: {stats['blink_count_max']} (final: {stats['blink_count_final']})")
        print(f"  Long Close Count: {stats['long_close_count']}")
        if not np.isnan(stats['ear_mean']):
            print(f"  EAR Mean: {stats['ear_mean']:.4f} (Std: {stats['ear_std']:.4f})")
        if not np.isnan(stats['gaze_offlvl_mean']):
            print(f"  Gaze Off Level Mean: {stats['gaze_offlvl_mean']:.4f} (Max: {stats['gaze_offlvl_max']:.4f})")
        print(f"  Alert Count: {stats['alert_count']}")
    
    # 全体統計
    if len(results) > 0:
        print("\n" + "=" * 80)
        print("Overall Statistics")
        print("=" * 80)
        total_duration = sum([r['duration_sec'] for r in results])
        total_blinks = sum([r['blink_count_max'] for r in results])
        total_long_close = sum([r['long_close_count'] for r in results])
        overall_concentration = np.mean([r['concentration_mean'] for r in results])
        
        print(f"Total Duration: {total_duration / 60.0:.2f} min ({total_duration:.2f} sec)")
        print(f"Total Blink Count: {total_blinks}")
        print(f"Total Long Close Count: {total_long_close}")
        print(f"Overall Concentration Mean: {overall_concentration:.4f}")


def save_csv(results: list, output_path: str):
    """結果をCSVファイルに保存"""
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze CSV log files")
    parser.add_argument("--csv", required=True, help="Path to CSV log file")
    parser.add_argument("--output", default=None, help="Output CSV file path (optional)")
    args = parser.parse_args()
    
    # ログファイルを読み込む
    frames, events, meta_row = load_log(args.csv)
    
    # ブロックごとに分析
    results = analyze_by_block(frames, events)
    
    # 結果を表示
    print_summary(results, meta_row)
    
    # CSVに保存（オプション）
    if args.output:
        save_csv(results, args.output)
    else:
        # デフォルトの出力ファイル名
        csv_path = Path(args.csv)
        output_path = csv_path.parent / f"{csv_path.stem}_analysis.csv"
        save_csv(results, str(output_path))


if __name__ == "__main__":
    main()

