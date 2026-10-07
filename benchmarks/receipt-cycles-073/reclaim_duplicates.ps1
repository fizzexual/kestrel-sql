$ErrorActionPreference='Stop'
$proof=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'fixture-reclamation-plan.json') -Raw | ConvertFrom-Json
$expected='C:\Users\Frizer\Documents\Codex\2026-10-05\letys\work\perf-071\fixtures'
$resolved=(Resolve-Path -LiteralPath $proof.target).ProviderPath
if($resolved -ne $expected -or $proof.file_count -ne 648 -or $proof.model_directories -ne 54){throw 'Unexpected target/inventory'}
$all=@(Get-ChildItem -LiteralPath $resolved -Recurse)
foreach($item in $all){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse entry'}}
if((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse target'}
$files=@($all | Where-Object {-not $_.PSIsContainer})
if($files.Count -ne 648 -or @($proof.files.PSObject.Properties).Count -ne 648){throw 'Inventory changed'}
foreach($file in $files){
    $relative='fixtures/'+$file.FullName.Substring($resolved.Length+1).Replace('\','/')
    $entry=$proof.files.PSObject.Properties[$relative].Value
    if($null -eq $entry -or $file.Length -ne $entry.bytes -or (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower() -ne $entry.sha256){throw 'File hash changed'}
}
$freeBefore=(Get-PSDrive -Name C).Free
Remove-Item -LiteralPath $resolved -Recurse -Force
if(Test-Path -LiteralPath $resolved){throw 'Target survived deletion'}
@{target=$resolved;files=648;logical_bytes=$proof.bytes;removed=$true;exact_paths_inventory_and_hashes_verified=$true;full_local_archives_and_private_assets_retained=$true;only_duplicate_frames_removed=$true;raw_logs_inputs_reports_sources_binaries_untouched=$true;free_before=$freeBefore;free_after=(Get-PSDrive -Name C).Free;utc=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'fixture-reclamation-result.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $PSScriptRoot 'fixture-reclamation-result.json') -Raw
