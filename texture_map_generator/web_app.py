from __future__ import annotations

import base64
from typing import Dict, List, Tuple

import cv2
import numpy as np
from flask import Flask, render_template, request

from .processing import generate_map


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


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            files = request.files.getlist('images')
            results: List[Dict[str, Dict[str, str]]] = []

            brightness = float(request.form.get('brightness', 100)) / 100.0
            contrast = float(request.form.get('contrast', 100)) / 100.0
            tint_strength = float(request.form.get('tint_strength', 50)) / 100.0
            tint_color_hex = request.form.get('tint_color', '#ffffff').lstrip('#')
            tint_color = tuple(int(tint_color_hex[i:i+2], 16) for i in (0, 2, 4))
            brightness_enabled = request.form.get('brightness_enabled') == 'on'
            contrast_enabled = request.form.get('contrast_enabled') == 'on'
            tint_enabled = request.form.get('tint_enabled') == 'on'

            invert_green = request.form.get('invert_green') == 'on'
            metallic_enabled = request.form.get('metallic_enabled') == 'on'
            emissive_enabled = request.form.get('emissive_enabled') == 'on'
            emissive_hex = request.form.get('emissive_color', '#f7f731').lstrip('#')
            emissive_color = tuple(int(emissive_hex[i:i+2], 16) for i in (0, 2, 4))

            strengths = {}
            for key in ['Opacity', 'AO', 'Roughness', 'Normal', 'Displacement', 'Metallic', 'Emissive']:
                strengths[key] = float(request.form.get(f'strength_{key}', 50)) / 100.0

            for f in files:
                data = np.frombuffer(f.read(), np.uint8)
                img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
                if img is None:
                    continue
                if img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                    has_alpha = True
                else:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    has_alpha = False

                map_list = [
                    "Diffuse",
                    "AO",
                    "Roughness",
                    "Normal",
                    "Displacement",
                    "Metallic",
                    "Emissive",
                ]
                if has_alpha:
                    map_list.insert(1, "Opacity")

                maps: Dict[str, str] = {}
                for map_type in map_list:
                    if map_type == 'Diffuse':
                        m = _apply_diffuse_adjustments(
                            img,
                            brightness,
                            contrast,
                            tint_strength,
                            tint_color,
                            brightness_enabled,
                            contrast_enabled,
                            tint_enabled,
                        )
                    else:
                        strength = strengths.get(map_type, 0.5)
                        m = generate_map(
                            map_type,
                            img,
                            strength,
                            invert_green=invert_green,
                            metallic_enabled=metallic_enabled,
                            emissive_enabled=emissive_enabled,
                            emissive_color=emissive_color,
                        )
                    _, buf = cv2.imencode('.png', cv2.cvtColor(m, cv2.COLOR_RGB2BGR))
                    maps[map_type] = base64.b64encode(buf).decode('utf-8')
                results.append({'name': f.filename, 'maps': maps})
            return render_template('result.html', results=results)
        return render_template('index.html')

    return app
