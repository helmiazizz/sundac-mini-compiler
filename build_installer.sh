#!/usr/bin/env bash
# =============================================================================
# build_installer.sh
# Skrip pikeun ngabungkus SUNDAC (kompiler) jadi hiji executable mandiri
# (installer) ngagunakeun PyInstaller.
#
# Pamakean (Linux / macOS):
#   bash build_installer.sh
#
# Pamakean (Windows, jalankeun dina PowerShell / CMD anu geus aya Python):
#   pip install pyinstaller
#   python -m PyInstaller --onefile --name sundac --distpath build\dist --workpath build\work --specpath build src\main.py
#
# Hasilna: hiji file executable mandiri di build/dist/
#   - Linux/macOS : build/dist/sundac
#   - Windows     : build\dist\sundac.exe
#
# Executable ieu BISA dijalankeun di komputer lian anu TEU kainstal Python
# sama sakali, sabab sakabéh runtime Python geus dibungkus di jerona.
# =============================================================================

set -e

echo "[1/3] Mariksa / masang PyInstaller ..."
pip install --break-system-packages -q pyinstaller || pip install -q pyinstaller

echo "[2/3] Ngabangun executable 'sundac' ..."
python3 -m PyInstaller --onefile --name sundac \
  --distpath build/dist --workpath build/work --specpath build \
  src/main.py

echo "[3/3] Beres! Executable aya di: build/dist/sundac"
echo ""
echo "Conto pamakean sanggeus dibangun:"
echo "  ./build/dist/sundac run examples/02_fungsi_prima.sun"
