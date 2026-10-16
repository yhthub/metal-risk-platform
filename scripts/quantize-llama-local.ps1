[CmdletBinding()]
param(
    [string]$DerivedRoot = 'E:/医学RAG模型/Llama-3.1-8B-Instruct-GGUF',
    [string]$RuntimeRoot = 'D:/DevTools/llama.cpp/b11552',
    [switch]$Execute
)
. (Join-Path $PSScriptRoot 'llama-local-common.ps1')
$inputModel = Join-Path $DerivedRoot 'Llama-3.1-8B-Instruct-F16.gguf'
$output = Assert-LlamaDerivedPath -DerivedRoot $DerivedRoot -OutputPath (Join-Path $DerivedRoot 'Llama-3.1-8B-Instruct-Q4_K_M.gguf')
if (-not $Execute) {
    [pscustomobject]@{Status='PLAN_ONLY'; Input=$inputModel; Output=$output; Quantization='Q4_K_M'; BufferMiB=512; CpuThreads=2; MinimumFreeRamGiB=4}
    return
}
if (-not (Test-Path -LiteralPath $inputModel -PathType Leaf)) { throw 'Completed F16 GGUF missing.' }
$runtime = Assert-LlamaPinnedRuntime $RuntimeRoot
$memory = Assert-LlamaFreeMemory -MinimumGiB 4
Assert-LlamaFreeDisk -Path $output -MinimumGiB 8
Invoke-LlamaIsolatedProcess -Executable (Join-Path $runtime 'bin/llama-quantize.exe') -RuntimeRoot $runtime -CpuOnly -Arguments @('--max-buffer-size','512',$inputModel,$output,'Q4_K_M','2')
Get-FileHash -Algorithm SHA256 -LiteralPath $output
