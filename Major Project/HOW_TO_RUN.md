# How to Run SmartAttend

## ⚡ Easiest Way (Recommended)

Double-click **`start.bat`** in the project folder. Done.

---

## Terminal Methods

### Option 1 — PowerShell (VS Code terminal, Windows Terminal)

```powershell
cd "c:\Users\ROHAN KUMAR\OneDrive\Desktop\Major Project\Major Project"
powershell -ExecutionPolicy Bypass -File start.ps1
```

Or if you're already in the project folder:
```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

### Option 2 — Command Prompt (CMD)

```cmd
cd "c:\Users\ROHAN KUMAR\OneDrive\Desktop\Major Project\Major Project"
start.bat
```

### Option 3 — Manually with venv

**PowerShell:**
```powershell
cd "c:\Users\ROHAN KUMAR\OneDrive\Desktop\Major Project\Major Project"
.\venv\Scripts\Activate.ps1
python run.py
```

**CMD:**
```cmd
cd "c:\Users\ROHAN KUMAR\OneDrive\Desktop\Major Project\Major Project"
venv\Scripts\activate
python run.py
```

---

## ⚠️ Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `venv\Scripts\activate cannot be loaded` | Use **Option 1 or 2** above. PowerShell blocks `.ps1` by default — that's why `start.bat` is easier. |
| `No module named flask` | You're using the wrong Python. Always use `venv\Scripts\python.exe` not system python. |
| `Address already in use` | Server is already running. Close it first or restart your terminal. |
| `venv not found` | Run `setup_windows.bat` first to set up the environment. |

---

## After Starting

1. Open your browser and go to **http://127.0.0.1:5000**
2. Log in with demo credentials:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@university.edu | admin123 |
| Teacher | sharma@university.edu | teacher123 |
| Student | rohan@student.edu | student123 |

3. Press **CTRL+C** in the terminal to stop the server.

---

## First Time Setup?

If this is your first time running the project, run this first:
```cmd
setup_windows.bat
```
This will create the virtual environment, install all packages, and seed the database.
