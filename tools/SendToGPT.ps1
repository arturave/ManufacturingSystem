# tools/ai/SendToGPT.ps1
param(
  [Parameter(Mandatory=$false)][string]$Path,
  [string]$Prompt = "Review and refactor this code for clarity, performance and testability. Add Google-style docstrings and type hints where reasonable."
)

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

# Jeśli uruchomione z VS External Tools – makro $(ItemPath) zwykle zadziała.
# W terminalu: jeśli brak -Path, bierzemy aktualny plik zaznaczony w git (lub wyjdziemy z błędem).
if (-not $Path) {
  $staged = git diff --name-only --cached 2>$null
  if ($staged) {
    $first = ($staged | Select-Object -First 1)
    $Path = Join-Path (Get-SolutionRoot) $first
  } else {
    Write-Error "Nie podano -Path i brak plików w stage. Uruchom z VS lub wskaż plik: -Path .\mfg_app.py"
  }
}

$full = Resolve-Path $Path
if (-not (Test-Path $full)) { Write-Error "File not found: $full"; exit 1 }

# ostrzeż przed wysyłką .env
if ($full.Path -like "*.env" -or $full.Path -like "*.pem") {
  Write-Warning "Wygląda na plik z sekretami (.env/.pem). Przerwano."
  exit 1
}

# wczytaj kod (UTF-8 jako domyślne)
$content = Get-Content -LiteralPath $full -Raw -Encoding UTF8
# proste escapowanie backticków i cudzysłowów
$content = $content -replace '`', '``' -replace '"','\"'

$header = "### Project: ManufacturingSystem  ·  File: $([System.IO.Path]::GetFileName($full))"
$payload = "$header`n`n$Prompt`n`n```$([System.IO.Path]::GetFileName($full))`n$content`n```"

Set-Clipboard -Value $payload
Start-Process "https://chat.openai.com/?model=gpt-5"
Write-Host "✅ Skopiowano do schowka i otwarto ChatGPT. Wklej (Ctrl+V) w czacie."
