FROM python:3.12-slim

WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/app.py .

EXPOSE 5000

ENV ENVIRONMENT=production

CMD ["python", "app.py"]
