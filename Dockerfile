# Použi oficiálny základný obraz pre Python 3.11
FROM python:3.11-slim

# Nastav pracovný adresár vnútri kontajnera
WORKDIR /app

# Skopíruj "nákupný zoznam" (requirements_ait.txt) 
# a premenuj ho na "requirements.txt", aby ho pip našiel
COPY requirements_ait.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Skopíruj mozog agenta (app_ait.py) 
# a premenuj ho na "app.py", aby ho gunicorn našiel
COPY app_ait.py app.py

# Skopíruj bázu znalostí
COPY info_ait.txt info_ait.txt

# Spusti gunicorn server s 5-minútovým (300s) timeoutom
# (predvolený bol 30s, čo bolo málo)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "300", "app:app"]
