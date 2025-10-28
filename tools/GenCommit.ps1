# tools/ai/GenCommit.ps1
param([string]$Scope = ".")

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
$diff = git -C $root diff --cached
if (-not $diff) { Write-Error "Brak zmian w stage (git add .)."; exit 1 }

$prompt = @"
Napisz zwięzły conventional commit po polsku:
- nagłówek do 72 znaków, tryb rozkazujący
- w treści wypunktuj kluczowe zmiany
- jeśli dotyczy testów/migracji DB – wspomnij
Zwróć TYLKO gotowy tekst commitu.
"@

$payload = "$prompt`n`n$diff"
Set-Clipboard -Value $payload
Start-Process "https://chat.openai.com/?model=gpt-5"
Write-Host "✅ Diff skopiowany do schowka. Otwórz ChatGPT i wklej (Ctrl+V)."
