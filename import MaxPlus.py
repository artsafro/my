import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os


class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обработка изображений")
        self.image_paths = []

        # Режим обработки: одно или пакетное
        self.processing_mode = tk.StringVar(value="single")

        # Радио-кнопки режима
        tk.Radiobutton(root, text="Одно изображение", variable=self.processing_mode,
                       value="single", command=self.update_mode).pack(anchor="w", padx=20)
        tk.Radiobutton(root, text="Пакетная обработка", variable=self.processing_mode,
                       value="batch", command=self.update_mode).pack(anchor="w", padx=20)

        # Кнопки
        self.select_button = tk.Button(root, text="Выбрать изображение", command=self.select_images)
        self.select_button.pack(pady=10)

        self.process_button = tk.Button(root, text="Обработать изображение", command=self.process_images)
        self.process_button.pack(pady=10)

        # Область превью с прокруткой
        self.preview_container = tk.Frame(root)
        self.preview_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.preview_container)
        self.scrollbar = tk.Scrollbar(self.preview_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # При изменении окна перерисовываем
        self.root.bind('<Configure>', self.on_window_resize)

    def update_mode(self):
        if self.processing_mode.get() == "batch":
            self.select_button.config(text="Выбрать изображения")
        else:
            self.select_button.config(text="Выбрать изображение")
            self.image_paths = []
            self.display_thumbnails()

    def select_images(self):
        if self.processing_mode.get() == "batch":
            paths = filedialog.askopenfilenames(filetypes=[("PNG Files", "*.png")])
            if paths:
                self.image_paths = paths
                self.display_thumbnails()
        else:
            path = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")])
            if path:
                self.image_paths = [path]
                self.display_thumbnails()

    def display_thumbnails(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Сетка: 6 колонок, 4 строки
        cell_size = 128
        columns = 6
        total_slots = 24

        images = []
        for path in self.image_paths[:total_slots]:
            try:
                img = Image.open(path)
                img.thumbnail((cell_size - 20, cell_size - 20))
                img_tk = ImageTk.PhotoImage(img)
                images.append(img_tk)
            except:
                images.append(None)

        for index in range(total_slots):
            row = index // columns
            col = index % columns

            frame = tk.Frame(self.scrollable_frame, width=cell_size, height=cell_size,
                             bg="white", highlightbackground="red", highlightthickness=1)
            frame.grid(row=row, column=col, padx=5, pady=5)
            frame.grid_propagate(False)

            if index < len(images) and images[index]:
                label = tk.Label(frame, image=images[index], bg="white")
                label.image = images[index]
                label.place(relx=0.5, rely=0.5, anchor="center")

    def on_window_resize(self, event):
        if self.image_paths:
            self.display_thumbnails()

    def process_images(self):
        if not self.image_paths:
            messagebox.showwarning("Нет изображений", "Пожалуйста, выберите изображение(я).")
            return

        save_folder = filedialog.askdirectory(title="Куда сохранить")
        if not save_folder:
            return

        for path in self.image_paths:
            try:
                img = Image.open(path)
                if img.mode != 'RGBA':
                    raise ValueError("Нет альфа-канала")

                alpha = img.split()[3]
                bw_alpha = alpha.point(lambda p: 255 if p > 128 else 0)

                base_name = os.path.basename(path).replace('.png', '_alpha.png')
                save_path = os.path.join(save_folder, base_name)
                bw_alpha.save(save_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"{os.path.basename(path)}: {e}")

        messagebox.showinfo("Готово", "Обработка завершена.")


# Запуск
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    app = ImageProcessorApp(root)
    root.mainloop()
