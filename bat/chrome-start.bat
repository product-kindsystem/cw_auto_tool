@echo off

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
  echo "64bit�t�@�C�������݂��Ă��܂��B"
  "C:\Program Files\Google\Chrome\Application\chrome.exe" --profile-directory="Profile 17" --remote-debugging-port=9222 --start-maximized
) else (
  echo "32bit�t�@�C�������݂��Ă��܂��B"
  "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --profile-directory="Profile 17" --remote-debugging-port=9222 --start-maximized
)

