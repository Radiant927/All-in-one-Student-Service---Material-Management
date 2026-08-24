FROM python:3.12-slim

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY alembic.ini ./alembic.ini

WORKDIR /app/backend
EXPOSE 8000

CMD ["sh", "-c", "alembic -c /app/alembic.ini upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
