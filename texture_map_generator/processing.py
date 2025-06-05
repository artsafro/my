"""Utility functions for texture map generation."""
from __future__ import annotations

import cv2
import numpy as np
from typing import Tuple


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert an RGB tuple to hexadecimal color string."""
    return "#%02x%02x%02x" % rgb


def generate_map(
    map_type: str,
    image: np.ndarray,
    strength: float,
    *,
    invert_green: bool = False,
    metallic_enabled: bool = True,
    emissive_enabled: bool = False,
    emissive_color: Tuple[int, int, int] = (247, 247, 49),
) -> np.ndarray:
    """Generate a texture map from the given image.

    Parameters
    ----------
    map_type:
        Type of texture map to generate (Diffuse, AO, etc.).
    image:
        Source image as a NumPy array in RGB[A] format.
    strength:
        Map generation strength in the range [0, 1].
    invert_green:
        Invert green channel for normal maps.
    metallic_enabled:
        If False, Metallic maps return a black image.
    emissive_enabled:
        If False, Emissive maps return a black image.
    emissive_color:
        Fill color for emissive maps when enabled.
    """
    if map_type == "Opacity" and image.shape[2] == 4:
        alpha = image[:, :, 3]
        binary = np.where(alpha > 0, 255, 0).astype(np.uint8)
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)

    gray = cv2.cvtColor(image[:, :, :3], cv2.COLOR_RGB2GRAY)

    if map_type == "AO":
        ao = cv2.equalizeHist(gray)
        ao = cv2.GaussianBlur(ao, (0, 0), 3)
        return cv2.cvtColor(cv2.addWeighted(gray, 1 - strength, ao, strength, 0), cv2.COLOR_GRAY2RGB)

    if map_type == "Roughness":
        inv = cv2.bitwise_not(gray)
        inv = cv2.convertScaleAbs(inv, alpha=1 + strength * 2)
        return cv2.cvtColor(inv, cv2.COLOR_GRAY2RGB)

    if map_type == "Normal":
        f_gray = gray.astype(np.float32) / 255.0
        dx = cv2.Sobel(f_gray, cv2.CV_32F, 1, 0, ksize=3)
        dy = cv2.Sobel(f_gray, cv2.CV_32F, 0, 1, ksize=3)
        if invert_green:
            dy = -dy
        dz = np.ones_like(f_gray) * strength
        normal = np.stack((-dx, -dy, dz), axis=2)
        norm = np.linalg.norm(normal, axis=2, keepdims=True)
        normal /= norm + 1e-5
        normal = (normal * 0.5 + 0.5) * 255
        return normal.astype(np.uint8)

    if map_type == "Displacement":
        disp = cv2.convertScaleAbs(gray, alpha=1 + strength * 2)
        return cv2.cvtColor(disp, cv2.COLOR_GRAY2RGB)

    if map_type == "Metallic":
        if not metallic_enabled:
            return np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
        metallic_map = cv2.cvtColor(image[:, :, :3], cv2.COLOR_RGB2GRAY)
        metallic_map = cv2.convertScaleAbs(metallic_map, alpha=strength * 2)
        return cv2.cvtColor(metallic_map, cv2.COLOR_GRAY2RGB)

    if map_type == "Emissive":
        if not emissive_enabled:
            return np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
        emissive = np.full((image.shape[0], image.shape[1], 3), emissive_color, dtype=np.uint8)
        return emissive

    if map_type == "Diffuse":
        return image[:, :, :3]

    return image[:, :, :3]
