@echo off
chcp 65001 >nul
echo ========================================
echo WohnungsScraper Portable - Build Script
echo Version 2.08 - Mit Chrome Portable
echo ========================================
echo.

REM Pruefe ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte installieren Sie Python 3.11+ von https://python.org
    pause
    exit /b 1
)

echo [1/9] Installiere benoetigte Pakete...
pip install pywebview pyinstaller beautifulsoup4 lxml pythonnet playwright nodriver curl_cffi

echo.
echo [2/9] Installiere Playwright Chromium Browser...
python -m playwright install chromium

echo.
echo [3/9] Kopiere Playwright Browser in lokalen Ordner...
rmdir /s /q playwright-browsers 2>nul
mkdir playwright-browsers

REM Kopiere den gesamten ms-playwright Ordner
echo Kopiere von %LOCALAPPDATA%\ms-playwright ...
xcopy "%LOCALAPPDATA%\ms-playwright" "playwright-browsers" /E /I /Y /Q

echo.
echo [4/9] Pruefe Browser-Installation...
dir playwright-browsers /s /b 2>nul | findstr chrome.exe
if errorlevel 1 (
    echo [WARNUNG] chrome.exe nicht gefunden in playwright-browsers!
)

echo.
echo ========================================
echo [5/9] Lade Chrome Portable herunter...
echo ========================================
echo.

REM Chrome Portable Download
set CHROME_URL=https://download3.portableapps.com/portableapps/GoogleChromePortable/GoogleChromePortable_131.0.6778.265_online.paf.exe
set CHROME_INSTALLER=ChromePortable_Installer.exe
set CHROME_DIR=chrome-portable

REM Loesche alten Chrome Portable Ordner
rmdir /s /q "%CHROME_DIR%" 2>nul

echo Lade Chrome Portable Installer herunter...
echo.

REM Download mit curl (primaer - funktioniert besser mit SSL)
curl -L -o "%CHROME_INSTALLER%" "%CHROME_URL%"

if not exist "%CHROME_INSTALLER%" (
    echo curl fehlgeschlagen, versuche PowerShell...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%CHROME_URL%', '%CHROME_INSTALLER%')"
)

if not exist "%CHROME_INSTALLER%" (
    echo PowerShell fehlgeschlagen, versuche certutil...
    certutil -urlcache -split -f "%CHROME_URL%" "%CHROME_INSTALLER%"
)

if exist "%CHROME_INSTALLER%" (
    echo.
    echo Chrome Portable Installer heruntergeladen.
    echo.
    echo ========================================
    echo WICHTIG: Chrome Portable Installation
    echo ========================================
    echo.
    echo Der Installer wird jetzt gestartet.
    echo Bitte waehlen Sie als Zielverzeichnis:
    echo   %CD%\%CHROME_DIR%
    echo.
    echo Druecken Sie eine Taste um fortzufahren...
    pause >nul
    
    REM Starte den Installer
    start /wait "" "%CHROME_INSTALLER%" /DESTINATION="%CD%\%CHROME_DIR%"
    
    REM Warte kurz
    timeout /t 3 /nobreak >nul
    
    REM Pruefe ob Installation erfolgreich war
    if exist "%CHROME_DIR%\App\Chrome-bin\chrome.exe" (
        echo.
        echo [OK] Chrome Portable erfolgreich installiert!
    ) else if exist "%CHROME_DIR%\GoogleChromePortable.exe" (
        echo.
        echo [OK] Chrome Portable installiert (alternative Struktur)
    ) else (
        echo.
        echo [WARNUNG] Chrome Portable Installation moeglicherweise fehlgeschlagen.
        echo Bitte manuell pruefen: %CHROME_DIR%
    )
    
    REM Loesche Installer
    del "%CHROME_INSTALLER%" 2>nul
) else (
    echo.
    echo [WARNUNG] Chrome Portable konnte nicht heruntergeladen werden.
    echo ImmoScout24 wird ohne Chrome Portable moeglicherweise blockiert.
    echo.
    echo Sie koennen Chrome Portable manuell herunterladen von:
    echo https://portableapps.com/apps/internet/google_chrome_portable
    echo.
    echo Und den Ordner "chrome-portable" neben der .exe ablegen.
)

echo.
echo [6/9] Entferne alte Build-Dateien...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del WohnungsScraper.spec 2>nul

echo.
echo [7/9] Erstelle portable .exe...

python -m PyInstaller ^
    --onedir ^
    --windowed ^
    --clean ^
    --noupx ^
    --name WohnungsScraper ^
    --add-data "playwright-browsers;playwright-browsers" ^
    --add-data "src/ui/templates;src/ui/templates" ^
    --add-data "src/ui/static;src/ui/static" ^
    --add-data "src/api;src/api" ^
    --add-data "src/database;src/database" ^
    --add-data "src/scraper;src/scraper" ^
    --add-data "src/__init__.py;src" ^
    --hidden-import=src.api.api ^
    --hidden-import=src.database.db ^
    --hidden-import=src.scraper.scraper ^
    --hidden-import=src.scraper.normalizer ^
    --hidden-import=src.scraper.base ^
    --hidden-import=src.scraper.wg_gesucht ^
    --hidden-import=src.scraper.immoscout ^
    --hidden-import=src.scraper.immowelt ^
    --hidden-import=src.scraper.kleinanzeigen ^
    --hidden-import=src.scraper.scrapeops_scraper ^
    --hidden-import=src.scraper.scrapfly_scraper ^
    --hidden-import=nodriver ^
    --hidden-import=curl_cffi ^
    --hidden-import=requests ^
    --exclude-module=tkinter ^
    wohnungsscraper.py

echo.
echo [8/9] Kopiere Chrome Portable...

if exist "%CHROME_DIR%" (
    echo Kopiere Chrome Portable...
    xcopy "%CHROME_DIR%" "dist\WohnungsScraper\chrome-portable" /E /I /Y /Q
    echo [OK] Chrome Portable kopiert
) else (
    echo [INFO] Chrome Portable nicht vorhanden - wird uebersprungen
)

echo.
echo [9/9] Erstelle data Ordner und raeume auf...
mkdir "dist\WohnungsScraper\data" 2>nul
rmdir /s /q build 2>nul
del WohnungsScraper.spec 2>nul

echo.
echo ========================================
echo FERTIG!
echo ========================================
echo.
echo Die portable Version befindet sich in:
echo   dist\WohnungsScraper\WohnungsScraper.exe
echo.

REM Zeige Inhalt des dist Ordners
echo Inhalt:
dir dist\WohnungsScraper /b
echo.

REM Zeige Groesse
echo Groesse:
dir dist\WohnungsScraper /s | findstr "Datei(en)"
echo.

if exist "dist\WohnungsScraper\chrome-portable" (
    echo [OK] Chrome Portable ist enthalten
    echo     ImmoScout24 sollte funktionieren!
) else (
    echo [INFO] Chrome Portable ist NICHT enthalten
    echo     ImmoScout24 wird moeglicherweise blockiert
)

echo.
echo Den gesamten "WohnungsScraper" Ordner koennen Sie
echo auf einen USB-Stick kopieren.
echo.
pause
