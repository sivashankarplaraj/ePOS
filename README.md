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

Notes / Rules implemented:
- MP file now includes the full product catalogue (all `PdItem` rows) with per-day TAKEAWAY/EATIN counts (zero when unsold). It does not list combos.
- PD file includes both products (COMBO=FALSE) and combination products (COMBO=TRUE).
- COMBO column outputs literal TRUE/FALSE (matching legacy format expectations).
- Crew Food and Waste food orders do NOT increment TAKEAWAY/EATIN counts; they increment only STAFF or WASTE respectively and are excluded from VAT. Their NET totals appear in RV as TSTAFFVAL and TWASTEVAL.
- Combination products: compulsory + selected optional + selected free-choice component products increment their own basis counts (TAKEAWAY/EATIN) in PD; none of these count toward OPTION.
- Extras / add-ons priced separately on a product increment basis counts AND OPTION for their own product code.
- Free choices attached to a product do NOT increment OPTION (only paid extras do).
- Combination discount (TDISCNTVA) = Sum(standard prices of compulsory + selected optional components) - combo price, aggregated across orders.
- Meal discount (TMEAL_DISCNT) = (Sum singles standard prices) - (Sum discounted meal component prices) per meal line when positive.

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

## Pull Request Summary (template)

Use this template when creating a PR for the CSV/statistics logic changes:

```
Summary:
	- MP export now lists full product catalogue (zero-filled counts) for the day.
	- PD export writes COMBO as TRUE/FALSE and applies new counting rules:
			* Staff/Waste -> only STAFF/WASTE columns; no basis increment.
			* Extras/add-ons -> basis + OPTION.
			* Free choices (product or combo) -> basis only (combo) or ignored for OPTION (product).
	- VAT pass apportions combo gross across components by standard prices and splits meal VAT by component classes.
	- Crew/Waste VAT excluded; net totals recorded in TSTAFFVAL/TWASTEVAL.
	- Weekly VAT snapshot (K_WK_VAT.csv) added to export set and Zip.
	- Tests added for staff/waste isolation, combo option exclusion, meal discount, VAT basis selection.

Testing:
	- 12 unit tests passing (`python manage.py test manage_orders`).
	- Manual export run for sample date: verified PD/MP/RV/K_WK_VAT structure.

Follow-ups:
	- Add Playwright spec for automated export ZIP validation.
	- Parameterize free-choice allowances for combos if business rules require partial free options.
```
```
