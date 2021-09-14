# Companion backend

## Develop

### Python version
3.9

### Create virtual environment
```
python -m venv .venv
```

### Activate virtual environment
```
.venv\Scripts\activate
```

### Install dependencies
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Migrate database
```
python manage.py migrate
```

### Run development server
```
python manage.py runserver
```

### Debug
#### For Visual studio code
Just press F5 (Config is inside `.vscode/`)

#### For other editors
Please contribute if you know how.

### Config environment variables
Default variables should work out of the box already, but in case you want to customize, here is how.

Add `.env` file and write your custom variables to it.

Available variables and their data type can be seen in `companion/settings.py`:
```
env = environ.Env(
    ...  # Variables are listed here
)
```

### Browsable API
You can login to the browsable API and explore it to help with development.
#### Collect static
```
python manage.py collectstatic
```

#### Browse!
Go to this URL in your brower. (You may need to register new user and then login if you haven't already)
```
http://localhost:8000/
```

### Test
#### Run unittests
```
python manage.py test
```

#### Run coverage
```
coverage run
```

#### Get coverage report as html
```
coverage html
```
Your report is inside `htmlcov` directory.

## Production

### Browsable API
In production, only staff users can access browsable API.

To create staff user:
```
python manage.py createsuperuser
```
