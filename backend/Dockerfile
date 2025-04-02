# PATH: backend/Dockerfile

FROM python:3.11

ARG SERVICE_NAME
ARG BACKEND_PORT

ENV SERVICE_NAME=$SERVICE_NAME
ENV BACKEND_PORT=$BACKEND_PORT

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# El puerto interno que escucha uvicorn
EXPOSE 8000

# En modo dev se sobreescribe con debugpy en docker-compose.override
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT"]
