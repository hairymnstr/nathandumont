# Developing

Basic steps to running this code for development.  Tested on Debian 11.

    sudo apt install python3-virtualenv

Next checkout this repository and switch into the directory.

    python3 -m venv djg
    source djg/bin/activate
    python -m pip install -r requirements.txt
    ./manage.py makemigrations blog
    ./manage.py migrate
    ./manage.py runserver

Note that by default there are only nathandumont.com and hairymnstr.com base templates included so you'll have to go into the admin site and alter site ID 1 to have one of these URLs or create your own base template.
