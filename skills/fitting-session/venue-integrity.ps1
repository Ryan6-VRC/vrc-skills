<#
  venue-integrity.ps1 — grade what a fitting-session worker changed on disk.

  The venue (the Unity avatar project a worker is turned loose in) is an UNTRACKED working folder,
  not a git repo — `git diff`/`git restore` silently report "clean" against it and detect nothing.
  This tool replaces that grading step with a filesystem walk: snapshot before, diff after. There
  is no revert; the venue is disposable and just accumulates. Pure filesystem — no Unity, no MCP,
  no git.

  Scope (deliberately kept out of the calling skill, not a caller-supplied parameter):
    include  <venue>/Assets/**                    + the single file <venue>/Packages/vpm-manifest.json
    exclude  Assets/Agent/Scratch|RunLogs|Snapshots/**, Assets/Plugins/Roslyn/**, everything else
             outside Assets/.
  The venue carries a residual .gitignore from when it was a tracked repo (ignores Assets/Vendor/,
  *.png, *.psd, *.fbx, ...) — exactly the worker deliverables this tool exists to catch. The walk
  is filesystem-based and never reads .gitignore.

  Change basis = file size + LastWriteTimeUtc.Ticks (an integer, so it survives DST/locale
  round-trips that a formatted local-time string would not). No content hashing — reading a 7+ GB
  venue to detect what mtime already tells us buys nothing.

  Usage:
    venue-integrity.ps1 -Snapshot -Venue <path> -Out <manifest>
    venue-integrity.ps1 -Diff -Before <manifest> -Venue <path>      # prints "A|M|D <relpath>", exit 0
    venue-integrity.ps1 -SelfTest                                  # exit 0 iff every assertion holds

  The manifest's internal format is private to this tool. Only the -Diff stdout contract (one of
  A/M/D, a space, a venue-root-relative path with forward slashes) is load-bearing for callers.
#>
[CmdletBinding()]
param(
  [Parameter(ParameterSetName = 'Snapshot', Mandatory = $true)] [switch]$Snapshot,
  [Parameter(ParameterSetName = 'Diff', Mandatory = $true)]     [switch]$Diff,
  [Parameter(ParameterSetName = 'SelfTest', Mandatory = $true)] [switch]$SelfTest,

  [Parameter(ParameterSetName = 'Snapshot', Mandatory = $true)]
  [Parameter(ParameterSetName = 'Diff', Mandatory = $true)]
  [string]$Venue,

  [Parameter(ParameterSetName = 'Snapshot', Mandatory = $true)] [string]$Out,
  [Parameter(ParameterSetName = 'Diff', Mandatory = $true)]     [string]$Before
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Exclude prefixes are matched against a forward-slash, venue-root-relative path (e.g.
# "Assets/Agent/Scratch/foo.txt") — never against the raw backslash path, or a caller on Windows
# would see the exclusion silently defeated.
$script:ExcludePrefixes = @(
  'Assets/Agent/Scratch/',
  'Assets/Agent/RunLogs/',
  'Assets/Agent/Snapshots/',
  'Assets/Plugins/Roslyn/'
)

function Test-AssetInScope([string]$relPath) {
  foreach ($p in $script:ExcludePrefixes) {
    if ($relPath.StartsWith($p, [StringComparison]::OrdinalIgnoreCase)) { return $false }
  }
  return $true
}

# Resolve to an absolute, normalized path without requiring the path to exist (the -Out manifest
# may not exist yet). Rooted paths normalize directly; relative ones resolve against PowerShell's
# current location, not the process CWD [System.IO.Path]::GetFullPath would otherwise use.
function Resolve-AbsPath([string]$path) {
  if ([System.IO.Path]::IsPathRooted($path)) { return [System.IO.Path]::GetFullPath($path) }
  return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).ProviderPath $path))
}

# A manifest written inside the venue self-registers as an added file and corrupts every later
# diff, so the tool refuses it — the calling skill never pins where the manifest goes.
function Assert-ManifestOutsideVenue([string]$venueRoot, [string]$manifestPath) {
  $root = (Resolve-Path -LiteralPath $venueRoot).ProviderPath.TrimEnd('\', '/')
  $manAbs = (Resolve-AbsPath $manifestPath).TrimEnd('\', '/')
  $rootPrefix = $root + [System.IO.Path]::DirectorySeparatorChar
  if ($manAbs.Equals($root, [StringComparison]::OrdinalIgnoreCase) -or
      $manAbs.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "manifest must live outside the venue (it would self-register as a change): $manAbs"
  }
}

# Walks the venue's deliverable scope and returns one entry per in-scope file: Rel (forward-slash,
# venue-root-relative), Size, Ticks. [System.IO.Directory]::EnumerateFiles, not Get-ChildItem
# -Recurse — the latter is tens of seconds over an 8k-file tree under Windows Defender.
# Packages/ is walked as a single named-file stat, never enumerated: the reproduced SDK payload
# under Packages/ is multi-GB and entirely out of scope except the one manifest.
function Get-VenueEntries([string]$venueRoot) {
  $root = (Resolve-Path -LiteralPath $venueRoot).ProviderPath.TrimEnd('\', '/')
  $entries = New-Object System.Collections.Generic.List[object]

  # IgnoreInaccessible so one ACL-blocked subdirectory degrades the walk past it instead of aborting
  # the whole enumeration under ErrorActionPreference='Stop' (the AllDirectories overload throws).
  $opts = [System.IO.EnumerationOptions]@{ RecurseSubdirectories = $true; IgnoreInaccessible = $true }
  $assetsRoot = Join-Path $root 'Assets'
  if ([System.IO.Directory]::Exists($assetsRoot)) {
    foreach ($full in [System.IO.Directory]::EnumerateFiles($assetsRoot, '*', $opts)) {
      $rel = $full.Substring($root.Length).TrimStart('\', '/') -replace '\\', '/'
      if (-not (Test-AssetInScope $rel)) { continue }
      $fi = [System.IO.FileInfo]::new($full)
      $entries.Add([pscustomobject]@{ Rel = $rel; Size = $fi.Length; Ticks = $fi.LastWriteTimeUtc.Ticks })
    }
  }

  $manifestPath = Join-Path $root 'Packages/vpm-manifest.json'
  if ([System.IO.File]::Exists($manifestPath)) {
    $fi = [System.IO.FileInfo]::new($manifestPath)
    $entries.Add([pscustomobject]@{ Rel = 'Packages/vpm-manifest.json'; Size = $fi.Length; Ticks = $fi.LastWriteTimeUtc.Ticks })
  }

  return $entries
}

function Write-VenueManifest([string]$venueRoot, [string]$outPath) {
  $entries = Get-VenueEntries $venueRoot
  $parent = Split-Path -Parent $outPath
  if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  $lines = foreach ($e in ($entries | Sort-Object Rel)) { "$($e.Rel)`t$($e.Size)`t$($e.Ticks)" }
  Set-Content -LiteralPath $outPath -Value $lines -Encoding utf8
  return $entries.Count
}

function Read-VenueManifest([string]$path) {
  $map = @{}
  foreach ($line in [System.IO.File]::ReadLines($path)) {
    if (-not $line) { continue }
    $parts = $line.Split("`t")
    if ($parts.Count -ne 3) { continue }
    $map[$parts[0]] = [pscustomobject]@{ Size = [int64]$parts[1]; Ticks = [int64]$parts[2] }
  }
  return $map
}

# Returns "A|M|D <relpath>" lines, sorted by relpath. A single pass over the union of before/after
# paths — cheaper than three separate set operations and keeps the classification in one place.
function Get-VenueDiff([string]$beforePath, [string]$venueRoot) {
  $beforeMap = Read-VenueManifest $beforePath
  $afterMap = @{}
  foreach ($e in (Get-VenueEntries $venueRoot)) { $afterMap[$e.Rel] = $e }

  # Case-insensitive to match Windows' filesystem and the case-insensitive before/after maps — else
  # a case-only rename (Assets/foo.txt -> Assets/Foo.txt) splits into two contradictory lines.
  $allRel = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  foreach ($k in $beforeMap.Keys) { [void]$allRel.Add($k) }
  foreach ($k in $afterMap.Keys) { [void]$allRel.Add($k) }

  $lines = New-Object System.Collections.Generic.List[string]
  foreach ($rel in ($allRel | Sort-Object)) {
    $inBefore = $beforeMap.ContainsKey($rel)
    $inAfter = $afterMap.ContainsKey($rel)
    if ($inAfter -and -not $inBefore) {
      $lines.Add("A $rel")
    } elseif ($inBefore -and -not $inAfter) {
      $lines.Add("D $rel")
    } else {
      $b = $beforeMap[$rel]; $a = $afterMap[$rel]
      if ($a.Size -ne $b.Size -or $a.Ticks -ne $b.Ticks) { $lines.Add("M $rel") }
    }
  }
  return $lines
}

function Invoke-SelfTest {
  # Diagnostics go through Write-Host (never the success/output stream): the caller wraps this
  # function as `exit (Invoke-SelfTest)`, and any object this function put on the pipeline would be
  # captured by that subexpression instead of reaching the console — output would vanish silently.
  # Only the final int is meant to reach the caller.
  $root = Join-Path $env:TEMP ("venue-integrity-selftest-" + [guid]::NewGuid().ToString('N'))
  $failures = New-Object System.Collections.Generic.List[string]
  function Test-Assertion([System.Collections.Generic.List[string]]$failures, [bool]$cond, [string]$name, [string]$detail) {
    if ($cond) { Write-Host "  PASS  $name" }
    else { Write-Host "  FAIL  $name — $detail"; $failures.Add($name) }
  }

  try {
    # --- build a synthetic venue-shaped tree ---
    New-Item -ItemType Directory -Force -Path (Join-Path $root 'Assets/Foo') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $root 'Assets/ToDelete') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $root 'Assets/Agent/Scratch') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $root 'Assets/Vendor') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $root 'Packages') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $root 'Library') | Out-Null

    $keepPath = Join-Path $root 'Assets/Foo/keep.txt'
    Set-Content -LiteralPath $keepPath -Value 'AAAA' -NoNewline -Encoding utf8

    $deletePath = Join-Path $root 'Assets/ToDelete/gone.txt'
    Set-Content -LiteralPath $deletePath -Value 'bye' -NoNewline -Encoding utf8

    $casePath = Join-Path $root 'Assets/Foo/case.txt'
    Set-Content -LiteralPath $casePath -Value 'zzz' -NoNewline -Encoding utf8

    $scratchPath = Join-Path $root 'Assets/Agent/Scratch/junk.txt'
    Set-Content -LiteralPath $scratchPath -Value 'scratch' -NoNewline -Encoding utf8

    $outsidePath = Join-Path $root 'Library/outside.txt'
    Set-Content -LiteralPath $outsidePath -Value 'outside' -NoNewline -Encoding utf8

    $manifestPath = Join-Path $root 'Packages/vpm-manifest.json'
    Set-Content -LiteralPath $manifestPath -Value '{}' -NoNewline -Encoding utf8

    # Residual .gitignore, same shape as the real venue's — must be ignored entirely by the walk.
    Set-Content -LiteralPath (Join-Path $root '.gitignore') -Value "Assets/Vendor/`n*.png`n" -Encoding utf8

    $manifestOut = Join-Path $root 'before.manifest'
    Write-VenueManifest -venueRoot $root -outPath $manifestOut | Out-Null

    Start-Sleep -Milliseconds 50

    # --- mutate ---
    # 1. add
    Set-Content -LiteralPath (Join-Path $root 'Assets/Foo/new.txt') -Value 'new' -NoNewline -Encoding utf8

    # 2. delete
    Remove-Item -LiteralPath $deletePath -Force

    # 3. same-size, mtime-only modify. Content is a different byte for byte, same length as "AAAA" —
    # the one branch that a size-only diff would silently miss. Explicitly bump mtime forward
    # rather than relying on filesystem clock resolution across two writes microseconds apart.
    Set-Content -LiteralPath $keepPath -Value 'BBBB' -NoNewline -Encoding utf8
    [System.IO.File]::SetLastWriteTimeUtc($keepPath, [System.IO.File]::GetLastWriteTimeUtc($keepPath).AddHours(1))

    # 4. touch excluded paths
    Set-Content -LiteralPath $scratchPath -Value 'scratch2' -NoNewline -Encoding utf8
    Set-Content -LiteralPath $outsidePath -Value 'outside2' -NoNewline -Encoding utf8

    # 5. .gitignore-ignored deliverable (Vendor/ + *.png) — must still surface
    Set-Content -LiteralPath (Join-Path $root 'Assets/Vendor/foo.png') -Value 'PNG' -NoNewline -Encoding utf8

    # 6. case-only rename (case.txt -> CASE.txt, content also changed) — the union set must dedup
    # case-insensitively so this collapses to a single M, never two contradictory lines.
    Remove-Item -LiteralPath $casePath -Force
    Set-Content -LiteralPath (Join-Path $root 'Assets/Foo/CASE.txt') -Value 'ZZZZ' -NoNewline -Encoding utf8

    $diffLines = Get-VenueDiff -beforePath $manifestOut -venueRoot $root
    $diffJoined = $diffLines -join '; '

    Test-Assertion $failures ($diffLines -contains 'A Assets/Foo/new.txt') `
      'new file -> A' "not found in diff: $diffJoined"

    Test-Assertion $failures ($diffLines -contains 'D Assets/ToDelete/gone.txt') `
      'deleted file -> D' "not found in diff: $diffJoined"

    Test-Assertion $failures ($diffLines -contains 'M Assets/Foo/keep.txt') `
      'same-size mtime-only modify -> M' "not found in diff: $diffJoined"

    $scratchHit = @($diffLines | Where-Object { $_ -like '*Assets/Agent/Scratch*' })
    $outsideHit = @($diffLines | Where-Object { $_ -like '*outside.txt*' })
    Test-Assertion $failures (($scratchHit.Count -eq 0) -and ($outsideHit.Count -eq 0)) `
      'Scratch/ + outside-Assets touch -> excluded' "leaked: $(@($scratchHit + $outsideHit) -join '; ')"

    Test-Assertion $failures ($diffLines -contains 'A Assets/Vendor/foo.png') `
      '.gitignore-ignored deliverable still surfaces -> A' "not found in diff: $diffJoined"

    $caseHits = @($diffLines | Where-Object { $_ -match '(?i)/case\.txt$' })
    Test-Assertion $failures ($caseHits.Count -eq 1) `
      'case-only rename -> exactly one line, not duplicate/contradictory' "got: $($caseHits -join '; ')"

    $guardThrew = $false
    try { Assert-ManifestOutsideVenue -venueRoot $root -manifestPath (Join-Path $root 'Assets/inside.manifest') }
    catch { $guardThrew = $true }
    Test-Assertion $failures $guardThrew `
      '-Out inside venue -> rejected' "guard did not throw"

    Write-Host "  --- diff output ---"
    $diffLines | ForEach-Object { Write-Host "  $_" }
  }
  finally {
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue }
  }

  if ($failures.Count -gt 0) {
    Write-Host "SELFTEST FAILED: $($failures.Count) assertion(s) failed — $($failures -join '; ')"
    return 1
  }
  Write-Host "SELFTEST OK: 7/7 assertions passed"
  return 0
}

switch ($PSCmdlet.ParameterSetName) {
  'Snapshot' {
    Assert-ManifestOutsideVenue -venueRoot $Venue -manifestPath $Out
    $count = Write-VenueManifest -venueRoot $Venue -outPath $Out
    "Snapshot: $count in-scope file(s) -> $Out"
    exit 0
  }
  'Diff' {
    Assert-ManifestOutsideVenue -venueRoot $Venue -manifestPath $Before
    (Get-VenueDiff -beforePath $Before -venueRoot $Venue) | ForEach-Object { $_ }
    exit 0
  }
  'SelfTest' {
    exit (Invoke-SelfTest)
  }
}
