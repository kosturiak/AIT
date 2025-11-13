# Použi oficiálny základný obraz pre Python 3.11
FROM python:3.11-slim

# Nastav pracovný adresár vnútri kontajnera
WORKDIR /app

# Skopíruj "nákupný zoznam" a nainštaluj knižnice
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skopíruj zvyšok aplikácie (app.py a info.txt)
COPY . .

# Spusti gunicorn server s 5-minútovým (300s) timeoutom
# (predvolený bol 30s, čo bolo málo)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "300", "app:app"]


