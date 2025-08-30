FROM python:3.11.9-slim
ENV PYTHONUNBUFFERED=1

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    nano \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to reduce image size
RUN apt-get remove -y gcc g++ make libffi-dev && \
    apt-get autoremove -y && \
    apt-get clean

COPY . /app

CMD [ "python", "main.py" ]