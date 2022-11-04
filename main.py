import tkinter as tk
from tkinter import ttk
import random
import math


def zobrazSkupiny():
    zobrazenie = tk.Tk()
    root.title("Rozdelenie do skupín")
    ziaci = list()
    for i in range(pocetZiakov.get()):
        ziaci.append(i + 1)
    random.shuffle(ziaci)
    skupina = list()
    posuvnik = 1
    skup = 1
    while posuvnik <= pocetZiakov.get():
        if skup > pocetSkupin.get():
            skup = 1
        skupina.append(skup)
        skup += 1
        posuvnik += 1
    for i in range(pocetSkupin.get()):
        aktualnaSkup = list()
        while True:
            try:
                ind = skupina.index(i + 1)
                aktualnaSkup.append(ziaci[0])
                ziaci.pop(0)
                skupina.pop(ind)
            except ValueError:
                ttk.Label(zobrazenie, text=f"Skupina {i + 1}: {aktualnaSkup}", font=("Arial", 50)).pack()
                break


root = tk.Tk()

root.title('Rozdelenie žiakov')
ttk.Label(root, text='Počet žiakov', font=("Arial", 25)).pack()

pocetZiakov = tk.IntVar()
fieldPocetZiakov = ttk.Entry(root, textvariable=pocetZiakov, font=("Arial", 25))
fieldPocetZiakov.pack()

ttk.Label(root, text='Počet skupín', font=("Arial", 25)).pack()

pocetSkupin = tk.IntVar()
fieldPocetSkupin = ttk.Entry(root, textvariable=pocetSkupin, font=("Arial", 25))
fieldPocetSkupin.pack()

ttk.Button(
    root,
    text="Zobraziť rozdelenie",
    command=zobrazSkupiny
).pack()

root.mainloop()
