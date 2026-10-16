[CmdletBinding()]
param(
    [string]$ModelPath = 'E:/医学RAG模型/Llama-3.1-8B-Instruct-GGUF/Llama-3.1-8B-Instruct-Q4_K_M.gguf',
    [string]$RuntimeRoot = 'D:/DevTools/llama.cpp/b11552',
    [string]$ApiKeyFile,
    [ValidateRange(0,20)][int]$GpuLayers = 16,
    [switch]$Execute
)
. (Join-Path $PSScriptRoot 'llama-local-common.ps1')
$memory = Get-LlamaMemoryGiB
$arguments = @('--model',$ModelPath,'--host','127.0.0.1','--port','8081','--alias','Llama-3.1-8B',
               '--ctx-size','4096','--parallel','1','--gpu-layers',"$GpuLayers",'--fit','on','--fit-target','1536',
               '--batch-size','256','--ubatch-size','128','--threads','4','--threads-batch','4',
               '--load-mode','mmap','--flash-attn','on','--cache-type-k','q8_0','--cache-type-v','q8_0','--no-webui')
if (-not $Execute) {
    [pscustomobject]@{Status='PLAN_ONLY'; Model=$ModelPath; Endpoint='http://127.0.0.1:8081/v1'; Alias='Llama-3.1-8B'; Context=4096; Parallel=1; GpuLayers=$GpuLayers; VramMarginMiB=1536; FreeRamGiB=$memory.FreeGiB; MinimumFreeRamGiB=6; Requires='Verified Q4_K_M plus protected ApiKeyFile and -Execute; no service started.'}
    return
}
if (-not [System.IO.Path]::IsPathFullyQualified($ModelPath) -or -not (Test-Path -LiteralPath $ModelPath -PathType Leaf)) { throw 'Quantized model path must be an existing absolute file.' }
if (-not $ModelPath.EndsWith('Q4_K_M.gguf', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'This profile is for the explicit Q4_K_M derived model only.' }
if (-not $ApiKeyFile -or -not [System.IO.Path]::IsPathFullyQualified($ApiKeyFile) -or -not (Test-Path -LiteralPath $ApiKeyFile -PathType Leaf)) { throw 'Provide a separately protected key file; never embed or print the key.' }
if (Get-NetTCPConnection -LocalPort 8081 -State Listen -ErrorAction SilentlyContinue) { throw 'Port 8081 is in use; do not stop or replace an existing service.' }
$runtime = Assert-LlamaPinnedRuntime $RuntimeRoot
$memory = Assert-LlamaFreeMemory -MinimumGiB 6
if ($GpuLayers -gt 0) {
    $gpuLine = & nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>$null | Select-Object -First 1
    if ($LASTEXITCODE -ne 0 -or -not $gpuLine -or [int]$gpuLine -lt 3500) { throw 'Need >= 3500 MiB currently free VRAM for this conservative profile; no GPU task started.' }
}
$arguments += @('--api-key-file',$ApiKeyFile)
# No tools/MCP/media path, no remote model URL, no web UI. Bind ONLY loopback.
Invoke-LlamaIsolatedProcess -Executable (Join-Path $runtime 'bin/llama-server.exe') -RuntimeRoot $runtime -Arguments $arguments -CpuOnly:($GpuLayers -eq 0)
