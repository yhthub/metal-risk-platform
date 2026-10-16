[CmdletBinding()]
param(
    [string]$OriginalWeights = 'E:/医学RAG模型/Llama-3.1-8B-Instruct',
    [string]$DerivedRoot = 'E:/医学RAG模型/Llama-3.1-8B-Instruct-GGUF',
    [string]$RuntimeRoot = 'D:/DevTools/llama.cpp/b11552',
    [switch]$WeightsVerified,
    [switch]$Execute
)
. (Join-Path $PSScriptRoot 'llama-local-common.ps1')
$output = Assert-LlamaDerivedPath -DerivedRoot $DerivedRoot -OutputPath (Join-Path $DerivedRoot 'Llama-3.1-8B-Instruct-F16.gguf') -OriginalRoot $OriginalWeights
$memory = Get-LlamaMemoryGiB
if (-not $Execute) {
    [pscustomobject]@{Status='PLAN_ONLY'; Input=$OriginalWeights; Output=$output; FreeRamGiB=$memory.FreeGiB; MinimumFreeRamGiB=6; Lazy=$true; UseTempFile=$true; Requirements='Complete source SHA256 verification plus -WeightsVerified and -Execute; no conversion started.'}
    return
}
if (-not $WeightsVerified) { throw 'Wait for complete transfer, verify the original SHA256 manifest, then explicitly attest with -WeightsVerified. A directory listing is not integrity verification.' }
if (-not (Test-Path -LiteralPath $OriginalWeights -PathType Container)) { throw 'Original weights directory missing.' }
if (Get-ChildItem -LiteralPath $OriginalWeights -File | Where-Object { $_.Name -match '\.(part|partial|tmp)$' }) { throw 'Partial download detected; conversion forbidden.' }
$indexPath = Join-Path $OriginalWeights 'model.safetensors.index.json'
if (-not (Test-Path -LiteralPath $indexPath -PathType Leaf)) { throw 'Expected safetensors index missing; review this model variant before conversion.' }
$index = Get-Content -LiteralPath $indexPath -Raw | ConvertFrom-Json
foreach ($name in @($index.weight_map.PSObject.Properties.Value | Sort-Object -Unique)) {
    if ([System.IO.Path]::GetFileName($name) -ne $name) { throw 'Weight index contains non-local paths.' }
    if (-not (Test-Path -LiteralPath (Join-Path $OriginalWeights $name) -PathType Leaf)) { throw "Missing source shard: $name" }
}
$runtime = Assert-LlamaPinnedRuntime $RuntimeRoot
$memory = Assert-LlamaFreeMemory -MinimumGiB 6
Assert-LlamaFreeDisk -Path $output -MinimumGiB 40
$venvPython = Join-Path $runtime 'conversion-venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) { throw 'Prepare the isolated conversion venv first.' }
New-Item -ItemType Directory -Path $DerivedRoot -Force | Out-Null
$taskTemp = Join-Path $DerivedRoot ('conversion-temp-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskTemp | Out-Null
$converter = Join-Path $runtime "source/llama.cpp-$script:LlamaPinnedCommit/convert_hf_to_gguf.py"
# Default lazy evaluation plus temp-file buffering; deliberately do not set --no-lazy.
Invoke-LlamaIsolatedProcess -Executable $venvPython -RuntimeRoot $runtime -TempDirectory $taskTemp -CpuOnly -Arguments @('-B',$converter,$OriginalWeights,'--outfile',$output,'--outtype','f16','--use-temp-file')
Get-FileHash -Algorithm SHA256 -LiteralPath $output
# Keep temporary/partial artifacts for audit; no automatic deletion or overwrite.
