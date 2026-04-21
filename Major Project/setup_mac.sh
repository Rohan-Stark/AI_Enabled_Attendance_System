#!/bin/bash
# ────────────────────────────────────────────────────────
#  SmartAttend — macOS/Linux Setup Script
# ────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo "  SmartAttend — macOS/Linux Setup"
echo "============================================"
echo ""

# ── Find Python 3.10+ ─────────────────────────────────
PYTHON_CMD=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v $cmd &>/dev/null; then
        VERSION=$($cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)
        if [ "$MAJOR" = "3" ] && [ "$MINOR" -ge "10" ]; then
            PYTHON_CMD=$cmd
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] Python 3.10+ not found. Install via: brew install python@3.12"
    exit 1
fi
echo "[OK] Found Python: $PYTHON_CMD ($($PYTHON_CMD --version))"

# ── Create virtual environment ─────────────────────────
if [ -f "venv/bin/python" ]; then
    echo "[OK] Virtual environment already exists"
else
    echo "[..] Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "[OK] Virtual environment created"
fi

# ── Upgrade pip ────────────────────────────────────────
echo "[..] Upgrading pip..."
venv/bin/python -m pip install --upgrade pip "setuptools<71" wheel >/dev/null 2>&1
echo "[OK] pip upgraded"

# ── Install dlib (compiles from source on macOS) ──────
echo "[..] Installing cmake and dlib (this may take a few minutes)..."
venv/bin/python -m pip install cmake >/dev/null 2>&1
venv/bin/python -m pip install dlib >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[WARN] dlib pip install failed. Try: conda install -c conda-forge dlib"
fi
echo "[OK] dlib installed"

# ── Install remaining requirements ────────────────────
echo "[..] Installing Python dependencies..."
venv/bin/python -m pip install -r requirements.txt >/dev/null 2>&1
echo "[OK] All dependencies installed"

# ── Seed database ─────────────────────────────────────
echo "[..] Seeding database with demo data..."
venv/bin/python database/seed.py
echo ""

# ── Done ──────────────────────────────────────────────
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "  To run the app:"
echo "    source venv/bin/activate"
echo "    python run.py"
echo ""
echo "  Then open: http://127.0.0.1:5000"
echo ""
