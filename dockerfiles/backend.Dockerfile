FROM python:3.10-slim

WORKDIR /backend

# Install system dependencies required by OpenCV and DeepFace
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

COPY ../backend/requirements.txt ./

RUN pip install -r requirements.txt

ENV TF_ENABLE_ONEDNN_OPTS=0

COPY ./backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

