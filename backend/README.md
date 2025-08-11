# Backend

This directory contains the Python backend application for the incarceration bot.

## Structure

- `main.py` - Main application entry point
- `requirements.txt` - Python dependencies
- `models/` - Data models (Jail, Inmate, Monitor)
- `scrapes/` - Jail scraping modules
- `helpers/` - Utility helpers
- `find_zuercher/` - Zuercher portal discovery tools
- `Dockerfile*` - Docker build files

## Running

### Using Docker

```bash
docker build -t incarceration_bot .
docker run incarceration_bot
```

### Using Python directly

```bash
pip install -r requirements.txt
python main.py
```
