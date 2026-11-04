set -uo pipefail
mkdir -p smoke
adb install -r yeshu_app/build/app/outputs/flutter-apk/app-release.apk || exit 1
fail() {
  echo "SMOKE FAILED ($1): $2"
  adb shell screencap -p /sdcard/fail.png; adb pull /sdcard/fail.png "smoke/$1-fail.png" >/dev/null 2>&1
  adb logcat -d > "smoke/$1.log"
  grep -E "AASHRAY_STARTUP_ERROR|flutter|FATAL|AndroidRuntime|Exception" "smoke/$1.log" | tail -80
  exit 1
}
for mode in fresh cold cleared; do
  adb shell am force-stop com.aashray.faith
  if [ "$mode" = cleared ]; then adb shell pm clear com.aashray.faith; fi
  adb logcat -c
  adb shell am start -n com.aashray.faith/.MainActivity
  for attempt in $(seq 1 30); do
    adb shell uiautomator dump /sdcard/window.xml >/dev/null 2>&1 || true
    adb pull /sdcard/window.xml smoke/$mode.xml >/dev/null 2>&1 || true
    if grep -q 'Unlock Premium' smoke/$mode.xml 2>/dev/null; then break; fi
    if grep -q 'Something went wrong while opening' smoke/$mode.xml 2>/dev/null; then fail "$mode" "startup error screen"; fi
    sleep 2
  done
  grep -q 'Unlock Premium' smoke/$mode.xml || fail "$mode" "paywall not shown"
  if grep -q 'Preview app' smoke/$mode.xml; then fail "$mode" "test access unexpectedly enabled"; fi
  adb shell screencap -p /sdcard/start.png
  adb pull /sdcard/start.png smoke/$mode.png
  adb logcat -d > smoke/$mode.log
  if grep -q 'FATAL EXCEPTION' smoke/$mode.log; then fail "$mode" "native startup crash"; fi
done
echo "SMOKE PASSED"
