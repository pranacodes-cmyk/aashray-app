set -euo pipefail
mkdir -p smoke
adb install -r yeshu_app/build/app/outputs/flutter-apk/app-release.apk
for mode in fresh cold cleared; do
  adb shell am force-stop com.aashray.faith
  if [ "$mode" = cleared ]; then adb shell pm clear com.aashray.faith; fi
  adb logcat -c
  adb shell am start -n com.aashray.faith/.MainActivity
  for attempt in $(seq 1 30); do
    adb shell uiautomator dump /sdcard/window.xml >/dev/null 2>&1 || true
    adb pull /sdcard/window.xml smoke/$mode.xml >/dev/null 2>&1 || true
    if grep -q 'Unlock Premium' smoke/$mode.xml; then break; fi
    sleep 2
  done
  grep -q 'Unlock Premium' smoke/$mode.xml
  if grep -q 'Preview app' smoke/$mode.xml; then echo 'Test access unexpectedly enabled'; exit 1; fi
  adb shell screencap -p /sdcard/start.png
  adb pull /sdcard/start.png smoke/$mode.png
  adb logcat -d > smoke/$mode.log
  if grep -q 'FATAL EXCEPTION' smoke/$mode.log; then echo 'Native startup crash'; exit 1; fi
done