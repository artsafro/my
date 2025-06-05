from __future__ import annotations

import os
from typing import List

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, Scrollbar, Canvas, colorchooser, ttk
import tkinterdnd2 as tkdnd
from PIL import Image, ImageTk
from PIL.Image import Resampling

from .processing import generate_map, rgb_to_hex


class TextureMapApp:
    """GUI application for generating various texture maps."""

    def __init__(self, root: tk.Misc) -> None:
        self.root = root
        self.root.title("Texture Map Generator")
        self.root.geometry("1920x1080")

        self.image_paths: List[str] = []
        self.save_path: str = ""
        self.original_images: List[np.ndarray] = []
        self.map_widgets: dict = {}
        self.tint_color = (255, 255, 255)
        self.emissive_color = (247, 247, 49)
        self.invert_green = tk.BooleanVar(value=False)
        self.save_res = tk.StringVar(value="original")
        self.metallic_enabled = tk.BooleanVar(value=True)
        self.emissive_enabled = tk.BooleanVar(value=False)

        self.setup_ui()

    # ------------------------------------------------------------------ UI setup
    def setup_ui(self) -> None:
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Выбрать изображение(я)", command=self.select_images).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Выбрать папку сохранения", command=self.select_save_path).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Сохранить все карты", command=self.save_all_maps).pack(side="left", padx=5)

        tk.Label(btn_frame, text="Сохр. размер:").pack(side="left")
        ttk.Combobox(btn_frame, textvariable=self.save_res, values=["original", "2048", "4096"], width=7).pack(side="left", padx=5)
        tk.Checkbutton(btn_frame, text="Инвертировать зелёный канал Normal", variable=self.invert_green).pack(side="left", padx=10)
        tk.Checkbutton(btn_frame, text="Metallic материал", variable=self.metallic_enabled).pack(side="left", padx=10)

        emissive_frame = tk.Frame(btn_frame)
        emissive_frame.pack(side="left", padx=10)
        tk.Checkbutton(emissive_frame, text="Emissive", variable=self.emissive_enabled, command=self.update_all_emissives).pack(side="left")
        tk.Button(emissive_frame, text="Цвет Emissive", command=self.select_emissive_color).pack(side="left")
        self.emissive_preview = tk.Label(emissive_frame, width=3, height=1, bg=rgb_to_hex(self.emissive_color), relief="ridge")
        self.emissive_preview.pack(side="left", padx=5)

        self.canvas = Canvas(self.root, scrollregion=(0, 0, 5000, 5000))
        self.h_scrollbar = Scrollbar(self.root, orient="horizontal", command=self.canvas.xview)
        self.v_scrollbar = Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)

        self.h_scrollbar.pack(side="bottom", fill="x")
        self.v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.preview_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.preview_frame, anchor="nw")
        self.preview_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.root.drop_target_register(tkdnd.DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

    # ----------------------------------------------------------------- callbacks
    def select_images(self) -> None:
        paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not paths:
            return

        self.image_paths = list(paths)
        self.original_images = [
            cv2.cvtColor(cv2.imread(p, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA if p.lower().endswith('.png') else cv2.COLOR_BGR2RGB)
            for p in paths
        ]
        self.display_all_previews()

    def select_save_path(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.save_path = path

    def on_drop(self, event: tk.Event) -> None:
        files = self.root.tk.splitlist(event.data)
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        self.image_paths = image_files
        self.original_images = [
            cv2.cvtColor(cv2.imread(p, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA if p.lower().endswith('.png') else cv2.COLOR_BGR2RGB)
            for p in image_files
        ]
        self.display_all_previews()

    # --------------------------------------------------------------- Preview area
    def display_all_previews(self) -> None:
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        self.map_widgets.clear()

        for idx, img in enumerate(self.original_images):
            maps = {}
            frame = tk.LabelFrame(self.preview_frame, text=os.path.basename(self.image_paths[idx]), padx=10, pady=10)
            frame.pack(padx=10, pady=10, fill="x")

            map_list = ["Diffuse", "AO", "Roughness", "Normal", "Displacement", "Metallic", "Emissive"]
            if img.shape[2] == 4:
                map_list.insert(1, "Opacity")

            for i, map_type in enumerate(map_list):
                sub = tk.Frame(frame)
                sub.grid(row=i // 3, column=i % 3, padx=10, pady=5)

                map_img = generate_map(
                    map_type,
                    img,
                    0.5,
                    invert_green=self.invert_green.get(),
                    metallic_enabled=self.metallic_enabled.get(),
                    emissive_enabled=self.emissive_enabled.get(),
                    emissive_color=self.emissive_color,
                )
                imgtk = ImageTk.PhotoImage(Image.fromarray(map_img).resize((384, 384)))

                label = tk.Label(sub, image=imgtk)
                label.image = imgtk
                label.pack()

                if map_type == "Diffuse":
                    brightness = tk.Scale(sub, from_=0, to=200, orient="horizontal", label="Яркость", command=lambda val, i=idx: self.update_diffuse(i))
                    contrast = tk.Scale(sub, from_=0, to=200, orient="horizontal", label="Контраст", command=lambda val, i=idx: self.update_diffuse(i))
                    tint_strength = tk.Scale(sub, from_=0, to=100, orient="horizontal", label="Tint %", command=lambda val, i=idx: self.update_diffuse(i))
                    brightness_toggle = tk.BooleanVar(value=True)
                    contrast_toggle = tk.BooleanVar(value=True)
                    tint_toggle = tk.BooleanVar(value=True)
                    tk.Checkbutton(sub, text="B", variable=brightness_toggle, command=lambda i=idx: self.update_diffuse(i)).pack()
                    tk.Checkbutton(sub, text="C", variable=contrast_toggle, command=lambda i=idx: self.update_diffuse(i)).pack()
                    tk.Checkbutton(sub, text="T", variable=tint_toggle, command=lambda i=idx: self.update_diffuse(i)).pack()
                    tint_color_btn = tk.Button(sub, text="Цвет", command=self.select_tint_color)
                    self.color_display = tk.Label(sub, width=3, height=1, bg=rgb_to_hex(self.tint_color), relief="ridge")

                    brightness.set(100)
                    contrast.set(100)
                    tint_strength.set(50)

                    brightness.pack()
                    contrast.pack()
                    tint_color_btn.pack(side="left")
                    self.color_display.pack(side="left", padx=5)
                    tint_strength.pack()

                    maps[map_type] = (
                        label,
                        brightness,
                        contrast,
                        tint_strength,
                        brightness_toggle,
                        contrast_toggle,
                        tint_toggle,
                    )
                else:
                    slider = tk.Scale(
                        sub,
                        from_=0,
                        to=100,
                        orient="horizontal",
                        label=map_type,
                        command=lambda val, i=idx, mt=map_type: self.update_map(i, mt, float(val)),
                    )
                    slider.set(50)
                    slider.pack()
                    maps[map_type] = (label, slider)

            self.map_widgets[idx] = maps

    # ---------------------------------------------------------------- map updates
    def update_map(self, idx: int, map_type: str, val: float) -> None:
        strength = val / 100.0
        img = self.original_images[idx]
        map_img = generate_map(
            map_type,
            img,
            strength,
            invert_green=self.invert_green.get(),
            metallic_enabled=self.metallic_enabled.get(),
            emissive_enabled=self.emissive_enabled.get(),
            emissive_color=self.emissive_color,
        )
        imgtk = ImageTk.PhotoImage(Image.fromarray(map_img).resize((384, 384)))
        label = self.map_widgets[idx][map_type][0]
        label.configure(image=imgtk)
        label.image = imgtk

    def update_diffuse(self, idx: int) -> None:
        img = self.original_images[idx]
        _, brightness, contrast, tint_strength, btog, ctog, ttog = self.map_widgets[idx]["Diffuse"]
        b = brightness.get() / 100.0 if btog.get() else 1.0
        c = contrast.get() / 100.0 if ctog.get() else 1.0
        t = tint_strength.get() / 100.0 if ttog.get() else 0.0

        img_adj = cv2.convertScaleAbs(img[:, :, :3], alpha=c, beta=(b - 1) * 255)
        tint = np.full_like(img_adj, self.tint_color, dtype=np.uint8)
        img_tinted = cv2.addWeighted(img_adj, 1 - t, tint, t, 0)
        imgtk = ImageTk.PhotoImage(Image.fromarray(img_tinted).resize((384, 384)))
        label = self.map_widgets[idx]["Diffuse"][0]
        label.configure(image=imgtk)
        label.image = imgtk

    def update_all_emissives(self) -> None:
        for idx in range(len(self.original_images)):
            self.update_map(idx, "Emissive", 0.5)

    # ---------------------------------------------------------------- color picks
    def select_tint_color(self) -> None:
        color = colorchooser.askcolor()[0]
        if color:
            self.tint_color = tuple(map(int, color))
            self.color_display.config(bg=rgb_to_hex(self.tint_color))
            for idx in range(len(self.original_images)):
                self.update_diffuse(idx)

    def select_emissive_color(self) -> None:
        color = colorchooser.askcolor()[0]
        if color:
            self.emissive_color = tuple(map(int, color))
            self.emissive_preview.config(bg=rgb_to_hex(self.emissive_color))
            self.update_all_emissives()

    # ---------------------------------------------------------- saving utilities
    def save_all_maps(self) -> None:
        if not self.save_path:
            messagebox.showwarning("Ошибка", "Укажите папку для сохранения.")
            return

        for idx, img in enumerate(self.original_images):
            base_name = os.path.splitext(os.path.basename(self.image_paths[idx]))[0]
            for map_type, widgets in self.map_widgets[idx].items():
                if map_type == "Diffuse":
                    _, brightness, contrast, tint_strength, btog, ctog, ttog = widgets
                    b = brightness.get() / 100.0 if btog.get() else 1.0
                    c = contrast.get() / 100.0 if ctog.get() else 1.0
                    t = tint_strength.get() / 100.0 if ttog.get() else 0.0
                    img_adj = cv2.convertScaleAbs(img[:, :, :3], alpha=c, beta=(b - 1) * 255)
                    tint = np.full_like(img_adj, self.tint_color, dtype=np.uint8)
                    result = cv2.addWeighted(img_adj, 1 - t, tint, t, 0)
                else:
                    strength = widgets[1].get() / 100.0
                    result = generate_map(
                        map_type,
                        img,
                        strength,
                        invert_green=self.invert_green.get(),
                        metallic_enabled=self.metallic_enabled.get(),
                        emissive_enabled=self.emissive_enabled.get(),
                        emissive_color=self.emissive_color,
                    )

                if self.save_res.get() in ["2048", "4096"]:
                    res = int(self.save_res.get())
                    result = cv2.resize(result, (res, res), interpolation=cv2.INTER_AREA)

                cv2.imwrite(
                    os.path.join(self.save_path, f"{base_name}_{map_type}.png"),
                    cv2.cvtColor(result, cv2.COLOR_RGB2BGR),
                )

        messagebox.showinfo("Готово", "Все карты сохранены.")


# --------------------------------------------------------------------------- run
if __name__ == "__main__":
    root = tkdnd.TkinterDnD.Tk()
    app = TextureMapApp(root)
    root.mainloop()
