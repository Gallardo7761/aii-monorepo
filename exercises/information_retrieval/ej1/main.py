import locale
import re
import urllib.request
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import Tk
from tkinter.scrolledtext import ScrolledText
import shutil, re, os

from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD, ID, NUMERIC
from whoosh.qparser import QueryParser
from whoosh import index, qparser, query

DATA_DIR = Path(__file__).parent / "data"
CONTACTS_DIR = DATA_DIR / "contacts"
EMAILS_DIR = DATA_DIR / "emails"
INDEX_DIR = Path(__file__).parent / "index"
CONTACTS = {}

def create_index():
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    
    if not index.exists_in(INDEX_DIR, indexname="EmailIndex"):
        schema = Schema(sender=TEXT(stored=True),
                        receiver=KEYWORD(stored=True),
                        date=DATETIME(stored=True),
                        subject=TEXT(stored=True),
                        body=TEXT(stored=True,phrase=False), 
                        file_name=ID(stored=True))
        idx = create_in(INDEX_DIR, schema=schema, indexname="EmailIndex")
        print(f"Created index: {idx.indexname}")
    else:
        print(f"An index already exists")

def add_to_index(writer, path, file_name):
    try:
        f = open(path, "r")
        sender = f.readline().strip()
        receiver = f.readline().strip()
        date_raw = f.readline().strip()
        date = datetime.strptime(date_raw, '%Y%m%d')
        subject = f.readline().strip()
        body = f.read()
        f.close()           
                
        writer.add_document(
            sender=sender,
            receiver=receiver,
            date=date,
            subject=subject,
            body=body,
            file_name=file_name
        )
    except:
        messagebox.showerror(f"[ERR] adding {path}/{file_name}")

def index_emails(delete = False):
    if delete:
        shutil.rmtree(INDEX_DIR)
        os.mkdir(INDEX_DIR)
        create_index()
        
    idx = index.open_dir(INDEX_DIR, "EmailIndex")
    writer = idx.writer()
    count = 0
    for f in os.listdir(EMAILS_DIR):
        if not os.path.isdir(EMAILS_DIR / f):
            add_to_index(writer, EMAILS_DIR / f, f)
            count += 1
        
    writer.commit()
    return count

def create_contacts():
    try:
        f = open(CONTACTS_DIR / "agenda.txt", "r")
        email = f.readline()
        while email:
            name = f.readline()
            CONTACTS[email.strip()] = name.strip()
            email = f.readline()
    except:
        messagebox.showerror(f"[ERR] creating contacts list")

def load(delete = False):
    create_contacts()
    return index_emails(delete)

class EmailsUI():
    def __init__(self, root, title = "AII"):
        self.root = root
        self.root.title(title)
        self.root.geometry("900x600")
                
        # Menu Principal
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        # Menu Datos
        datos_menu = tk.Menu(self.menu, tearoff=0)
        datos_menu.add_command(label="Cargar", command=lambda: self.callback("load"))
        datos_menu.add_command(label="Listar", command=lambda: self.callback("list"))
        datos_menu.add_separator()
        datos_menu.add_command(label="Salir", command=self.root.quit)
        self.menu.add_cascade(label="Datos", menu=datos_menu)

        # Menu Buscar
        buscar_menu = tk.Menu(self.menu, tearoff=0)
        buscar_menu.add_command(label="Cuerpo o Asunto", command=lambda: self.callback("search_body_or_subject"))
        buscar_menu.add_command(label="Fecha", command=lambda: self.callback("search_date"))
        buscar_menu.add_command(label="Spam", command=lambda: self.callback("search_spam"))
        self.menu.add_cascade(label="Buscar", menu=buscar_menu)

        # Callback externo desde el punto de entrada
        self.callback = None
        
    def show_list(self, items, fields, title="Listado"):
        mw = tk.Toplevel(self.root)
        mw.title(title)
        listbox = tk.Listbox(mw, width=80, height=20)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(mw)
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        for item in items:
            row = " | ".join(str(item.get(field, "Unknown")) for field in fields)
            listbox.insert("end", row)
            
    def ask_text(self, label, callback):
        mw = tk.Toplevel(self.root)
        mw.title(label)
        tk.Label(mw, text=label).pack(pady=5)
        entry = ttk.Entry(mw)
        entry.pack(pady=5)
        ttk.Button(mw, text="Aceptar", command=
                    lambda: [callback(entry.get()), mw.destroy()]).pack(pady=10)   
    
    def ask_spinbox(self, label, options, callback):
        mw = tk.Toplevel(self.root)
        mw.title(label)
        tk.Label(mw, text=label).pack(pady=5)
        spinbox = ttk.Spinbox(mw, values=options, state="readonly", width=40)
        spinbox.pack(pady=5)
        ttk.Button(mw, text="Aceptar", command=
                    lambda: [callback(spinbox.get()), mw.destroy()]).pack(pady=10)
        
    def ask_radiobutton(self, label, options, callback):
        mw = tk.Toplevel(self.root)
        mw.title(label)
        tk.Label(mw, text=label).pack(pady=5)
        sv = tk.StringVar(value=options[0])
        for option in options:
            tk.Radiobutton(mw, text=option, variable=sv, value=option).pack(anchor="w")
        ttk.Button(mw, text="Aceptar", command=
                    lambda: [callback(sv.get()), mw.destroy()]).pack(pady=10)
        
    def info(slef, message):
        messagebox.showinfo("Información", message)

def main():
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
    
    create_index()
    root = Tk()
    ui = EmailsUI(root)

    def handle_action(action):
        match(action):
            case "load":
                resp = messagebox.askyesno(title="Cargar", message="Quieres cargar todos los datos de nuevo?")
                if resp:
                    recipes_count = load(True)
                    ui.info(f"Se han indexado {recipes_count} emails")
            case "list":
                ix = open_dir(INDEX_DIR, "EmailIndex")
                with ix.searcher() as searcher:
                    emails = searcher.search(query.Every(), limit=None)
                    print(emails)
                    ui.show_list(emails, ["sender", "receiver", "name", "subject", "body"])
            # buscar con queries y tal...
           
    ui.callback = handle_action
    root.mainloop()
    
if __name__ == "__main__":
    main()
    