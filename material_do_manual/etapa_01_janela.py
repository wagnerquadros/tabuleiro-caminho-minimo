"""Etapa 1: uma janela e uma área de desenho."""
import tkinter as tk


def main():
    root = tk.Tk()
    root.title("Etapa 1 - Janela")
    canvas = tk.Canvas(root, width=612, height=408, bg="#15243a")
    canvas.pack(padx=16, pady=16)
    root.mainloop()


if __name__ == "__main__":
    main()
