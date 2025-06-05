from __future__ import annotations

import os
from typing import List, Tuple

import cv2
import numpy as np
import dearpygui.dearpygui as dpg

from .processing import generate_map, generate_combined_map


# ---------------------------------------------------------------------------
# state
images: List[np.ndarray] = []
image_paths: List[str] = []
save_dir: str = ""


# ---------------------------------------------------------------------------
# helpers

def _apply_diffuse_adjustments(
    img: np.ndarray,
    brightness: float,
    contrast: float,
    tint_strength: float,
    tint_color: Tuple[int, int, int],
    brightness_enabled: bool,
    contrast_enabled: bool,
    tint_enabled: bool,
) -> np.ndarray:
    """Apply brightness/contrast/tint adjustments to a diffuse map."""
    b = brightness if brightness_enabled else 1.0
    c = contrast if contrast_enabled else 1.0
    t = tint_strength if tint_enabled else 0.0

    img_adj = cv2.convertScaleAbs(img[:, :, :3], alpha=c, beta=(b - 1) * 255)
    tint = np.full_like(img_adj, tint_color, dtype=np.uint8)
    return cv2.addWeighted(img_adj, 1 - t, tint, t, 0)


# ---------------------------------------------------------------------------
# callbacks

def _load_images_callback(sender, app_data):
    global images, image_paths
    image_paths = list(app_data["selections"].values())
    images = []
    for path in image_paths:
        data = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
        if img is None:
            continue
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        images.append(img)
    _update_preview()

def _select_save_dir_callback(sender, app_data):
    global save_dir
    save_dir = app_data["file_path_name"]


def _update_preview(sender=None, app_data=None, user_data=None):
    if not images:
        return
    img = images[0]
    brightness = dpg.get_value("brightness") / 100.0
    contrast = dpg.get_value("contrast") / 100.0
    tint_strength = dpg.get_value("tint_strength") / 100.0
    tint_color = tuple(int(c * 255) for c in dpg.get_value("tint_color")[:3])
    b_en = dpg.get_value("brightness_enabled")
    c_en = dpg.get_value("contrast_enabled")
    t_en = dpg.get_value("tint_enabled")

    preview = _apply_diffuse_adjustments(
        img,
        brightness,
        contrast,
        tint_strength,
        tint_color,
        b_en,
        c_en,
        t_en,
    )
    data = (preview.astype(np.float32) / 255.0).flatten()
    dpg.set_value("preview_texture", data)
    dpg.configure_item("preview_texture", width=preview.shape[1], height=preview.shape[0])


def _generate(action: str):
    if not images or not save_dir:
        return

    invert_green = dpg.get_value("invert_green")
    metallic_enabled = dpg.get_value("metallic_enabled")
    emissive_enabled = dpg.get_value("emissive_enabled")
    emissive_color = tuple(int(c * 255) for c in dpg.get_value("emissive_color")[:3])

    strengths = {}
    for key in [
        "Opacity",
        "AO",
        "Roughness",
        "Normal",
        "Displacement",
        "Metallic",
        "Emissive",
    ]:
        strengths[key] = dpg.get_value(f"strength_{key}") / 100.0

    for img, path in zip(images, image_paths):
        base = os.path.splitext(os.path.basename(path))[0]
        if action in {"ORM", "ERM"}:
            combined = generate_combined_map(
                action,
                img,
                strengths,
                invert_green=invert_green,
                metallic_enabled=metallic_enabled,
                emissive_enabled=emissive_enabled,
                emissive_color=emissive_color,
            )
            cv2.imwrite(
                os.path.join(save_dir, f"{base}_{action}.png"),
                cv2.cvtColor(combined, cv2.COLOR_RGB2BGR),
            )
        else:
            map_list = [
                "Diffuse",
                "AO",
                "Roughness",
                "Normal",
                "Displacement",
                "Metallic",
                "Emissive",
            ]
            if img.shape[2] == 4:
                map_list.insert(1, "Opacity")
            for map_type in map_list:
                if map_type == "Diffuse":
                    m = _apply_diffuse_adjustments(
                        img,
                        dpg.get_value("brightness") / 100.0,
                        dpg.get_value("contrast") / 100.0,
                        dpg.get_value("tint_strength") / 100.0,
                        tuple(int(c * 255) for c in dpg.get_value("tint_color")[:3]),
                        dpg.get_value("brightness_enabled"),
                        dpg.get_value("contrast_enabled"),
                        dpg.get_value("tint_enabled"),
                    )
                else:
                    m = generate_map(
                        map_type,
                        img,
                        strengths.get(map_type, 0.5),
                        invert_green=invert_green,
                        metallic_enabled=metallic_enabled,
                        emissive_enabled=emissive_enabled,
                        emissive_color=emissive_color,
                    )
                cv2.imwrite(
                    os.path.join(save_dir, f"{base}_{map_type}.png"),
                    cv2.cvtColor(m, cv2.COLOR_RGB2BGR),
                )


# ---------------------------------------------------------------------------
# UI setup

def run() -> None:
    dpg.create_context()

    with dpg.texture_registry(show=False):
        dpg.add_dynamic_texture(1, 1, [1, 1, 1], tag="preview_texture")

    with dpg.window(label="Controls", width=320, height=700, tag="controls"):
        dpg.add_button(label="Open Images", callback=lambda: dpg.show_item("load_dialog"))
        dpg.add_button(label="Select Save Folder", callback=lambda: dpg.show_item("save_dialog"))
        dpg.add_separator()
        dpg.add_checkbox(label="Invert Green Channel", tag="invert_green")
        dpg.add_checkbox(label="Metallic Enabled", default_value=True, tag="metallic_enabled")
        dpg.add_checkbox(label="Emissive Enabled", tag="emissive_enabled")
        dpg.add_color_edit("Emissive Color", default_value=(247/255, 247/255, 49/255, 1), no_alpha=True, tag="emissive_color")
        dpg.add_separator()
        dpg.add_text("Diffuse Adjustments")
        dpg.add_slider_int("Brightness", min_value=0, max_value=200, default_value=100, tag="brightness", callback=_update_preview)
        dpg.add_checkbox("Enable Brightness", default_value=True, tag="brightness_enabled", callback=_update_preview)
        dpg.add_slider_int("Contrast", min_value=0, max_value=200, default_value=100, tag="contrast", callback=_update_preview)
        dpg.add_checkbox("Enable Contrast", default_value=True, tag="contrast_enabled", callback=_update_preview)
        dpg.add_slider_int("Tint Strength", min_value=0, max_value=100, default_value=50, tag="tint_strength", callback=_update_preview)
        dpg.add_checkbox("Enable Tint", default_value=True, tag="tint_enabled", callback=_update_preview)
        dpg.add_color_edit("Tint Color", default_value=(1, 1, 1, 1), no_alpha=True, tag="tint_color", callback=_update_preview)
        dpg.add_separator()
        dpg.add_text("Map Strengths")
        for key in ["Opacity", "AO", "Roughness", "Normal", "Displacement", "Metallic", "Emissive"]:
            dpg.add_slider_int(key, min_value=0, max_value=100, default_value=50, tag=f"strength_{key}")
        dpg.add_separator()
        dpg.add_button(label="Generate Maps", callback=lambda: _generate("maps"))
        dpg.add_button(label="Create ORM", callback=lambda: _generate("ORM"))
        dpg.add_button(label="Create ERM", callback=lambda: _generate("ERM"))

    with dpg.window(label="Preview", pos=(340, 10)):
        dpg.add_image("preview_texture")

    with dpg.file_dialog(directory_selector=False, show=False, callback=_load_images_callback, tag="load_dialog"):
        dpg.add_file_extension("Image Files (*.png *.jpg *.jpeg){.png,.jpg,.jpeg}")

    with dpg.file_dialog(directory_selector=True, show=False, callback=_select_save_dir_callback, tag="save_dialog"):
        pass

    dpg.create_viewport(title="Texture Map Generator", width=1200, height=720)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("controls", True)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    run()
