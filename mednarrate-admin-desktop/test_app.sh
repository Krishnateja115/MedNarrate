#!/bin/bash
open "src-tauri/target/release/bundle/macos/MedNarrate Admin.app"
sleep 5
screencapture -x screenshot.png
killall "MedNarrate Admin" || killall mednarrate-admin-desktop
