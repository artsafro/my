from texture_map_generator.app import TextureMapApp
import tkinterdnd2 as tkdnd


def main() -> None:
    root = tkdnd.TkinterDnD.Tk()
    app = TextureMapApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
