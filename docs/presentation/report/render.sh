#!/usr/bin/env bash
# report.html을 장별 PNG와 PDF 하나로 내보낸다
set -euo pipefail
cd "$(dirname "$0")"
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
n=$(grep -c '<section class="slide' report.html)
rm -f slide-*.png
for i in $(seq 1 "$n"); do
  "$C" --headless=new --disable-gpu --hide-scrollbars --window-size=1920,1080 --virtual-time-budget=3000 --screenshot="$PWD/slide-$i.png" "file://$PWD/report.html#$i" 2>/dev/null
done
"$C" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=3000 --print-to-pdf="$PWD/결과보고서_05조_이선좌.pdf" "file://$PWD/report.html" 2>/dev/null
echo "slides: $n"
