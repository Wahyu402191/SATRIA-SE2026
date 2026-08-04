<#
SATRIA SE2026 - Pasang auto-start
Badan Pusat Statistik Kabupaten Bangkalan

Mendaftarkan Jalankan_SATRIA_SE2026.bat supaya otomatis jalan setiap kali
komputer ini dinyalakan/restart, lewat Windows Task Scheduler bawaan
(tidak perlu install software pihak ketiga apa pun).

Cara pakai: klik kanan file ini -> "Run with PowerShell" -> pilih "Yes"
kalau diminta izin Administrator. Cukup dijalankan SEKALI saja.
#>

#Requires -RunAsAdministrator

$ErrorActionPreference = 'Stop'

$taskName = 'SATRIA SE2026 - Auto Start'
$scriptDir = $PSScriptRoot
$batPath = Join-Path $scriptDir 'Jalankan_SATRIA_SE2026.bat'

if (-not (Test-Path $batPath)) {
    Write-Host "[GAGAL] Tidak ketemu $batPath" -ForegroundColor Red
    Write-Host "Pastikan file ini ada di folder yang sama dengan Jalankan_SATRIA_SE2026.bat"
    exit 1
}

# Idempotent: hapus dulu task lama dengan nama yang sama kalau ada, supaya
# skrip ini aman dijalankan berkali-kali tanpa bikin duplikat.
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Task '$taskName' sudah ada, mendaftar ulang..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $scriptDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Berhasil! SATRIA SE2026 akan otomatis jalan setiap kali" -ForegroundColor Green
Write-Host "  komputer ini dinyalakan." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Catatan: task ini jalan saat user '$env:USERNAME' login."
Write-Host "Kalau mau komputer langsung jalankan server tanpa perlu ada"
Write-Host "yang login dulu, hubungi IT untuk ubah task ini jadi jalan"
Write-Host "sebagai SYSTEM lewat Task Scheduler (taskschd.msc)."
Write-Host ""
Read-Host "Tekan Enter untuk menutup"
