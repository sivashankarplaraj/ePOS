# Django Project Setup

This project uses a Python virtual environment for dependency management.

## Virtual Environment Setup

### Activating the Virtual Environment
```powershell
# Navigate to project directory
cd "c:\Users\sivashankar.palraj\OneDrive - ETI Ltd\Documents-SP\US_App_Work\ePOS"

# Activate virtual environment
.\django_env\Scripts\Activate.ps1
```

### Deactivating the Virtual Environment
```powershell
deactivate
```

### Installing Dependencies
```powershell
# Make sure virtual environment is activated first
pip install -r requirements.txt
```

## Django Project Commands

### Create a new Django project
```powershell
django-admin startproject myproject .
```

### Create a new Django app
```powershell
python manage.py startapp myapp
```

### Run development server
```powershell
python manage.py runserver
```

### Run migrations
```powershell
python manage.py migrate
```

### Create superuser
```powershell
python manage.py createsuperuser
```

## Environment Information
- Python Version: 3.13.5
- Django Version: 5.2.4
- Virtual Environment: django_env

## Daily CSV Exports

You can generate the Daily CSVs (MP, PD, RV) and the weekly VAT snapshot (K_WK_VAT.csv) for any business date.

```powershell
# From the project root, with your virtual environment activated
python manage.py export_daily_csvs --date YYYY-MM-DD --outdir .\exports

# Example: export for today to .\exports_tmp
python manage.py export_daily_csvs --date (Get-Date -Format 'yyyy-MM-dd') --outdir .\exports_tmp
```

This writes the following files into the chosen folder:
- MP<ddmmyy>.CSV
- PD<ddmmyy>.CSV
- RV<ddmmyy>.CSV
- K_WK_VAT.csv (added)

Notes:
- Crew Food and Waste food orders are excluded from VAT totals and their net values are recorded in RV as TSTAFFVAL and TWASTEVAL respectively.
- PD OPTION counts reflect add-on/extra items attached to products; free items selected as part of combos are not added to OPTION.

To quickly inspect aggregated totals without exporting files:

```powershell
# Print KRev totals (and optionally selected KPro rows)
python manage.py inspect_daily --date YYYY-MM-DD
```

## UI tests (Playwright, optional)

End-to-end UI smoke tests use Playwright via pytest. They are skipped by default.

Setup (one-time):

```powershell
pip install -r requirements.txt
python -m playwright install
```

Run smoke test (server must be running locally):

```powershell
$env:EPOS_E2E = "1"       # enable e2e tests
$env:EPOS_BASE_URL = "http://127.0.0.1:8090"  # optional, defaults to this
pytest -m e2e tests/e2e/test_smoke.py -q
```
