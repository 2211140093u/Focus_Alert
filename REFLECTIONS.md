# REFLECTIONS (Feedback, Mistakes, and Prevention)

This document records issues encountered, feedback received, and concrete actions to prevent recurrence.

## 1) Directory creation on save/load
- Issue: Model save/load failed when parent folders didn't exist (e.g., `models/P01.json`).
- Fix: `personalize.save()` now creates parent directory before writing.
- Prevention: Always ensure write paths create parents; add unit tests or try/except with mkdir.

## 2) Initial detection sensitivity too low
- Issue: Blink count not increasing; gaze responsiveness low; unclear detection status.
- Fix: EWMA open-eye baseline, relative EAR threshold, blink counted on closed->open; gaze threshold lowered, calibration bias, off-level EMA; overlay enriched.
- Prevention: Start with adaptive thresholds + live diagnostics; include calibration key; expose thresholds on UI.

## 3) Drift during online use
- Issue: Unlabeled usage risks baseline drifting toward fatigued state.
- Fix: Safety-guarded learning (skip on closed/off/alert/no-face, stable frames, asymmetric EWMA), eval phase to freeze; session-bound persistence.
- Prevention: Default to guarded train, fixed eval; require explicit session-end save; consider periodic validation tasks.

## 4) Evaluation visibility
- Issue: 難しかった: アラート妥当性や検出遅延の客観評価。
- Fix: CSV schema拡張（meta/frames/events）、ホットキー（s/e/m/d/c/q）、分析ノートブックで混同行列/AUC/遅延を算出。
- Prevention: 実験設計の標準手順をプロジェクトに同梱（手順書, ノートブック）。

## 5) User guidance
- Issue: 使い方やショートカットの意図が分かりづらい。
- Fix: READMEを詳細化、UIに検出状態と閾値を可視化、ショートカットの説明を提供。
- Prevention: 新機能追加時にREADMEとCHANGELOGを同時更新。チュートリアルを用意。

## 6) Session-bound adaptation clarity
- Issue: セッション中に基準が変わると評価が難しい。
- Fix: eval中は完全固定、trainのみ学習、保存はセッション終了時のみ。blink側にもadaptフラグ追加。
- Prevention: 仕様として明文化（この文書とREADME/CHANGELOGに追記）。

## 7) Future work reminders
- Add CLI flags to tune safety params (stable_frames_req, ear_alpha_up/down, gaze_alpha).
- Option: allow save-on-block-end (eイベント) with explicit flag.
- Add analysis notebook cells for task-score onsets (CPT/RT based) and exportable reports.
