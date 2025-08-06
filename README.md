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
