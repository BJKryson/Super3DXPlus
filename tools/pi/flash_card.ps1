<#
Writes a raspberry Pi OS Lite image (the .img, unpacked from the .img.xz) to an SD card from Windows and checks it by reading it back.
Needs an elevated PowerShell. It refuses anything that is not a USB/SD disk of exactly the size you give it, so a wrong
disk number cannot wipe a system disk, and it asks you to type the size back.

  powershell -ExecutionPolicy Bypass -File tools\pi\flash_card.ps1 -Image C:\path\raspios.img -Disk 4 -SizeBytes 31914983424

Find the disk number and size with:  Get-Disk | ? BusType -eq USB
#>
param([Parameter(Mandatory)][string]$Image, [Parameter(Mandatory)][int]$Disk, [Parameter(Mandatory)][long]$SizeBytes)
$ErrorActionPreference = 'Stop'
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'run this from an elevated PowerShell' }
$d = Get-Disk -Number $Disk
if ($d.BusType -ne 'USB' -or $d.Size -ne $SizeBytes) { throw "disk $Disk is $($d.BusType), $($d.Size) bytes: not the card you named" }
Write-Host "About to ERASE disk $Disk : $($d.FriendlyName), $($d.Size) bytes, serial $($d.SerialNumber)"
if ((Read-Host 'type the size in bytes to go ahead') -ne "$SizeBytes") { throw 'not confirmed' }
Clear-Disk -Number $Disk -RemoveData -RemoveOEM -Confirm:$false
$len = (Get-Item $Image).Length
$phys = "\\.\PhysicalDrive$Disk"
$buf = New-Object byte[] (4MB)
$in = [IO.File]::OpenRead($Image)
$out = New-Object IO.FileStream($phys, 'Open', 'ReadWrite', 'None', 1MB)
[long]$done = 0
while (($n = $in.Read($buf, 0, $buf.Length)) -gt 0) {
  $m = [int]([math]::Ceiling($n / 512.0) * 512)
  if ($m -gt $n) { [Array]::Clear($buf, $n, $m - $n) }
  $out.Write($buf, 0, $m)
  $done += $n
  if (($done / 4MB) % 50 -lt 1) { Write-Host ('{0:N0} / {1:N0} MB' -f ($done / 1MB), ($len / 1MB)) }
}
$out.Flush(); $out.Close(); $in.Close()
Write-Host 'written; verifying'
# read both back and compare (a Windows disk is read in whole sectors)
$a = [IO.File]::OpenRead($Image); $b = New-Object IO.FileStream($phys, 'Open', 'Read', 'ReadWrite', 1MB)
$buf2 = New-Object byte[] (4MB)
$h1 = [Security.Cryptography.SHA256]::Create(); $h2 = [Security.Cryptography.SHA256]::Create()
[long]$left = $len; $bad = $false
while ($left -gt 0) {
  $use = [int][math]::Min([long]$buf.Length, $left)
  $n1 = $a.Read($buf, 0, $use)
  $n2 = $b.Read($buf2, 0, [int]([math]::Ceiling($use / 512.0) * 512))
  if ($n1 -le 0 -or $n2 -lt $n1) { $bad = $true; break }
  [void]$h1.TransformBlock($buf, 0, $n1, $null, 0); [void]$h2.TransformBlock($buf2, 0, $n1, $null, 0)
  $left -= $n1
}
[void]$h1.TransformFinalBlock($buf, 0, 0); [void]$h2.TransformFinalBlock($buf, 0, 0)
$a.Close(); $b.Close()
if ($bad -or [BitConverter]::ToString($h1.Hash) -ne [BitConverter]::ToString($h2.Hash)) { Write-Host 'MISMATCH: write the card again, or try another card'; exit 1 }
Write-Host 'FLASH VERIFIED'
