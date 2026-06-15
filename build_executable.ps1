# Build Script for AlgoSwitcher and StabilizationSwitcher Executables
# This script builds standalone executables using PyInstaller

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Multi-Tool Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if Python is available
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow

# Try to find Python
$pythonCmd = $null
$pythonPaths = @(
    "python",
    "py",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe",
    "C:\Python310\python.exe"
)

foreach ($path in $pythonPaths) {
    try {
        $testOutput = & $path --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $testOutput -match "Python") {
            $pythonCmd = $path
            Write-Host "  OK Found: $testOutput" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "  X Error: Python not found" -ForegroundColor Red
    Write-Host "  Please install Python from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Check/Install required packages
Write-Host ""
Write-Host "[2/6] Checking required packages..." -ForegroundColor Yellow

$requiredPackages = @("pyinstaller", "pandas", "openpyxl")
foreach ($package in $requiredPackages) {
    $installed = & $pythonCmd -m pip show $package 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Installing $package..." -ForegroundColor Cyan
        & $pythonCmd -m pip install $package
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  X Failed to install $package" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  OK $package is installed" -ForegroundColor Green
    }
}

# Clean previous build
Write-Host ""
Write-Host "[3/7] Cleaning previous build..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item "build" -Recurse -Force
    Write-Host "  OK Removed old build directory" -ForegroundColor Green
}
if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
    Write-Host "  OK Removed old dist directory" -ForegroundColor Green
}

# Update spec file with data files
Write-Host ""
Write-Host "[4/7] Preparing spec files..." -ForegroundColor Yellow

# Spec file for AlgoSwitcher
$specContent1 = @"
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['switch_algo.py'],
    pathex=[],
    binaries=[],
    datas=[('abtesting_instructions', 'abtesting_instructions')],
    hiddenimports=['pandas', 'openpyxl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AlgoSwitcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"@

Set-Content -Path "AlgoSwitcher.spec" -Value $specContent1
Write-Host "  OK AlgoSwitcher.spec created" -ForegroundColor Green

# Spec file for StabilizationSwitcher
$specContent2 = @"
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['stabilization_switcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='StabilizationSwitcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"@

Set-Content -Path "StabilizationSwitcher.spec" -Value $specContent2
Write-Host "  OK StabilizationSwitcher.spec created" -ForegroundColor Green

# Spec file for MultivariateSwitcher
$specContent3 = @"
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['multivariate_testing.py'],
    pathex=[],
    binaries=[],
    datas=[('abtesting_instructions', 'abtesting_instructions')],
    hiddenimports=['pandas', 'openpyxl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MultivariateSwitcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"@

Set-Content -Path "MultivariateSwitcher.spec" -Value $specContent3
Write-Host "  OK MultivariateSwitcher.spec created" -ForegroundColor Green

# Build executables
Write-Host ""
Write-Host "[5/7] Building executables with PyInstaller..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Cyan
Write-Host ""

# Build AlgoSwitcher
Write-Host "  Building AlgoSwitcher..." -ForegroundColor Cyan
& $pythonCmd -m PyInstaller AlgoSwitcher.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  X AlgoSwitcher build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  OK AlgoSwitcher built successfully" -ForegroundColor Green

# Build StabilizationSwitcher
Write-Host "  Building StabilizationSwitcher..." -ForegroundColor Cyan
& $pythonCmd -m PyInstaller StabilizationSwitcher.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  X StabilizationSwitcher build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  OK StabilizationSwitcher built successfully" -ForegroundColor Green

# Build MultivariateSwitcher
Write-Host "  Building MultivariateSwitcher..." -ForegroundColor Cyan
& $pythonCmd -m PyInstaller MultivariateSwitcher.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  X MultivariateSwitcher build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  OK MultivariateSwitcher built successfully" -ForegroundColor Green

Write-Host ""
Write-Host "[6/7] Preparing distribution package..." -ForegroundColor Yellow

# Get short git hash
$gitHash = (& git rev-parse --short HEAD 2>&1)
if ($LASTEXITCODE -ne 0 -or -not $gitHash) {
    $gitHash = "unknown"
}

# Rename executables with hash
$exeName1 = "AlgoSwitcher_$gitHash.exe"
$exePath1 = "dist\$exeName1"
if (Test-Path "dist\AlgoSwitcher.exe") {
    Rename-Item "dist\AlgoSwitcher.exe" $exeName1 -Force
    $fileSize1 = (Get-Item $exePath1).Length / 1MB
    Write-Host "  OK AlgoSwitcher executable: $exeName1 ($([math]::Round($fileSize1, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "  X AlgoSwitcher executable not found!" -ForegroundColor Red
    exit 1
}

$exeName2 = "StabilizationSwitcher_$gitHash.exe"
$exePath2 = "dist\$exeName2"
if (Test-Path "dist\StabilizationSwitcher.exe") {
    Rename-Item "dist\StabilizationSwitcher.exe" $exeName2 -Force
    $fileSize2 = (Get-Item $exePath2).Length / 1MB
    Write-Host "  OK StabilizationSwitcher executable: $exeName2 ($([math]::Round($fileSize2, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "  X StabilizationSwitcher executable not found!" -ForegroundColor Red
    exit 1
}

$exeName3 = "MultivariateSwitcher_$gitHash.exe"
$exePath3 = "dist\$exeName3"
if (Test-Path "dist\MultivariateSwitcher.exe") {
    Rename-Item "dist\MultivariateSwitcher.exe" $exeName3 -Force
    $fileSize3 = (Get-Item $exePath3).Length / 1MB
    Write-Host "  OK MultivariateSwitcher executable: $exeName3 ($([math]::Round($fileSize3, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "  X MultivariateSwitcher executable not found!" -ForegroundColor Red
    exit 1
}

# Find and extract eyetracker-service version
Write-Host ""
Write-Host "[7/7] Creating distribution package..." -ForegroundColor Yellow

$eyetrackerFile = Get-ChildItem "$ScriptDir\eyetracker_to_test" -Filter "eyetracker-service-*-win64-Release.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
$eyetrackerVersion = $null
if ($eyetrackerFile) {
    # Extract version from filename: eyetracker-service-<version>-win64-Release.exe
    if ($eyetrackerFile.Name -match "eyetracker-service-([\d.]+)-win64-Release\.exe") {
        $eyetrackerVersion = $matches[1]
        Write-Host "  Found eyetracker-service version: $eyetrackerVersion" -ForegroundColor Cyan
    }
}

# Create zip package with executables and instructions
$versionSuffix = if ($eyetrackerVersion) { "_et$eyetrackerVersion" } else { "" }
$zipName = "EyeTrackerTools_$gitHash$versionSuffix.zip"
$zipPath = "$ScriptDir\$zipName"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

# Prepare temp folder for packaging
$packageDir = "$ScriptDir\package_temp"
if (Test-Path $packageDir) { Remove-Item $packageDir -Recurse -Force }
New-Item -ItemType Directory -Path $packageDir | Out-Null

# Copy all executables
Copy-Item $exePath1 $packageDir\
Copy-Item $exePath2 $packageDir\
Copy-Item $exePath3 $packageDir\
Write-Host "  OK Added all executables to package" -ForegroundColor Green

# Copy abtesting instructions (all xlsx files)
if (Test-Path "$ScriptDir\abtesting_instructions") {
    New-Item -ItemType Directory -Path "$packageDir\abtesting_instructions" | Out-Null
    Copy-Item "$ScriptDir\abtesting_instructions\*.xlsx" "$packageDir\abtesting_instructions\"
    Write-Host "  OK Added abtesting instructions to package" -ForegroundColor Green
}

# Copy README.md
if (Test-Path "$ScriptDir\README.md") {
    Copy-Item "$ScriptDir\README.md" "$packageDir\"
    Write-Host "  OK Added README.md to package" -ForegroundColor Green
}

# Copy eyetracker-service executable
if ($eyetrackerFile) {
    New-Item -ItemType Directory -Path "$packageDir\eyetracker_to_test" | Out-Null
    Copy-Item $eyetrackerFile.FullName "$packageDir\eyetracker_to_test\"
    Write-Host "  OK Added eyetracker-service to package" -ForegroundColor Green
}

Compress-Archive -Path "$packageDir\*" -DestinationPath $zipPath
Remove-Item $packageDir -Recurse -Force

Write-Host "" 
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "" 
Write-Host "Your package is ready at:" -ForegroundColor White
Write-Host "  $zipPath" -ForegroundColor Cyan
Write-Host "" 
Write-Host "Package includes:" -ForegroundColor White
Write-Host "  1. AlgoSwitcher - Toggle between MEDIAPIPE and BLINKEYE + A/B Testing" -ForegroundColor Gray
Write-Host "  2. StabilizationSwitcher - Configure eye stabilization parameters" -ForegroundColor Gray
Write-Host "  3. MultivariateSwitcher - Multivariate testing (algorithm + stabilization)" -ForegroundColor Gray
if ($eyetrackerFile) {
    Write-Host "  4. eyetracker-service executable (v$eyetrackerVersion)" -ForegroundColor Gray
}
Write-Host "" 
Write-Host "You can now:" -ForegroundColor White
Write-Host "  1. Distribute the zip file ($zipName)" -ForegroundColor Gray
Write-Host "  2. Unzip and run the executables" -ForegroundColor Gray
Write-Host "  3. Note: Run as Administrator for full functionality" -ForegroundColor Yellow
Write-Host "" 
