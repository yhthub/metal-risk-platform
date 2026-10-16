# Helpers only: do not start models or install dependencies when dot-sourced.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:LlamaPinnedCommit = '23b0202a189c44a54625aadcb37a946dd1d6278d'

function Assert-LlamaPinnedRuntime {
    param([Parameter(Mandatory)][string]$RuntimeRoot)
    $runtimeAbsolute = [System.IO.Path]::GetFullPath($RuntimeRoot)
    $expected = @{
        'llama-b11552-bin-win-cuda-12.4-x64.zip' = 'e48331718aa82aa34571cfad8510e6d6b9a8e4dad11a73e065f94f212e280256'
        'cudart-llama-bin-win-cuda-12.4-x64.zip' = '8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6'
        'bin/llama-server.exe' = '6a13c30b9086fc7d0d67fb0ffd1d85ef3a376c17b1b2262e064dffa49585614e'
        'bin/llama-quantize.exe' = '28f7c258c6491b84bdc9c5ced700c36667e1cedad18d3697bff5e157445f7146'
        'llama.cpp-source-23b0202.zip' = '355e34b9f018978ff93c9c6dc4fbb06b40ad51e5704e690078eda3407c7bfb9b'
        "source/llama.cpp-$script:LlamaPinnedCommit/convert_hf_to_gguf.py" = 'e9a1da876330bbce9687541ab31736542a01b4ac43c6686126514a50f122fb7f'
    }
    foreach ($relative in $expected.Keys) {
        $candidate = Join-Path $runtimeAbsolute $relative
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw "Pinned runtime file missing: $relative" }
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $candidate).Hash.ToLowerInvariant() -ne $expected[$relative]) {
            throw "Pinned runtime hash mismatch: $relative"
        }
    }
    return $runtimeAbsolute
}

function Get-LlamaMemoryGiB {
    $os = Get-CimInstance Win32_OperatingSystem
    return [pscustomobject]@{ TotalGiB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2); FreeGiB = [math]::Round($os.FreePhysicalMemory / 1MB, 2) }
}

function Assert-LlamaFreeMemory {
    param([double]$MinimumGiB)
    $memory = Get-LlamaMemoryGiB
    if ($memory.FreeGiB -lt $MinimumGiB) { throw "Insufficient currently available RAM: $($memory.FreeGiB) GiB; require >= $MinimumGiB GiB. Close other applications or use separately authorized offline quantization hardware. No job started." }
    return $memory
}

function Assert-LlamaDerivedPath {
    param([Parameter(Mandatory)][string]$DerivedRoot, [Parameter(Mandatory)][string]$OutputPath, [string]$OriginalRoot)
    if (-not [System.IO.Path]::IsPathFullyQualified($DerivedRoot) -or -not [System.IO.Path]::IsPathFullyQualified($OutputPath)) {
        throw 'All model/output paths must be fully qualified.'
    }
    $root = [System.IO.Path]::GetFullPath($DerivedRoot).TrimEnd('\','/')
    $output = [System.IO.Path]::GetFullPath($OutputPath)
    if ($root.Length -le 3 -or -not $output.StartsWith($root + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Output must remain inside a dedicated derived-model directory, not a drive/workspace root.'
    }
    if ($OriginalRoot) {
        $original = [System.IO.Path]::GetFullPath($OriginalRoot).TrimEnd('\','/')
        if ($root -eq $original -or $root.StartsWith($original + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw 'Never write converted/quantized output into the original weight directory.'
        }
    }
    if (Test-Path -LiteralPath $output) { throw 'Output exists: choose a new generation, never overwrite.' }
    return $output
}

function Assert-LlamaFreeDisk {
    param([string]$Path, [double]$MinimumGiB)
    $drive = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath($Path)))
    if (($drive.AvailableFreeSpace / 1GB) -lt $MinimumGiB) { throw "Insufficient disk space: require >= $MinimumGiB GiB free on the derived-output drive." }
}

function Invoke-LlamaIsolatedProcess {
    param([string]$Executable, [string[]]$Arguments, [string]$RuntimeRoot, [string]$TempDirectory, [switch]$CpuOnly)
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'Use PowerShell 7; isolated ArgumentList requires .NET Core.' }
    $info = [System.Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $Executable
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    # Never inherit tool/model-download/MCP settings from another llama-server session.
    foreach ($key in @($info.Environment.Keys)) {
        if ($key.StartsWith('LLAMA_ARG_', [System.StringComparison]::OrdinalIgnoreCase)) { $info.Environment.Remove($key) | Out-Null }
    }
    $info.Environment['PATH'] = (Join-Path $RuntimeRoot 'cuda') + ';' + (Join-Path $RuntimeRoot 'bin') + ';' + $info.Environment['PATH']
    $info.Environment['HF_HUB_OFFLINE'] = '1'
    $info.Environment['TRANSFORMERS_OFFLINE'] = '1'
    if ($TempDirectory) { $info.Environment['TEMP'] = $TempDirectory; $info.Environment['TMP'] = $TempDirectory }
    if ($CpuOnly) { $info.Environment['CUDA_VISIBLE_DEVICES'] = '-1' }
    $process = [System.Diagnostics.Process]::Start($info)
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw "Native/Python task failed with exit code $($process.ExitCode); keep any partial output for audit and do not retry/overwrite automatically." }
}
