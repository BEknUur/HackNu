CREATE THE VENV 
python3 -m venv venv 
source venv/bin/activate - >bash 
source venv/bin/activate.fish - > if you are using the fist






RUN THE BACKEND 
uvicorn main:app --reload --host 0.0.0.0 --port 8000
