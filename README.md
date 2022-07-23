# cardabot-api
A REST API for the CardaBot application.

## Install

This API requires `python=3.10.5`, `npm` and `nodejs`.

Create and activate a python virtual environment (recommended):

```
python3 -m venv env/
source env/bin/activate
```

Install requirements:
```
python -m pip install -r requirements.txt
```

## Install Tailwind modules

```
cd cardabot_api/payment/static_src
npm i
npm i daisyui
cd ../../../
python manage.py tailwind install
```


## Run
Execute the cardano-api application and the reloader server:
```
python manage.py runserver 
python manage.py tailwind start
```