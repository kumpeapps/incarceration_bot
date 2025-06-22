FROM python:3.11.9-slim
ENV PYTHONUNBUFFERED=1
COPY . /app
WORKDIR /app

RUN pip install aiohttp==3.10.11
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "main.py" ]