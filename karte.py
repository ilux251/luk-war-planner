from tkinter import *

def key_press(e):
  if e.keysym == "Right":
    canvas.xview_scroll

def scroll_start(event):
    canvas.scan_mark(event.x, event.y)

def scroll_move(event):
    canvas.scan_dragto(event.x, event.y, gain=1)

karte = Tk()

karte.title("Karte")
karte.geometry("800x800")

canvas = Canvas(karte, scrollregion=(-2000, -1000, 1000, 1000), background="grey")
canvas.pack(fill="both", expand=True)

canvas.create_rectangle(800, 50, 850, 100, fill="red")
canvas.bind("<ButtonPress-1>", scroll_start)
canvas.bind("<B1-Motion>", scroll_move)


karte.mainloop()