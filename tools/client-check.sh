#!/bin/bash
# Start the real game client, wait until it reaches the main menu, quit it and scan
# the client log. Catches runtime problems (missing images, animations) that the
# dummy server run in check.sh can't see.
# Usage: tools/client-check.sh [seconds-to-stay-in-menu]
LOG="$HOME/Library/Logs/vcmi/VCMI_Client_log.txt"
STAY=${1:-3}
/Applications/VCMI.app/Contents/MacOS/vcmiclient -i --disable-video > /dev/null 2>&1 &
PID=$!; disown $PID
for i in $(seq 1 60); do
  sleep 1
  grep -q "Loading music file Music/MainMenu" "$LOG" 2>/dev/null && break
done
sleep "$STAY"
kill $PID 2>/dev/null; sleep 1; kill -9 $PID 2>/dev/null
pkill -f "vcmiserver --run-by-client" 2>/dev/null
grep -q "Loading music file Music/MainMenu" "$LOG" || { echo "client never reached the main menu (waited ${i}s)"; exit 1; }
grep -q "Loading mod: OK (naruto-heroes)" "$LOG" || { echo "naruto-heroes not loaded"; exit 1; }
hits=$(grep -E "\] (ERROR|WARN) " "$LOG" | grep -vE "Potential confict detected .*add file '[^']*/'$" \
  | grep -vE "Potential confict detected between '(hd-remastered|russian-translation|vcmi-extras[^']*)' and '(hd-remastered|russian-translation|vcmi-extras[^']*)'")
[ -n "$hits" ] && { echo "$hits"; exit 1; }
echo "OK: client reached the main menu in ${i}s with no errors or warnings"
