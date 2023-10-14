import os

current_path = os.path.dirname(os.path.abspath(__file__))

import sys
sys.path.insert(0,f"{current_path}/venv_eyetroduit/lib/python3.8/site-packages")
sys.path.insert(0,f"{current_path}")
os.chdir(current_path)

from app import app
application = app
