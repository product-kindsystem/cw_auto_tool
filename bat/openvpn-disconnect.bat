@echo off
REM "C:\Program Files\OpenVPN\bin\openvpn-gui.exe" --command disconnect_all => Failure

tasklist /FI "IMAGENAME eq openvpn.exe" 2>NUL | find /I /N "openvpn.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo OpenVPN is running. Terminating the process...
    taskkill /F /IM openvpn.exe
    REM timeout /t 2 /nobreak
    echo OpenVPN process terminated.
) else (
    echo OpenVPN is not running.
)


tasklist /FI "IMAGENAME eq openvpn-gui.exe" 2>NUL | find /I /N "openvpn-gui.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo OpenVPN-GUI is running. Terminating the process...
    taskkill /F /IM openvpn-gui.exe
    REM timeout /t 2 /nobreak
    echo OpenVPN-GUI process terminated.
) else (
    echo OpenVPN-GUI is not running.
)