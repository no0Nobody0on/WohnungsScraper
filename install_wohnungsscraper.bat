@echo off
title WohnungsScraper Installer v2.08

echo.
echo ========================================================
echo        WohnungsScraper - Automatischer Installer
echo                     Version 2.08
echo ========================================================
echo.

:: Installation im aktuellen Verzeichnis (wo die BAT liegt)
set "CURRENT_DIR=%~dp0"
set "FINAL_DIR=%CURRENT_DIR%WohnungsScraper"
set "TEMP_DIR=%TEMP%\WSInstall"
set "ZIP_URL=https://github.com/no0Nobody0on/WohnungsScraper/archive/refs/heads/main.zip"
set "ZIP_FILE=%TEMP_DIR%\main.zip"

:: Temp Ordner erstellen
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

echo Installationsort: %FINAL_DIR%
echo.

:: -----------------------------------------------------------
:: SCHRITT 1: Python pruefen
:: -----------------------------------------------------------
echo [1/5] Pruefe Python...

python --version >nul 2>&1
if %ERRORLEVEL%==0 (
    echo       [OK] Python gefunden.
    goto DOWNLOAD
)

echo       Python nicht gefunden - installiere...

:: Winget versuchen
winget --version >nul 2>&1
if %ERRORLEVEL%==0 (
    echo       Nutze winget...
    winget install --id Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements
    echo.
    echo       [!] Python wurde installiert.
    echo       [!] Bitte SCHLIESSE dieses Fenster und starte den Installer NEU!
    echo.
    pause
    exit /b 0
)

:: Manueller Python Download mit curl
echo       Lade Python mit curl...
curl -L -o "%TEMP_DIR%\python_setup.exe" "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"

if exist "%TEMP_DIR%\python_setup.exe" (
    echo       Installiere Python...
    "%TEMP_DIR%\python_setup.exe" /quiet InstallAllUsers=0 PrependPath=1
    echo.
    echo       [!] Python wurde installiert.
    echo       [!] Bitte SCHLIESSE dieses Fenster und starte den Installer NEU!
    echo.
    pause
    exit /b 0
)

echo       [FEHLER] Python konnte nicht installiert werden.
echo       Bitte manuell installieren: https://www.python.org/downloads/
pause
exit /b 1

:: -----------------------------------------------------------
:: SCHRITT 2: ZIP herunterladen
:: -----------------------------------------------------------
:DOWNLOAD
echo.
echo [2/5] Lade WohnungsScraper herunter...

:: Loesche alte ZIP falls vorhanden
if exist "%ZIP_FILE%" del "%ZIP_FILE%"

:: Download mit curl
echo       Download laeuft...
curl -L -o "%ZIP_FILE%" "%ZIP_URL%" 2>nul

if not exist "%ZIP_FILE%" (
    :: Fallback: PowerShell
    echo       Versuche PowerShell...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%ZIP_URL%', '%ZIP_FILE%')"
)

if not exist "%ZIP_FILE%" (
    echo       [FEHLER] Download fehlgeschlagen!
    pause
    exit /b 1
)

echo       [OK] Download erfolgreich.

:: -----------------------------------------------------------
:: SCHRITT 3: ZIP entpacken
:: -----------------------------------------------------------
echo.
echo [3/5] Entpacke Dateien...

:: Loesche altes extracted falls vorhanden
rmdir /s /q "%TEMP_DIR%\extracted" 2>nul

:: Entpacke in Temp
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%TEMP_DIR%\extracted' -Force"

:: Finde den Build-Ordner (suche nach build_windows.bat)
set "BUILD_DIR="

:: Suche in allen Unterordnern nach build_windows.bat
for /f "delims=" %%F in ('dir /s /b "%TEMP_DIR%\extracted\build_windows.bat" 2^>nul') do (
    set "BUILD_DIR=%%~dpF"
)

if not defined BUILD_DIR (
    echo       [FEHLER] build_windows.bat nicht gefunden!
    echo.
    echo       Inhalt von extracted:
    dir /s /b "%TEMP_DIR%\extracted" 2>nul
    pause
    exit /b 1
)

echo       [OK] Build-Ordner: %BUILD_DIR%

:: -----------------------------------------------------------
:: SCHRITT 4: Build ausfuehren
:: -----------------------------------------------------------
echo.
echo [4/5] Erstelle EXE...
echo       (Das kann einige Minuten dauern)
echo.

cd /d "%BUILD_DIR%"
call build_windows.bat

:: Pruefe ob dist\WohnungsScraper erstellt wurde
if not exist "dist\WohnungsScraper\WohnungsScraper.exe" (
    echo       [FEHLER] Build fehlgeschlagen - EXE nicht gefunden!
    echo.
    echo       Inhalt von dist:
    dir /s /b "dist" 2>nul
    pause
    exit /b 1
)

echo.
echo       [OK] Build erfolgreich!

:: -----------------------------------------------------------
:: SCHRITT 5: Finalen Ordner erstellen (sauber)
:: -----------------------------------------------------------
echo.
echo [5/5] Erstelle finalen Ordner...

:: Loesche alten Zielordner falls vorhanden
if exist "%FINAL_DIR%" (
    echo       Entferne alte Installation...
    rmdir /s /q "%FINAL_DIR%" 2>nul
    timeout /t 2 /nobreak >nul
)

:: WICHTIG: Verschiebe den kompletten dist\WohnungsScraper Ordner
:: (nicht kopieren - verschieben ist zuverlaessiger)
echo       Verschiebe Dateien...
move "dist\WohnungsScraper" "%FINAL_DIR%"

:: Falls move fehlschlaegt, nutze robocopy
if not exist "%FINAL_DIR%\WohnungsScraper.exe" (
    echo       Move fehlgeschlagen, nutze robocopy...
    robocopy "dist\WohnungsScraper" "%FINAL_DIR%" /E /MOVE /NFL /NDL /NJH /NJS
)

:: Falls robocopy nicht verfuegbar, nutze xcopy
if not exist "%FINAL_DIR%\WohnungsScraper.exe" (
    echo       Robocopy fehlgeschlagen, nutze xcopy...
    xcopy "dist\WohnungsScraper\*.*" "%FINAL_DIR%\" /E /I /Y /H
)

:: Erstelle data Ordner falls nicht vorhanden
if not exist "%FINAL_DIR%\data" mkdir "%FINAL_DIR%\data"

:: Pruefe ob Installation erfolgreich
if not exist "%FINAL_DIR%\WohnungsScraper.exe" (
    echo       [FEHLER] Installation fehlgeschlagen!
    echo       Die EXE wurde nicht korrekt kopiert.
    echo.
    echo       Bitte manuell kopieren von:
    echo       %BUILD_DIR%dist\WohnungsScraper
    echo.
    pause
    exit /b 1
)

:: Loesche temporaere Dateien
echo       Raeume auf...
cd /d "%CURRENT_DIR%"
rmdir /s /q "%TEMP_DIR%" 2>nul

echo       [OK] Fertig!

:: -----------------------------------------------------------
:: FERTIG
:: -----------------------------------------------------------
echo.
echo ========================================================
echo              Installation abgeschlossen!
echo ========================================================
echo.
echo   Ordner: %FINAL_DIR%
echo.
echo   Inhalt:
dir /b "%FINAL_DIR%"
echo.
echo   Starte das Programm mit WohnungsScraper.exe
echo.
echo ========================================================

:: Oeffne den finalen Ordner
start "" explorer "%FINAL_DIR%"

echo.
pause
