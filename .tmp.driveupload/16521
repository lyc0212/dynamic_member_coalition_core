$ErrorActionPreference = 'Stop'
$repo = 'D:\1st\dynamic_member_coalition_core'
$python = 'D:\anaconda3\python.exe'
$head = '72fda26ffe1a1049a4de30bda52586587106e387'
Set-Location $repo
if ((git branch --show-current).Trim() -ne 'main') { throw 'BRANCH_MISMATCH' }
if ((git rev-parse HEAD).Trim() -ne $head) { throw 'HEAD_MISMATCH' }
if (@(git status --porcelain --untracked-files=all).Count -ne 0) { throw 'DIRTY_WORKTREE' }
if (-not (Test-Path -LiteralPath $python)) { throw 'PYTHON_NOT_FOUND' }
$dir = Join-Path $PSScriptRoot 'd2a_evidence'
New-Item -ItemType Directory -Path $dir -ErrorAction Stop | Out-Null
$stdout = Join-Path $dir 'stdout.txt'
$stderr = Join-Path $dir 'stderr.txt'
$cleanupLog = Join-Path $dir 'cleanup.txt'
$receiptPath = Join-Path $dir 'receipt.json'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTEST_ADDOPTS = ''
$record = [ordered]@{
    task='M3_D2_A_DETERMINISTIC_TEST'; head=$head
    command='D:\anaconda3\python.exe -B -m pytest -q -x -p no:cacheprovider tests/test_stfbs_lite_real_d60_m3_cpu_guard.py'
    started_utc=[DateTime]::UtcNow.ToString('o'); wall_limit_seconds=45
    timed_out=$false; pytest_pid=$null; pytest_exit_code=$null
    cleanup_verified=$null; controller_error=$null; worktree_clean_after=$null
    stdout_path=$stdout; stderr_path=$stderr; elapsed_seconds=$null
    timeout_request_elapsed_seconds=$null
}
$p=$null
$watch=[Diagnostics.Stopwatch]::StartNew()
try {
    $p=Start-Process -FilePath $python -ArgumentList @(
        '-B','-m','pytest','-q','-x','-p','no:cacheprovider',
        'tests/test_stfbs_lite_real_d60_m3_cpu_guard.py'
    ) -WorkingDirectory $repo -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $record.pytest_pid=$p.Id
    $null=$p.Handle
    $remaining=[Math]::Max(0,45000-[int]$watch.ElapsedMilliseconds)
    if (-not $p.WaitForExit($remaining)) {
        $record.timed_out=$true
        $record.timeout_request_elapsed_seconds=$watch.Elapsed.TotalSeconds
        & taskkill.exe /PID $p.Id /T /F 2>&1 | Out-File -LiteralPath $cleanupLog
        $null=$p.WaitForExit(3000)
    }
    $p.Refresh()
    $record.cleanup_verified=$p.HasExited
    if ($p.HasExited) { $record.pytest_exit_code=$p.ExitCode }
} catch {
    $record.controller_error=$_.ToString()
} finally {
    if ($null -ne $p) {
        $p.Refresh()
        if (-not $p.HasExited) {
            try {
                & taskkill.exe /PID $p.Id /T /F 2>&1 | Out-File -LiteralPath $cleanupLog -Append
                $null=$p.WaitForExit(3000)
                if (-not $p.HasExited) { $p.Kill(); $null=$p.WaitForExit(1000) }
            } catch { $_ | Out-File -LiteralPath $cleanupLog -Append }
        }
        $p.Refresh()
        $record.cleanup_verified=$p.HasExited
        if ($p.HasExited) { $record.pytest_exit_code=$p.ExitCode }
    }
    $record.elapsed_seconds=$watch.Elapsed.TotalSeconds
    $record.worktree_clean_after=(@(git status --porcelain --untracked-files=all).Count -eq 0)
    $record.ended_utc=[DateTime]::UtcNow.ToString('o')
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
}
Write-Output "Evidence: $dir"
if ($record.timed_out -or $null -ne $record.controller_error -or $null -eq $record.pytest_exit_code -or $record.pytest_exit_code -ne 0 -or $record.cleanup_verified -ne $true -or $record.worktree_clean_after -ne $true) {
    throw 'M3_D2_A_FAILED_OR_INCOMPLETE'
}
Write-Output 'M3_D2_A_PASS_CANDIDATE'
