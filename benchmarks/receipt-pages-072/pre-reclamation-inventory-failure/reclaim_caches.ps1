$ErrorActionPreference='Stop'
$taskWorkspace='C:\Users\Frizer\Documents\Codex\2026-10-05\letys\work'
$proofPath=Join-Path $PSScriptRoot 'cache-reclamation-plan.json'
$proof=Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
if($proof.targets.Count -ne 3){throw 'Unexpected target count'}
$records=@()
$freeBefore=(Get-PSDrive -Name C).Free
foreach($target in $proof.targets){
    $expected=Join-Path $taskWorkspace ('perf-{0:000}\build-cache' -f $target.trial)
    $resolved=(Resolve-Path -LiteralPath $target.path).ProviderPath
    if($resolved -ne $expected -or -not $resolved.StartsWith($taskWorkspace+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target outside exact task cache'}
    if((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse target'}
    if(-not (Get-Content -LiteralPath (Join-Path $resolved 'CACHEDIR.TAG') -Raw).StartsWith('Signature: 8a477f597d28d172789f06886806bc55')){throw 'Cache tag missing'}
    $current=@(Get-ChildItem -LiteralPath $resolved -Recurse -File)
    if($current.Count -ne $target.files.PSObject.Properties.Count){throw 'Cache inventory changed'}
    foreach($file in $current){
        if($file.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse file'}
        $relative=$file.FullName.Substring($resolved.Length+1).Replace('\','/')
        $entry=$target.files.PSObject.Properties[$relative].Value
        if($null -eq $entry -or $file.Length -ne $entry.bytes -or (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower() -ne $entry.sha256){throw 'Cache hash changed'}
    }
    foreach($dir in (Get-ChildItem -LiteralPath $resolved -Directory -Recurse)){
        if($dir.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse directory'}
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
    if(Test-Path -LiteralPath $resolved){throw 'Cache survived deletion'}
    $records+=@{path=$resolved;files=$current.Count;bytes=$target.bytes;inventory_verified_before_remove=$true;removed=$true}
}
@{targets=$records;free_before=$freeBefore;free_after=(Get-PSDrive -Name C).Free;no_raw_evidence_deleted=$true;no_current_072_cache_deleted=$true;utc=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'cache-reclamation-result.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cache-reclamation-result.json') -Raw
