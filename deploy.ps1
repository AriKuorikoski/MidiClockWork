# deploy.ps1 — Copy all source files to the CIRCUITPY drive.
#
# Usage:
#   .\deploy.ps1           # auto-detect CIRCUITPY drive
#   .\deploy.ps1 D:        # specify drive explicitly

param(
    [string]$Drive = ""
)

# Auto-detect CIRCUITPY drive if not specified
if (-not $Drive) {
    $vol = Get-Volume | Where-Object { $_.FileSystemLabel -eq 'CIRCUITPY' } | Select-Object -First 1
    if (-not $vol) {
        Write-Error "CIRCUITPY drive not found. Is the Pico plugged in with CircuitPython?"
        exit 1
    }
    $Drive = "$($vol.DriveLetter):"
}

Write-Host "Deploying to $Drive..."

$files = @(
    "boot.py",
    "code.py",
    "config.json",
    "config.py",
    "event_bus.py",
    "midi_message.py",
    "midi_input.py",
    "midi_output.py",
    "midi_router.py",
    "midi_clock_tracker.py",
    "uart_writer.py",
    "tempo_to_cc.py",
    "transport_ble.py",
    "transport_usb.py",
    "transport_serial.py",
    "system_builder.py"
)

foreach ($f in $files) {
    Copy-Item "src\$f" "$Drive\$f" -Force
    Write-Host "  $f"
}

Write-Host "Done. CircuitPython will auto-reload."
