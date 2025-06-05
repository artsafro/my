# Texture Map Generator

This repository contains a web-based application for generating common texture maps (AO, Roughness, Normal, etc.) from source images. The interface uses a dark theme and runs in your browser.

## Structure

- `texture_map_generator/`
  - `processing.py` – image processing utilities.
  - `web_app.py` – Flask web interface.
  - `templates/` – HTML templates for the web UI.
- `main.py` – entry point to run the web application.
- `requirements.txt` – Python dependencies.

## Usage

Install dependencies and run the server:

```bash
pip install -r requirements.txt
python main.py
```

Open `http://localhost:5000` in your browser, upload images and the generated maps will be displayed.
