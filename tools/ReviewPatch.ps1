# tools/ai/ReviewPatch.ps1
param([Parameter(Mandatory=$true)][string]$File)

$ErrorActionPreference = "Stop"

function Get-SolutionRoot {
  param([string]$Start = (Get-Location).Path)
  $dir = Get-Item -Path $Start
  while ($null -ne $dir) {
    $sln = Get-ChildItem -Path $dir.FullName -Filter *.sln -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($sln) { return $dir.FullName }
    $dir = $dir.Parent
  }
  return (Get-Location).Path
}

$root = Get-SolutionRoot
$full = Resolve-Path $File
if (-not (Test-Path $full)) { Write-Error "Plik nie istnieje: $File"; exit 1 }

$content = Get-Content -LiteralPath $full -Raw -Encoding UTF8
$content = $content -replace '`','``' -replace '"','\"'

$rel = (Resolve-Path -Relative $full) -replace '^\.\.\\',''
$prompt = @"
Przeanalizuj i zaproponuj minimalny patch (unified diff) poprawiający:
- czytelność, typy, docstringi Google-style
- błędy oczywiste (np. wyjątki, brak walidacji)
- brakujące testy – tylko TODO w komentarzu
Zwróć TYLKO diff (bez opisu).
"@

$payload = "$prompt`n`n--- a/$rel`n+++ b/$rel`n```$([System.IO.Path]::GetFileName($full))`n$content`n```"
Set-Clipboard -Value $payload
Start-Process "https://chat.openai.com/?model=gpt-5"
Write-Host "✅ Kod skopiowany do schowka. Wklej w ChatGPT – dostaniesz unified diff."
