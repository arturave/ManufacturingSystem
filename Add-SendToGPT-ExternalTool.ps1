# Add-SendToGPT-ExternalTool.ps1
# Dodaje External Tool w VS2022 i generuje .vssettings z Ctrl+Alt+G

$ErrorActionPreference = "Stop"

function Get-VS2022Hives {
  Get-ChildItem "HKCU:\SOFTWARE\Microsoft\VisualStudio" -Name |
    Where-Object { $_ -like '17.0_*' } |
    ForEach-Object { "HKCU:\SOFTWARE\Microsoft\VisualStudio\$_\External Tools" }
}

function Get-NextToolIndex($extKey) {
  if (-not (Test-Path $extKey)) { New-Item -Path $extKey -Force | Out-Null }
  $existing = Get-ItemProperty -Path $extKey -ErrorAction SilentlyContinue
  if (-not $existing) { return 1 }
  $max = 0
  ($existing.PSObject.Properties | Where-Object { $_.Name -match '^ToolTitle \d+$' } | ForEach-Object {
    [int]($_.Name -replace '[^\d]', '')
  }) | ForEach-Object { if ($_ -gt $max) { $max = $_ } }
  if ($max -lt 1) { return 1 } else { return $max + 1 }
}

function Add-ExternalTool($extKey, $index, $title, $cmd, $args, $dir) {
  New-ItemProperty -Path $extKey -Name ("ToolTitle {0}" -f $index) -Value $title -PropertyType String -Force | Out-Null
  New-ItemProperty -Path $extKey -Name ("ToolCmd {0}"   -f $index) -Value $cmd   -PropertyType String -Force | Out-Null
  New-ItemProperty -Path $extKey -Name ("ToolArg {0}"   -f $index) -Value $args  -PropertyType String -Force | Out-Null
  New-ItemProperty -Path $extKey -Name ("ToolDir {0}"   -f $index) -Value $dir   -PropertyType String -Force | Out-Null
  New-ItemProperty -Path $extKey -Name ("ToolOpt {0}"   -f $index) -Value 0x00000010 -PropertyType DWord -Force | Out-Null
  New-ItemProperty -Path $extKey -Name ("ToolSourceKey {0}" -f $index) -Value "" -PropertyType String -Force | Out-Null
}

function New-KeybindingVssettings($externalIndex, $outputPath) {
  # UŻYJEMY POJEDYNCZEGO HERE-STRINGA I SPECJALNEGO PLACEHOLDERA __IDX__
  $xml = @'
<UserSettings>
  <ApplicationIdentity version="17.0"/>
  <Category name="Environment_Group">
    <Category name="Environment_KeyBindings" Category="{5EFC7975-14BC-11CF-9B2B-00AA00573819}">
      <KeyboardShortcuts>
        <Shortcut Command="Tools.ExternalCommand__IDX__" Scope="Global::Global" Modifiers="Control+Alt" Key="G" />
      </KeyboardShortcuts>
    </Category>
  </Category>
</UserSettings>
'@
  $xml = $xml.Replace("__IDX__", [string]$externalIndex)
  Set-Content -Path $outputPath -Value $xml -Encoding UTF8
}

Write-Host "=== Adding External Tool: SendToGPT ==="

$toolTitle = "SendToGPT"
$toolCmd   = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
$toolArgs  = '-ExecutionPolicy Bypass -NoProfile -File "$(SolutionDir)\tools\ai\SendToGPT.ps1" "$(ItemPath)"'
$toolDir   = '$(ProjectDir)'

$hives = Get-VS2022Hives
if (-not $hives) { throw "VS2022 registry hive not found (17.0_*). Start Visual Studio once and retry." }

$results = @()
foreach ($h in $hives) {
  $idx = Get-NextToolIndex -extKey $h
  Add-ExternalTool -extKey $h -index $idx -title $toolTitle -cmd $toolCmd -args $toolArgs -dir $toolDir
  $results += [pscustomobject]@{ Hive=$h; Index=$idx }
  Write-Host "Added in $h as External Command #$idx"
}

$kbIndex = $results[0].Index
$outVssettings = Join-Path -Path (Get-Location) -ChildPath "VS_Keybinding_SendToGPT.vssettings"
New-KeybindingVssettings -externalIndex $kbIndex -outputPath $outVssettings
Write-Host "Created keyboard file: $outVssettings (Ctrl+Alt+G -> Tools.ExternalCommand$kbIndex)"
Write-Host "Import in VS: Tools → Import and Export Settings → Import → select only 'Keyboard' and choose this file."

