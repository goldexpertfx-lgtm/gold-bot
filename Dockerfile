FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Is line se Render ko token milega
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
