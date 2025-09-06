@echo off

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
  echo "64bitファイルが存在しています。"
  "C:\Program Files\Google\Chrome\Application\chrome.exe" --profile-directory="Profile 17" --remote-debugging-port=9222 --start-maximized
) else (
  echo "32bitファイルが存在しています。"
  "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --profile-directory="Profile 17" --remote-debugging-port=9222 --start-maximized
)

