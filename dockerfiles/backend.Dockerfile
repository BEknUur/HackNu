FROM python:3.10-slim

WORKDIR /backend

COPY ../backend/requirements.txt ./

RUN pip install -r requirements.txt

COPY ./backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

