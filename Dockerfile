FROM python:3.12-slim

WORKDIR /app

# Allows docker to cache installed dependencies between builds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# runs the production server
ENTRYPOINT ["python", "manage.py"]
CMD ["runserver", "0.0.0.0:8000"]

VOLUME [ "/app/data" ]
