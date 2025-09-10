<#
Build a one-directory distribution (folder with EXE + libs) using PyInstaller.

Usage (PowerShell):
  pwsh -File scripts/build_onedir.ps1

Requirements:
  - Python with pip, PyInstaller installed (script will install if missing)
  - Run from repo root (where main.py is)
#>

param(
  [string]$Python = "py",
  [string]$Name = "PDF a PPTX",
  [string]$Icon = "icon.ico"
)

$ErrorActionPreference = 'Stop'

Write-Host "==> Checking PyInstaller..."
try {
  & $Python -m PyInstaller --version | Out-Null
} catch {
  Write-Host "Installing PyInstaller..."
  & $Python -m pip install --upgrade pip setuptools wheel | Out-Null
  & $Python -m pip install pyinstaller | Out-Null
}

Write-Host "==> Cleaning previous builds..."
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist

$cmd = @(
  '-m','PyInstaller',
  '--name', $Name,
  '--noconsole',
  '--onedir',
  '--clean',
  '--collect-all','fitz',        # PyMuPDF
  '--collect-all','pptx',        # python-pptx
  '--collect-all','flet',        # Flet assets
  'main.py'
)

if (Test-Path $Icon) {
  $cmd += @('--icon', $Icon)
}

Write-Host "==> Running PyInstaller (onedir)..."
& $Python $cmd

Write-Host "==> Done. Output at: dist\$Name\"
Write-Host "   Run: dist\\$Name\\$Name.exe"
