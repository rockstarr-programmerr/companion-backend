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
#### Create user
Open django shell and create user
```
python manage.py shell

>>> from django.contrib.auth import get_user_model
>>> get_user_model().objects.create_user(<your username>, password=<your password>)
>>> exit()
```

Go to this URL in your brower, login with the user you created.
```
http://localhost:8000/api-auth/login/
```

### Test
Run unittests:
```
python manage.py test
```
