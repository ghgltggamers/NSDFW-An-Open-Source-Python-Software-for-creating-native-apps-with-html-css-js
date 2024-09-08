import tkinter as tk
from editor.editor import Editor

def main():
    root = tk.Tk()
    editor = Editor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
