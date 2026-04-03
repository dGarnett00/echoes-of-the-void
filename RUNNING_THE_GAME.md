# Running Echoes of the Void

This guide explains exactly how to launch the game locally.

## Quick Way

After cloning the repo, just run:

```bash
python play.py
```

This automatically installs dependencies and starts the game. For manual setup, continue reading below.

## 1) Prerequisites

- Python 3.8+
- `pip` available in your terminal

Check your Python version:

```powershell
python --version
```

If that does not work, try:

```powershell
py --version
```

## 2) Open the project folder

```powershell
cd path\to\echoes-of-the-void
```

## 3) (Recommended) Create and activate a virtual environment

Create:

```powershell
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If your system blocks script execution, run this once in PowerShell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again.

## 4) Install dependencies

```powershell
pip install -r requirements.txt
```

## 5) Run the game

```powershell
python run.py
```

If `python` is not recognized, use:

```powershell
py run.py
```

## 6) Optional: run tests

```powershell
pytest tests/ -v
```

## Common issues

- `ModuleNotFoundError`: Make sure dependencies are installed in the active environment.
- `python not found`: Use `py` instead of `python` on Windows.
- Colors not showing correctly: Use Windows Terminal or PowerShell and ensure `colorama` is installed.
