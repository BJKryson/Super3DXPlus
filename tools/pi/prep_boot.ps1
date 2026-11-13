<#
Prepares a freshly flashed Pi OS card's boot partition (the FAT one Windows can write) from Windows, elevated:
 - 480i NTSC composite output (the config.txt and cmdline.txt settings that work on a Pi 5; see docs/PI.md), or with -Hdmi none of it
   (the HDMI output: install the game with tools/pi/install.sh ... --hdmi),
 - a one-time first-boot script (systemd.run=, run as root before the normal boot) that makes your user, enables SSH, installs
   your SSH key and removes the setup wizard that waits for a keyboard and screen. (Trixie ignores userconfig.txt and the
   cloud-init user-data of the image, which is why this goes through the kernel command line.)

  powershell -ExecutionPolicy Bypass -File tools\pi\prep_boot.ps1 -Disk 4 -SizeBytes 31914983424 -PublicKey $HOME\.ssh\id_ed25519.pub -PasswordHash '$6$...'

-PasswordHash is a crypt(3) SHA-512 hash:  openssl passwd -6 'yourpassword'  (WSL has openssl). The user is called wmmt;
change -User and the matching paths in platform/pi/files/wmmt.service together if you want another name.
#>
param([Parameter(Mandatory)][int]$Disk, [Parameter(Mandatory)][long]$SizeBytes, [Parameter(Mandatory)][string]$PublicKey,
      [Parameter(Mandatory)][string]$PasswordHash, [string]$User = 'wmmt', [switch]$Hdmi)
$ErrorActionPreference = 'Stop'
$d = Get-Disk -Number $Disk
if ($d.BusType -ne 'USB' -or $d.Size -ne $SizeBytes) { throw "disk $Disk is not the card you named" }
$p = Get-Partition -DiskNumber $Disk -PartitionNumber 1
if (-not $p.DriveLetter) { Add-PartitionAccessPath -DiskNumber $Disk -PartitionNumber 1 -AccessPath 'R:\' }
$R = (Get-Partition -DiskNumber $Disk -PartitionNumber 1).AccessPaths | ? { $_ -match '^[A-Z]:\\$' } | Select -First 1
if (-not (Test-Path "$R\config.txt")) { throw "no config.txt on $R : is this a Pi OS card?" }
$nl = "`n"
$files = Join-Path (Split-Path $PSScriptRoot -Parent) '..\platform\pi\files'
# composite output (not with -Hdmi): the overlay with the composite option, and the connector's mode on the command line
$cfg = [IO.File]::ReadAllText("$R\config.txt")
if (-not $Hdmi -and $cfg -notmatch 'composite') {
  $cfg = $cfg -replace '(?m)^dtoverlay=vc4-kms-v3d\s*$', 'dtoverlay=vc4-kms-v3d,composite'
  $cfg = $cfg.TrimEnd() + "${nl}${nl}# Super3DX+${nl}enable_tvout=1${nl}disable_splash=1${nl}"
  [IO.File]::WriteAllText("$R\config.txt", $cfg)
}
$c = ([IO.File]::ReadAllText("$R\cmdline.txt")).Trim()
if (-not $Hdmi -and $c -notmatch 'Composite-1') { $c += ' video=Composite-1:720x480,tv_mode=NTSC-J drm_rp1_vec.cmode=27000:721/16/64/58,480/6/6/34' }
# the first-boot script
$key = ([IO.File]::ReadAllText($PublicKey)).Trim()
$sh = [IO.File]::ReadAllText((Join-Path $files 'firstrun.sh.in')).Replace('@HASH@', $PasswordHash).Replace('@KEY@', $key).Replace('wmmt', $User).Replace("`r`n", "`n")
[IO.File]::WriteAllText("$R\firstrun.sh", $sh)
if ($c -notmatch 'systemd.run=') { $c += ' systemd.run=/boot/firmware/firstrun.sh systemd.run_success_action=reboot systemd.unit=kernel-command-line.target' }
[IO.File]::WriteAllText("$R\cmdline.txt", $c + $nl)
Write-VolumeCache -DriveLetter $R.Substring(0, 1)
Write-Host "BOOT PREPARED ($R). Put the card in the Pi, plug in Ethernet and power: it reboots once by itself, then ssh $User@<its address>"
