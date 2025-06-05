# Texture Map Generator

This repository contains a desktop application for generating common texture maps (AO, Roughness, Normal, etc.) from source images. The interface is built with Dear PyGui and provides a dark theme.

## Structure

- `texture_map_generator/`
  - `processing.py` – image processing utilities.
  - `dpg_app.py` – Dear PyGui desktop interface.
  - `web_app.py` – (legacy) Flask web interface.
  - `templates/` – HTML templates for the old web UI.
- `main.py` – entry point to run the application.
- `requirements.txt` – Python dependencies.

## Usage

Install dependencies and run the application:

```bash
pip install -r requirements.txt
python main.py
```

Launch the program and use the file dialogs to load images and choose an output folder.
Sliders update a live preview in real time for the first selected image.
Use the **Generate Maps** button for individual maps, or the **Create ORM** / **Create ERM**
buttons to produce combined maps. Multiple images are processed in batch and saved to the selected folder.
