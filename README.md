# Texture Map Generator

This repository contains a Tkinter-based GUI application for generating common texture maps (AO, Roughness, Normal, etc.) from source images. The interface now features a dark theme and tabbed previews for a modern look.

## Structure

- `texture_map_generator/`
  - `processing.py` – image processing utilities.
  - `app.py` – main GUI application.
- `main.py` – entry point to run the application.
- `import MaxPlus.py` – previous example script kept for reference.

## Usage

Run the application with:

```bash
python main.py
```

Drag-and-drop images onto the window or use the "Выбрать изображение(я)" button. `ttk` styling provides a polished experience. Adjust parameters and save the generated maps.