[CmdletBinding()]
param(
    [string]$RuntimeRoot = 'D:/DevTools/llama.cpp/b11552',
    [string]$Python = 'python',
    [switch]$InstallDependencies
)
. (Join-Path $PSScriptRoot 'llama-local-common.ps1')
$runtime = Assert-LlamaPinnedRuntime $RuntimeRoot
$venv = Join-Path $runtime 'conversion-venv'
$requirements = Join-Path $runtime "source/llama.cpp-$script:LlamaPinnedCommit/requirements/requirements-convert_hf_to_gguf.txt"
if (-not $InstallDependencies) {
    [pscustomobject]@{ Status='PREPARED_ONLY'; Runtime=$runtime; Venv=$venv; Requirements=$requirements; Action='Use -InstallDependencies to create an isolated CPU conversion environment; does not convert or start models.' }
    return
}
if (Test-Path -LiteralPath $venv) { throw 'Conversion venv already exists; inspect it instead of overwriting or changing it automatically.' }
Assert-LlamaFreeDisk -Path $venv -MinimumGiB 8
& $Python -m venv $venv
if ($LASTEXITCODE -ne 0) { throw 'venv creation failed.' }
$venvPython = Join-Path $venv 'Scripts/python.exe'
# Pin the official converter's CPU Torch version. Never install Torch into the global environment.
Invoke-LlamaIsolatedProcess -Executable $venvPython -RuntimeRoot $runtime -CpuOnly -Arguments @('-m','pip','install','--index-url','https://download.pytorch.org/whl/cpu','torch==2.11.0')
Invoke-LlamaIsolatedProcess -Executable $venvPython -RuntimeRoot $runtime -CpuOnly -Arguments @('-m','pip','install','-r',$requirements)
[pscustomobject]@{Status='DEPENDENCIES_INSTALLED_NOT_MODEL_VALIDATED'; Venv=$venv}
