
# ProjectApp
Custom Software Development Company

# How to Run the Project

## Clone the repository:
```bash
git clone https://github.com/gustavop-dev/projectapp.git
cd projectapp
```

## Install virtualenv:
```bash
pip install virtualenv
```

## Create virtual env:
```bash
virtualenv projectapp_env
```

## Activate virtual env:
```bash
source projectapp_env/bin/activate
```

## Install dependencies:
```bash
pip install -r requirements.txt
```

## Deactivate virtual env:
```bash
deactivate
```

## Run makemigrations:
```bash
python3 manage.py makemigrations
```

## Run migrations:
```bash
python3 manage.py migrate
```

## Create superuser:
```bash
python3 manage.py createsuperuser
```

## Create fake data:
```bash
python3 manage.py create_fake_data
```

## Start the server:
```bash
python3 manage.py runserver
```

## Delete fake data:
```bash
python3 manage.py delete_fake_data
```

## Frontend setup:
```bash
cd frontend
npm install
npm run dev
```

You can also see other examples like reference implementations:

- [Candle Project](https://github.com/carlos18bp/candle_project)
- [Jewel Project](https://github.com/carlos18bp/jewel_project)
- [Dress Rental Project](https://github.com/carlos18bp/dress_rental_project)

If you need an implementation for user login and registration, use:
- [Sign In/Sign On Feature](https://github.com/carlos18bp/signin_signon_feature)
