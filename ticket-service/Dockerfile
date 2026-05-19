FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN python -m grpc_tools.protoc -I./app/proto --python_out=./app/proto --grpc_python_out=./app/proto ./app/proto/user.proto

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]