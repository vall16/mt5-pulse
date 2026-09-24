# 1️⃣ Usa Python 3.11.9 come base
FROM python:3.11.9-slim

# 2️⃣ Imposta la working directory dentro il container
WORKDIR /code

# 3️⃣ Installa i build tools necessari (psutil su ARM)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 4️⃣ Copia requirements.txt e installa dipendenze
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5️⃣ Copia tutto il codice del progetto
COPY . .

# 6️⃣ Espone la porta usata dal backend
EXPOSE 8080

# 7️⃣ Comando per avviare lo script
CMD ["python", "run_multi_instances.py"]
