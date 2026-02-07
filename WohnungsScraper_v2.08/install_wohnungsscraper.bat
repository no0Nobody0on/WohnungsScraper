@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title WohnungsScraper Installer

echo.
echo ══════════════════════════════════════════════════════════════
echo            WohnungsScraper - Automatischer Installer
echo                       Version 2.08
echo ══════════════════════════════════════════════════════════════
echo.

:: Temp-Verzeichnis für Downloads
set "TEMP_DIR=%TEMP%\WohnungsScraperInstall"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: ═══════════════════════════════════════════════════════════════
:: SCHRITT 1: Prüfe und installiere Git
:: ═══════════════════════════════════════════════════════════════
echo [1/5] Pruefe Git Installation...

git --version >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo       [OK] Git ist bereits installiert.
    goto :check_python
)

echo       Git nicht gefunden - wird installiert...
echo.

:: Prüfe ob winget verfügbar ist
winget --version >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo       Installiere Git via winget...
    winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements
    if !ERRORLEVEL! EQU 0 (
        echo       [OK] Git erfolgreich installiert!
        set "PATH=!PATH!;C:\Program Files\Git\bin;C:\Program Files\Git\cmd"
        goto :check_python
    )
)

:: Fallback: Manueller Download
echo       Lade Git herunter (ca. 50 MB)...
set "GIT_URL=https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
set "GIT_INSTALLER=%TEMP_DIR%\git_installer.exe"

powershell -Command "Invoke-WebRequest -Uri '%GIT_URL%' -OutFile '%GIT_INSTALLER%'" 2>nul

if not exist "%GIT_INSTALLER%" (
    echo       [FEHLER] Git Download fehlgeschlagen!
    echo       Bitte manuell installieren: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo       Installiere Git (bitte warten)...
"%GIT_INSTALLER%" /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"

set "PATH=!PATH!;C:\Program Files\Git\bin;C:\Program Files\Git\cmd"
echo       [OK] Git installiert!

:: ═══════════════════════════════════════════════════════════════
:: SCHRITT 2: Prüfe und installiere Python
:: ═══════════════════════════════════════════════════════════════
:check_python
echo.
echo [2/5] Pruefe Python Installation...

python --version >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo       [OK] Python ist bereits installiert.
    goto :verify_install
)

echo       Python nicht gefunden - wird installiert...
echo.

:: Prüfe ob winget verfügbar ist
winget --version >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo       Installiere Python via winget...
    winget install --id Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements
    if !ERRORLEVEL! EQU 0 (
        echo       [OK] Python erfolgreich installiert!
        set "PATH=!PATH!;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
        goto :verify_install
    )
)

:: Fallback: Manueller Download
echo       Lade Python herunter (ca. 25 MB)...
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
set "PYTHON_INSTALLER=%TEMP_DIR%\python_installer.exe"

powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'" 2>nul

if not exist "%PYTHON_INSTALLER%" (
    echo       [FEHLER] Python Download fehlgeschlagen!
    echo       Bitte manuell installieren: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo       Installiere Python (bitte warten)...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

set "PATH=!PATH!;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
echo       [OK] Python installiert!

:: Warte kurz
timeout /t 3 /nobreak >nul

:: ═══════════════════════════════════════════════════════════════
:: SCHRITT 3: Verifiziere Installationen
:: ═══════════════════════════════════════════════════════════════
:verify_install
echo.
echo [3/5] Verifiziere Installationen...

:: Aktualisiere PATH mit bekannten Pfaden
set "PATH=!PATH!;C:\Program Files\Git\bin;C:\Program Files\Git\cmd"
set "PATH=!PATH!;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
set "PATH=!PATH!;C:\Python311;C:\Python311\Scripts"

:: Teste Git
git --version >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo       [WARNUNG] Git nicht im PATH - versuche direkten Pfad...
    if exist "C:\Program Files\Git\cmd\git.exe" (
        set "GIT_CMD=C:\Program Files\Git\cmd\git.exe"
    ) else (
        echo       [FEHLER] Git nicht gefunden!
        echo       Bitte starte den Computer neu und fuehre den Installer erneut aus.
        pause
        exit /b 1
    )
) else (
    set "GIT_CMD=git"
)

:: Teste Python
python --version >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo       [WARNUNG] Python nicht im PATH - versuche direkten Pfad...
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else if exist "C:\Python311\python.exe" (
        set "PYTHON_CMD=C:\Python311\python.exe"
    ) else (
        echo       [FEHLER] Python nicht gefunden!
        echo       Bitte starte den Computer neu und fuehre den Installer erneut aus.
        pause
        exit /b 1
    )
) else (
    set "PYTHON_CMD=python"
)

echo       [OK] Alle Abhaengigkeiten vorhanden.

:: ═══════════════════════════════════════════════════════════════
:: SCHRITT 4: Repository klonen oder aktualisieren
:: ═══════════════════════════════════════════════════════════════
echo.
set "INSTALL_DIR=%USERPROFILE%\WohnungsScraper"
echo [4/5] Zielverzeichnis: %INSTALL_DIR%

:: Falls Verzeichnis existiert, aktualisieren
if exist "%INSTALL_DIR%" (
    echo       Verzeichnis existiert - aktualisiere...
    cd /d "%INSTALL_DIR%"
    
    !GIT_CMD! pull origin main 2>nul
    if !ERRORLEVEL! EQU 0 (
        echo       [OK] Repository aktualisiert.
        goto :start_build
    ) else (
        echo       Aktualisierung fehlgeschlagen - loesche und klone neu...
        cd /d "%USERPROFILE%"
        rmdir /s /q "%INSTALL_DIR%" 2>nul
    )
)

echo       Klone Repository von GitHub...
!GIT_CMD! clone https://github.com/no0Nobody0on/WohnungsScraper.git "%INSTALL_DIR%"

if !ERRORLEVEL! NEQ 0 (
    echo       [FEHLER] Git Clone fehlgeschlagen!
    echo       Bitte pruefen Sie Ihre Internetverbindung.
    pause
    exit /b 1
)

echo       [OK] Repository geklont.

:: ═══════════════════════════════════════════════════════════════
:: SCHRITT 5: Build starten
:: ═══════════════════════════════════════════════════════════════
:start_build
echo.
echo [5/5] Starte Build-Prozess...
echo.

cd /d "%INSTALL_DIR%"

:: Finde build_windows.bat
if exist "build_windows.bat" (
    call build_windows.bat
) else if exist "portable_app\build_windows.bat" (
    cd portable_app
    call build_windows.bat
) else (
    echo       [FEHLER] build_windows.bat nicht gefunden!
    pause
    exit /b 1
)

:: ═══════════════════════════════════════════════════════════════
:: FERTIG
:: ═══════════════════════════════════════════════════════════════
echo.
echo ══════════════════════════════════════════════════════════════
echo                    Installation erfolgreich!
echo ══════════════════════════════════════════════════════════════
echo.
echo   Installationsort: %INSTALL_DIR%
echo   Die EXE-Datei befindet sich im "dist" Ordner.
echo.
echo ══════════════════════════════════════════════════════════════

:: Aufräumen
rmdir /s /q "%TEMP_DIR%" 2>nul

:: Öffne den dist Ordner
if exist "dist" (
    start "" explorer "dist"
)

echo.
echo Druecke eine Taste zum Beenden...
pause >nul
