@echo off
REM PC用の起動スクリプト（Windows）
REM 使い方: このファイルをダブルクリックするか、コマンドプロンプトから実行

cd /d "%~dp0\.."

REM 仮想環境が存在するか確認
if not exist "venv\Scripts\activate.bat" (
    echo 仮想環境が見つかりません。まず仮想環境を作成してください。
    echo python -m venv venv
    pause
    exit /b 1
)

REM 仮想環境を有効化
call venv\Scripts\activate.bat

REM ログディレクトリを作成
if not exist "logs" mkdir logs

REM タイムスタンプ付きログファイル名
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set mydate=%%c%%a%%b
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do set mytime=%%a%%b
set mytime=%mytime: =0%
set timestamp=%mydate%_%mytime%

REM アプリを起動（横長モード480x320で起動、Pi版と同じレイアウト）
python src/app.py --cam 0 --width 640 --height 480 --display-width 480 --display-height 320 --log logs\pc_%timestamp%.csv

pause

