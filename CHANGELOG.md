# CHANGELOG

All notable changes to this project will be documented in this file.

## 2025-11-24
- Add project scaffold (src/, scripts/, notebooks/), Windows prototype.
- Implement MediaPipe FaceMesh + Iris wrapper.
- Implement blink detection via EAR with EWMA open-eye baseline and relative threshold; proper blink counting and long-close detection.
- Implement gaze estimator with iris-based horizontal offset, smoothing, calibration bias, and off-level EMA.
- Implement fusion scorer (long-close emphasis + gaze off-level) with alert threshold and cooldown.
- Implement overlay with detailed status (Face/Iris, EAR baseline/threshold, blink stats, gaze bias/threshold/off-level, FPS, risk).
- Implement CSV logger with frame and event rows, plus meta (session/participant/task/phase/block_id).
- Implement main app with CLI: cam/size/display, logging, experiment metadata, train/eval phases, calibration seconds, model save/load, hotkeys (s/e/m/d/c/q).
- Add safety-guarded personalization: skip learning when face-missing/closed/off/alert; require consecutive stable frames; asymmetric EWMA; train-only.
- Session-bound persistence: apply models only on load at session start; save only at session end; disable blink baseline adaptation in eval.
- Analysis notebook (notebooks/analysis.ipynb): load logs, build timelines, plots, confusion/F1/AUC, detection delay.
- Requirements updated for analysis (pandas, seaborn, scikit-learn, matplotlib).

## 2025-11-10
- Initial prototype iteration: base blink/gaze logic, overlay panel, basic fusion and alert, logging v1.

## 2025-11-03
- Planning: pipeline design, feature list, Windows-first approach; decided not to use Coral USB Accelerator initially.


# Conventions
- Versioning by date; semantic tags can be added later if packaging.
- Each entry should specify: change summary, purpose, affected modules.

# How to add a new entry
1) Add a new date heading.
2) Bullet the changes with purpose and files touched.
3) If changing behavior, note migration notes (CLI flags, defaults).
