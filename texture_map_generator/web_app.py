from __future__ import annotations

import base64
import io
from typing import List, Dict

import cv2
import numpy as np
from flask import Flask, render_template, request

from .processing import generate_map


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            files = request.files.getlist('images')
            results: List[Dict[str, Dict[str, str]]] = []
            for f in files:
                data = np.frombuffer(f.read(), np.uint8)
                img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
                if img is None:
                    continue
                if img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                else:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

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

                maps: Dict[str, str] = {}
                for map_type in map_list:
                    m = generate_map(map_type, img, 0.5)
                    _, buf = cv2.imencode('.png', cv2.cvtColor(m, cv2.COLOR_RGB2BGR))
                    maps[map_type] = base64.b64encode(buf).decode('utf-8')
                results.append({'name': f.filename, 'maps': maps})
            return render_template('result.html', results=results)
        return render_template('index.html')

    return app
