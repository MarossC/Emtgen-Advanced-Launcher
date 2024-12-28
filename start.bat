@echo off
cd "%~dp0"

echo Checking if python is installed
where python >nul 2>&1
if %errorlevel%==0 (
    echo Python is already installed
) else (
    echo Installing python 3.12.3...
    PowerShell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile 'python-3.12.3-amd64.exe'"
    start /wait python-3.12.3-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-3.12.3-amd64.exe
    echo Python 3.12.3 installed
)
echo Checking dependencies...
powershell -Command ^
  "$apiUrl = 'https://api.github.com/repos/Smety2001/Stellaria-Advanced-Launcher/contents/requirements.txt?ref=main';" ^
  "$timestamp = Get-Date -Format 'yyyyMMddHHmmss';$uniqueUrl = $apiUrl + '&timestamp=' + $timestamp;" ^
  "$headers = @{ 'Cache-Control' = 'no-cache' };" ^
  "$response = Invoke-RestMethod -Uri $uniqueUrl -Headers $headers;" ^
  "$content = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($response.content));" ^
  "$lib = $content -split '\n' | Where-Object { $_ -ne '' } | ForEach-Object { $_.Trim() };" ^
  "& pip install $lib"
echo Dependencies checked

rem echo Updating stellaria advanced launcher...
rem powershell -Command ^
rem   "$apiUrl = 'https://api.github.com/repos/Smety2001/Stellaria-Advanced-Launcher/contents/main.py?ref=main';" ^
rem   "$timestamp = Get-Date -Format 'yyyyMMddHHmmss';" ^
rem   "$uniqueUrl = $apiUrl + '&timestamp=' + $timestamp;" ^
rem   "$headers = @{ 'Cache-Control' = 'no-cache' };" ^
rem   "$response = Invoke-RestMethod -Uri $uniqueUrl -Headers $headers;" ^
rem   "$content = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($response.content));" ^
rem   "$filePath = '%~dp0' + $response.name;" ^
rem   "Set-Content -Path $filePath -Value $content -Encoding utf8"
rem echo Stellaria advanced launcher updated

echo Starting stellaria advanced launcher...
start python main.py
echo Stellaria advanced launcher started
pause