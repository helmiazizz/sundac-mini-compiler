# =============================================================================
# build_installer.ps1
# Versi PowerShell dari build_installer.sh -- membungkus SUNDAC jadi
# satu file executable mandiri (sundac.exe) memakai PyInstaller.
#
# Pemakaian:
#   .\build_installer.ps1
#
# Hasilnya: build\dist\sundac.exe -- bisa dijalankan di komputer Windows
# lain meskipun tidak terinstall Python sama sekali.
# =============================================================================

# -- Deteksi perintah Python yang tersedia (dites beneran, bukan cuma cek nama) --
$PYTHON = $null
foreach ($cand in @("python", "python3", "py")) {
    try {
        $verOutput = (& $cand --version) 2>&1 | Out-String
        if ($verOutput -match "Python \d+\.\d+") {
            $PYTHON = $cand
            break
        }
    } catch {
        # perintah tidak ada / gagal dijalankan, coba kandidat berikutnya
    }
}
if (-not $PYTHON) {
    Write-Host "Python tidak ditemukan di PATH. Install dulu dari https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "Memakai perintah Python: $PYTHON"

Write-Host "[1/3] Memeriksa / memasang PyInstaller ..."
& $PYTHON -m pip install --quiet pyinstaller

Write-Host "[2/3] Membangun executable 'sundac.exe' ..."
& $PYTHON -m PyInstaller --onefile --name sundac `
    --distpath build/dist --workpath build/work --specpath build `
    src/main.py

Write-Host "[3/3] Selesai! Executable ada di: build\dist\sundac.exe"
Write-Host ""
Write-Host "Contoh pemakaian setelah dibangun:"
Write-Host "  .\build\dist\sundac.exe run examples\02_fungsi_prima.sun"
