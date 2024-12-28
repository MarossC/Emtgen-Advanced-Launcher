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
  "$apiUrl = 'https://api.github.com/repos/MarossC/Emtgen-Advanced-Launcher/contents/requirements.txt?ref=main';" ^
  "$timestamp = Get-Date -Format 'yyyyMMddHHmmss';$uniqueUrl = $apiUrl + '&timestamp=' + $timestamp;" ^
  "$headers = @{ 'Cache-Control' = 'no-cache' };" ^
  "$response = Invoke-RestMethod -Uri $uniqueUrl -Headers $headers;" ^
  "$content = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($response.content));" ^
  "$lib = $content -split '\n' | Where-Object { $_ -ne '' } | ForEach-Object { $_.Trim() };" ^
  "& pip install $lib"
echo Dependencies checked

echo Updating Emtgen advanced launcher...
powershell -Command ^
  "$apiUrl = 'https://api.github.com/repos/MarossC/Emtgen-Advanced-Launcher/contents/main.py?ref=main';" ^
  "$timestamp = Get-Date -Format 'yyyyMMddHHmmss';" ^
  "$uniqueUrl = $apiUrl + '&timestamp=' + $timestamp;" ^
  "$headers = @{ 'Cache-Control' = 'no-cache' };" ^
  "$response = Invoke-RestMethod -Uri $uniqueUrl -Headers $headers;" ^
  "$content = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($response.content));" ^
  "$filePath = '%~dp0' + $response.name;" ^
  "Set-Content -Path $filePath -Value $content -Encoding utf8"
echo Emtgen advanced launcher updated

echo Starting Emtgen advanced launcher...
start python main.py
echo Emtgen advanced launcher started
