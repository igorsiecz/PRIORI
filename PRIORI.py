import sys
import threading
import time
from datetime import datetime
from tkinter import filedialog
from scipy.ndimage import distance_transform_edt
from whitebox.whitebox_tools import WhiteboxTools
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import subprocess
from cartopy import crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import rasterio.plot
from matplotlib.patches import Patch
from skimage.morphology import opening, closing, disk
from scipy.ndimage import generic_filter, label, binary_dilation
from functools import lru_cache
import ee
import tkinter as tk
from tkinter.filedialog import askopenfilename
import rasterio
import webview
import requests
import osmnx as ox
from osgeo import ogr, gdal
import geopandas as gpd
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio import CRS
import os
import shutil
import pandas as pd
import rasterio.plot
import numpy as np
from shapely.geometry import Polygon
from rasterio.features import rasterize
from shapely.ops import unary_union
from shapely.geometry import mapping
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
import cairosvg
import io
import img2pdf
import tempfile
import cartopy.io.img_tiles as cimgt
from urllib.error import URLError
import colorsys
from shapely.geometry import box
from skimage.morphology import skeletonize
from matplotlib.lines import Line2D
import matplotlib
import traceback
from pyproj import Transformer
import webbrowser


# Inicializa tema do customtkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Variáveis globais
root_logs = None
log_widget = None
captured_coordinates = None
time_start = None
logs_salvos = []
matplotlib.use('Agg')

# Palheta de cores
azul_escuro = "#003566"
azul_petroleo = "#0077b6"
cinza_escuro = "gray30"
cinza_claro = "#bbbbbb"
azul_claro = "#90e0ef"

# Ícones
loading = "Icons/loading.png"
globe = "Icons/globe.png"
calendar = "Icons/calendar.png"
compass = "Icons/compass.png"
map_ico = "Icons/map.png"
susc = "Icons/susc.png"
pin = "Icons/pin.png"
pasta = "Icons/pasta.png"
pixel = "Icons/pixel.png"
best = "Icons/best.png"
update = "Icons/update.png"
info = "Icons/info.png"
check = "Icons/check.png"
alerta = "Icons/alerta.png"
error = "Icons/error.png"
logo = "Icons/logo_horizontal.png"
logo_ico = "Icons/logo_ico.ico"


spinner_registry: dict[int, callable] = {}
def thread_excepthook(args):
    print("⚠️ Erro capturado em thread", args.thread.name)
    del_pasta("cache")
    del_file("dem_tmp.tif")
    del_file("Flow_accumulation_withnodata.tif")
    del_file(path_geohydro)
    del_file(path_georoads)
    spinner_fn = spinner_registry.pop(args.thread.ident, None)
    if spinner_fn:
        try:
            spinner_fn()
        except Exception:
            pass
    log(error, "FATAL ERROR DETECTED:", color="red")
    log_spacing(f"{args.exc_type}: {args.exc_value}", font_size=13, color="red")
    log_spacing("Please restart the application and send this log to the developer.", font_size=13, color="red")
    traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)
threading.excepthook = thread_excepthook


def on_close(win):
    try:
        ctk.destroy_all()
    except:
        pass
    win.destroy()
    sys.exit()


class Theme:
    BG = "#f0f2f2"
    TEXT = "#2f3438"
    MUTED = "#5d6870"
    ACCENT = "#2a9d8f"
    ACCENT_HOVER = "#238176"
    CARD_BG = "#ffffff"
    CARD_BG_HOVER = "#eef2f2"
    DANGER = "#d9534f"
FONT_TITLE = ("Sans Serif", 40, "bold")
FONT_SUBTITLE = ("Sans Serif", 18)
FONT_CAT = ("Sans Serif", 14, "bold")
FONT_BUTTON = ("Sans Serif", 18, "bold")
FONT_FOOTER = ("Sans Serif", 12)
FONT_BODY = ("Sans Serif", 14)
ICON_DIR = "Icons"
APP_WIDTH, APP_HEIGHT = 1040, 720
APP_NAME = "PRIORI – Flood Operational Risk"
APP_VERSION = "v1.0.0"


def center_window(root, w, h):
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")


def load_image(path, max_height=None, max_side=None):
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    ow, oh = img.size
    if max_height:
        scale = max_height / oh
    elif max_side:
        scale = min(max_side / ow, max_side / oh)
    else:
        scale = 1.0
    nw, nh = int(ow * scale), int(oh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    return ctk.CTkImage(light_image=img, size=(nw, nh))


ABOUT_TEXT = f"""
PRIORI (Protocol for Road Infrastructure Operational Risk due to Inundation)

This software is part of a Master's dissertation (Academic Innovation modality) developed at UFRGS,
with methodological partnership from the University of Birmingham (UoB) and collaboration from LAPAV and IPH laboratories.

Funding: CNPq scholarship and institutional support from Infratest (academic innovation partnership program).

Author / Developer: Civil Eng. Igor Sieczkowski Moreira.

Supervision: Prof. Lélio A. T. Brito (LAPAV / UFRGS) and co-supervision by Prof. Fernando Dornelles (IPH / UFRGS).

Scope: Assess the operational flood risk of road infrastructure assets by integrating susceptibility and vulnerability,
supporting intervention prioritization and resilient planning.

Disclaimer: Initial version ({APP_VERSION}) – under continuous development. Results must be interpreted considering input data quality,
calibration parameters and the accompanying methodological documentation.

Contact: igor.moreira@ufrgs.br
"""

def open_about(parent):
    about = ctk.CTkToplevel(parent)
    about.title("About – PRIORI")
    about.configure(fg_color=Theme.BG)
    w, h = 700, 680
    center_window(about, w, h)
    about.grab_set()
    about.resizable(False, False)
    outer = ctk.CTkFrame(about, fg_color="transparent")
    outer.pack(fill="both", expand=True, padx=30, pady=30)
    outer.grid_columnconfigure(0, weight=1)
    outer.grid_rowconfigure(2, weight=1)
    main_logo_path = os.path.join(ICON_DIR, "logo_horizontal.png")
    logo_img = load_image(main_logo_path, max_height=100)
    if logo_img:
        ctk.CTkLabel(outer, image=logo_img, text="").grid(row=0, column=0, pady=(0, 65))
    title_wrapper = ctk.CTkFrame(outer, fg_color="transparent")
    title_wrapper.grid(row=1, column=0, sticky="ew")
    ctk.CTkLabel(title_wrapper, text="ABOUT", font=("Sans Serif", 26, "bold"), text_color=Theme.TEXT).pack(anchor="w")
    scroll = ctk.CTkScrollableFrame(outer, fg_color="transparent")
    scroll.grid(row=2, column=0, sticky="nsew")
    ctk.CTkLabel(scroll, text=ABOUT_TEXT, font=FONT_BODY, justify="left", text_color=Theme.TEXT, wraplength=600).pack(anchor="w")
    btn_close = ctk.CTkButton(
        outer, text="Close", width=200, height=50, corner_radius=12, font=FONT_BUTTON,
        fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER, command=about.destroy)
    btn_close.grid(row=3, column=0, sticky="e", pady=(18, 0))


def build_hero(root, parent, start_callback, exit_callback):
    hero_wrapper = ctk.CTkFrame(parent, fg_color="transparent")
    hero_wrapper.grid(row=0, column=0, sticky="nsew", padx=(40, 10), pady=(30, 75))
    hero_wrapper.grid_columnconfigure(0, weight=1)
    hero_wrapper.grid_rowconfigure(0, weight=1)
    hero = ctk.CTkFrame(hero_wrapper, fg_color="transparent")
    hero.grid(row=0, column=0, sticky="sw")
    main_logo_path = os.path.join(ICON_DIR, "logo_horizontal.png")
    logo_img = load_image(main_logo_path, max_height=110)
    if logo_img:
        ctk.CTkLabel(hero, image=logo_img, text="").pack(anchor="w", pady=(0, 12))
    tagline = ctk.CTkLabel(hero, text="Operational Flood Risk for Road Infrastructure",
                           font=FONT_SUBTITLE, text_color=Theme.MUTED)
    tagline.pack(anchor="w", pady=(0, 12))
    btns = ctk.CTkFrame(hero, fg_color="transparent")
    btns.pack(anchor="w", pady=(0, 10))
    btn_start = ctk.CTkButton(btns, text="Start Analysis", width=200, height=50,
                              corner_radius=12, font=FONT_BUTTON, fg_color=Theme.ACCENT,
                              hover_color=Theme.ACCENT_HOVER, command=start_callback)
    btn_about = ctk.CTkButton(btns, text="About", width=140, height=50,
                              corner_radius=12, font=FONT_BUTTON, fg_color=Theme.CARD_BG,
                              hover_color=Theme.CARD_BG_HOVER, text_color=Theme.TEXT,
                              command=lambda: open_about(root))
    btn_exit = ctk.CTkButton(btns, text="Exit", width=140, height=50,
                             corner_radius=12, font=FONT_BUTTON, fg_color="#adb5bd",
                             hover_color="#6c757d", text_color="black", command=exit_callback)
    btn_start.grid(row=0, column=0, padx=(0, 12))
    btn_about.grid(row=0, column=1, padx=(0, 12))
    btn_exit.grid(row=0, column=2)
    return hero_wrapper


def build_partners(parent):
    PADDING_RIGHT = 24
    H_SPACE = 8
    CARD_W, CARD_H = 120, 110
    categories = {
        "Universities": [
            ("ufrgs.png", "https://www.ufrgs.br"),
            ("uob.png", "https://www.birmingham.ac.uk/"),
        ],
        "Laboratories": [
            ("lapav.png", "https://www.ufrgs.br/lapav/"),
            ("iph.png", "https://www.ufrgs.br/iph/"),
        ],
        "Departments": [
            ("ppgci.png", "https://www.ufrgs.br/ppgec-ci/"),
            ("engenharia.png", "https://www.ufrgs.br/engenharia"),
        ],
        "Funders": [
            ("cnpq.png", "https://www.gov.br/cnpq/pt-br"),
            ("infratest.png", "https://infratest.com.br/"),
        ],
    }
    wrapper = ctk.CTkFrame(parent, fg_color="transparent")
    wrapper.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(30, 70))
    wrapper.grid_rowconfigure(0, weight=1)
    wrapper.grid_columnconfigure(0, weight=1)
    right_col = ctk.CTkFrame(wrapper, fg_color="transparent")
    right_col.pack(side="right", anchor="se", padx=PADDING_RIGHT, pady=0)

    def bind_card(card, lbl, url):
        def on_enter(_e): card.configure(fg_color=Theme.CARD_BG_HOVER)
        def on_leave(_e): card.configure(fg_color=Theme.CARD_BG)
        def on_click(_e): webbrowser.open(url)
        for w in (card, lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
    for cat, items in categories.items():
        cat_block = ctk.CTkFrame(right_col, fg_color="transparent")
        cat_block.pack(fill="x", anchor="w")
        ctk.CTkLabel(cat_block, text=cat.upper(), font=FONT_CAT, text_color=Theme.MUTED).pack(anchor="w", pady=(14, 6))
        row = ctk.CTkFrame(cat_block, fg_color="transparent")
        row.pack(anchor="w")
        for idx, (icon, url) in enumerate(items):
            p = os.path.join(ICON_DIR, icon)
            img = load_image(p, max_side=70)
            card = ctk.CTkFrame(row, fg_color=Theme.CARD_BG, corner_radius=16, width=CARD_W, height=CARD_H)
            card.pack_propagate(False)
            pad_right = H_SPACE if idx < len(items) - 1 else 0
            card.pack(side="left", padx=(0, pad_right), pady=4)
            if img:
                lbl = ctk.CTkLabel(card, image=img, text="")
                lbl.image = img
                lbl.pack(expand=True)
            else:
                lbl = ctk.CTkLabel(card, text=icon.split('.')[0], font=("Sans Serif", 12), text_color=Theme.TEXT)
                lbl.pack(expand=True)
            bind_card(card, lbl, url)
    return wrapper


def iniciar_fluxo(root):
    print("Iniciando fluxo principal...")


def initialize_tela_inicial():
    ctk.set_appearance_mode("light")
    root = ctk.CTk(fg_color=Theme.BG)
    root.title(APP_NAME)
    center_window(root, APP_WIDTH, APP_HEIGHT)
    root.resizable(False, False)
    ico_path = os.path.join(ICON_DIR, "logo_ico.ico")
    if os.path.exists(ico_path):
        try:
            root.iconbitmap(ico_path)
        except Exception:
            pass
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    build_hero(root, root, start_callback=lambda: iniciar_fluxo(root), exit_callback=lambda: on_close(root))
    build_partners(root)
    footer = ctk.CTkLabel(root, text=f"© 2025 PRIORI – UFRGS / LAPAV  •  {APP_VERSION}", font=FONT_FOOTER, text_color=Theme.MUTED)
    footer.place(relx=0.5, rely=0.985, anchor="s")
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()


def iniciar_fluxo(root_tela_inicial):
    root_tela_inicial.destroy()
    run_start()


def mostrar_tela_logs(north_east_lat, north_east_lng, south_west_lat, south_west_lng):
    BG_COLOR = "#f0f0f0"
    HEADER_BG = "#e0e0e0"
    TITLE_COLOR = "#1d3557"
    SUBTITLE_COLOR = "#343a40"
    ACCENT_COLOR = "#2a9d8f"
    HOVER_COLOR = "#21867a"
    BUTTON_COLOR = "#adb5bd"
    BUTTON_HOVER = "#6c757d"
    FONT_HEADER = ("Sans Serif", 24, "bold")
    FONT_INFO = ("Sans Serif", 12)
    FONT_BUTTON = ("Sans Serif", 14, "bold")
    global root_logs, log_container
    root_logs = ctk.CTk(fg_color=BG_COLOR)
    root_logs.title("PRIORI Execution Log")
    root_logs.iconbitmap(logo_ico)
    w, h = 1180, 720
    root_logs.geometry(f"{w}x{h}")
    root_logs.update_idletasks()
    x = (root_logs.winfo_screenwidth() - w) // 2
    y = (root_logs.winfo_screenheight() - h) // 2
    root_logs.geometry(f"{w}x{h}+{x}+{y}")
    root_logs.grid_rowconfigure(0, weight=0)
    root_logs.grid_rowconfigure(1, weight=1)
    root_logs.grid_rowconfigure(2, weight=0)
    root_logs.grid_columnconfigure(0, weight=1)
    header = ctk.CTkFrame(root_logs, fg_color=HEADER_BG, corner_radius=10)
    header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
    header.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        header,
        text="PRIORI – Flood Risk Report",
        font=FONT_HEADER,
        text_color=TITLE_COLOR
    ).grid(row=0, column=0, pady=(10, 0))
    global time_start
    time_start = datetime.now()
    info = f"Date: {time_start:%d-%m-%Y %H:%M}   •   NE: ({north_east_lat:.6f}, {north_east_lng:.6f})   •   SW: ({south_west_lat:.6f}, {south_west_lng:.6f})"
    ctk.CTkLabel(
        header,
        text=info,
        font=FONT_INFO,
        text_color=SUBTITLE_COLOR
    ).grid(row=1, column=0, pady=(0, 10))
    scroll_frame = ctk.CTkScrollableFrame(root_logs, fg_color="white", corner_radius=10)
    scroll_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
    scroll_frame.grid_columnconfigure(0, weight=1)
    log_container = scroll_frame
    log_spacing(f"Date: {time_start:%d-%m-%Y %H:%M} • NE: ({north_east_lat:.6f}, {north_east_lng:.6f}) • SW: ({south_west_lat:.6f}, {south_west_lng:.6f})")
    log_spacing()
    log(pin, "Susceptibility Calculation", color=azul_escuro, font_size=20, font_weight="bold", icon_size=20)
    log_spacing()
    btn_frame = ctk.CTkFrame(root_logs, fg_color=BG_COLOR)
    btn_frame.grid(row=2, column=0, pady=(0, 20), sticky="ew")
    btn_frame.grid_columnconfigure((0, 1), weight=1)
    btn_export = ctk.CTkButton(
        btn_frame,
        text="Export Report as PDF",
        font=FONT_BUTTON,
        width=180,
        height=50,
        fg_color=ACCENT_COLOR,
        hover_color=HOVER_COLOR,
        text_color="white",
        corner_radius=10,
        command=exportar_logs_completos)
    btn_export.grid(row=0, column=0, padx=20)
    def on_close():
        del_pasta("cache")
        del_file("dem_tmp.tif")
        del_file("Flow_accumulation_withnodata.tif")
        del_file(path_geohydro)
        del_file(path_georoads)
        root_logs.destroy()
        sys.exit()
    root_logs.protocol("WM_DELETE_WINDOW", on_close)
    btn_exit = ctk.CTkButton(
        btn_frame,
        text="Exit",
        font=FONT_BUTTON,
        width=180,
        height=50,
        fg_color=BUTTON_COLOR,
        hover_color=BUTTON_HOVER,
        text_color="black",
        corner_radius=10,
        command=on_close)
    btn_exit.grid(row=0, column=1, padx=20)
    def start_priori_thread():
        time.sleep(0.1)
        threading.Thread(
            target=run_priori,
            args=(north_east_lat, north_east_lng, south_west_lat, south_west_lng),
            daemon=True).start()
    root_logs.after(200, start_priori_thread)
    root_logs.mainloop()


def exportar_logs_completos():
    largura = 595
    margem = 40
    y = margem
    altura_total = 2000
    cores_permitidas = {
        "gray30": (77, 77, 77),
        "gray20": (51, 51, 51),
        "gray10": (26, 26, 26),
        "gray": (128, 128, 128),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "blue": (0, 0, 255),
        "red": (255, 0, 0),
        "green": (0, 128, 0),}
    try:
        fonte_padrao = ImageFont.truetype("arial.ttf", 16)
    except:
        fonte_padrao = ImageFont.load_default()
    imagem = Image.new("RGB", (largura, altura_total), "white")
    draw = ImageDraw.Draw(imagem)
    for log in logs_salvos:
        if log["type"] == "text":
            if os.path.exists(log["icon_path"]):
                try:
                    icon = Image.open(log["icon_path"]).resize((log["icon_size"], log["icon_size"])).convert("RGBA")
                    imagem.paste(icon, (margem, y), icon)
                except:
                    pass
            texto_x = margem + log["icon_size"] + 10
            try:
                fonte = ImageFont.truetype(
                    "arialbd.ttf" if log["font_weight"] == "bold" else "arial.ttf",
                    log["font_size"])
            except:
                fonte = fonte_padrao
            cor = cores_permitidas.get(log.get("color", "black").lower(), (0, 0, 0))
            for linha in log["message"].split("\n"):
                draw.text((texto_x, y), linha, fill=cor, font=fonte)
                y += log["font_size"] + 4
            y += 10
        elif log["type"] == "image":
            try:
                ext = os.path.splitext(log["image_path"])[1].lower()
                if ext == ".svg":
                    png_bytes = cairosvg.svg2png(url=log["image_path"],output_width=log["width"])
                    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
                else:
                    img = Image.open(log["image_path"]).convert("RGB")
                    ratio = log["width"] / img.width
                    img = img.resize((log["width"], int(img.height * ratio)), Image.Resampling.LANCZOS)
                if log["description"]:
                    cor = cores_permitidas.get(log.get("color", "black").lower(), (0, 0, 0))
                    draw.text((margem, y), log["description"], fill=cor, font=fonte_padrao)
                    y += 30
                imagem.paste(img, (margem, y))
                y += img.height + 10
            except Exception as e:
                print(f"[image export error] {e}")
        elif log["type"] == "spacing":
            try:
                fonte = ImageFont.truetype(
                    "arialbd.ttf" if log["font_weight"] == "bold" else "arial.ttf", log["font_size"])
            except:
                fonte = fonte_padrao
            cor = cores_permitidas.get(log.get("color", "black").lower(), (0, 0, 0))
            for linha in log["text"].split("\n"):
                if linha.strip():
                    draw.text((margem, y), linha, fill=cor, font=fonte)
                y += log["font_size"] + 4
            y += 4
        if y > altura_total - 200:
            nova = Image.new("RGB", (largura, altura_total + 2000), "white")
            nova.paste(imagem, (0, 0))
            imagem = nova
            draw = ImageDraw.Draw(imagem)
            altura_total += 2000
    imagem_final = imagem.crop((0, 0, largura, y + margem))
    caminho = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save report as PDF")
    if caminho:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            temp_path = tmp.name
        imagem_final.save(temp_path)
        a4_width_pt, a4_height_pt = img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297)
        dpi = 100
        a4_width_px = int((210 / 25.4) * dpi)
        a4_height_px = int((297 / 25.4) * dpi)
        img = Image.open(temp_path).convert("RGB")
        ratio = a4_width_px / img.width
        new_height = int(img.height * ratio)
        img_resized = img.resize((a4_width_px, new_height), Image.Resampling.LANCZOS)
        canvas_height = max(a4_height_px, new_height)
        canvas = Image.new("RGB", (a4_width_px, canvas_height), "white")
        canvas.paste(img_resized, (0, 0))
        canvas.save("temp_a4.png")
        with open(caminho, "wb") as f:
            f.write(img2pdf.convert("temp_a4.png"))
        os.remove("temp_a4.png")
        print(f"✅ Exported to {caminho}")


def log(icon_path, message, font_size=13, font_weight="normal", icon_size=13, color="gray20"):
    logs_salvos.append({
        "type": "text",
        "icon_path": icon_path,
        "message": message,
        "font_size": font_size,
        "font_weight": font_weight,
        "icon_size": icon_size,
        "color": color})
    def _log_internal():
        try:
            img = Image.open(icon_path).resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, size=(icon_size, icon_size))
            frame = ctk.CTkFrame(log_container, fg_color="white")
            frame.pack(anchor="w", padx=15, pady=5)
            label_icon = ctk.CTkLabel(frame, image=ctk_img, text="")
            label_icon.image = ctk_img
            label_icon.pack(side="left", padx=(5, 10))
            label_msg = ctk.CTkLabel(
                frame,
                text=message,
                anchor="w",
                justify="left",
                wraplength=700,
                font=ctk.CTkFont(size=font_size, weight=font_weight),
                text_color=color)
            label_msg.pack(side="left")
            root_logs.after_idle(scroll_to_end)
        except Exception as e:
            print(f"[log error] {e}")
    try:
        root_logs.after(0, _log_internal)
    except Exception as e:
        print(f"[log schedule error] {e}")


def log_loading(icon_path, message, font_size=12, font_weight="normal", icon_size=12, color="black"):
    rotation_angles = [0, 90, 180, 270]
    current_angle = [0]
    running = [True]
    frame_container = ctk.CTkFrame(log_container, fg_color="white")
    frame_container.pack(anchor="w", padx=15, pady=5)
    root_logs.after_idle(scroll_to_end)
    img = Image.open(icon_path).resize(
        (icon_size, icon_size), Image.Resampling.LANCZOS)
    label_icon = ctk.CTkLabel(frame_container, text="")
    label_icon.pack(side="left", padx=(5, 10))
    label_msg = ctk.CTkLabel(
        frame_container,
        text=message,
        anchor="w",
        justify="left",
        wraplength=700,
        font=ctk.CTkFont(size=font_size, weight=font_weight),
        text_color=color)
    label_msg.pack(side="left")
    def rotate():
        if not running[0]:
            frame_container.destroy()
            return
        angle = rotation_angles[current_angle[0] % len(rotation_angles)]
        rotated = img.rotate(angle)
        ctk_img = ctk.CTkImage(rotated, size=(icon_size, icon_size))
        label_icon.configure(image=ctk_img)
        label_icon.image = ctk_img
        current_angle[0] += 1
        root_logs.after(500, rotate)
    root_logs.after(0, rotate)
    def stop_spinner():
        running[0] = False
    spinner_registry[threading.current_thread().ident] = stop_spinner
    return stop_spinner


def log_spacing(text="\n", font_size=12, font_weight="normal", color="black"):
    logs_salvos.append({
        "type": "spacing",
        "text": text,
        "font_size": font_size,
        "font_weight": font_weight,
        "color": color})
    def _log_spacing_internal():
        try:
            frame = ctk.CTkFrame(log_container, fg_color="white")
            frame.pack(anchor="w", padx=15, pady=2)
            label_msg = ctk.CTkLabel(
                frame,
                text=text,
                anchor="w",
                justify="left",
                wraplength=700,
                font=ctk.CTkFont(size=font_size, weight=font_weight),
                text_color=color)
            label_msg.pack(side="left")
            root_logs.after_idle(scroll_to_end)
        except Exception as e:
            print(f"[log spacing error] {e}")
    try:
        root_logs.after(0, _log_spacing_internal)
    except Exception as e:
        print(f"[log spacing schedule error] {e}")


def log_image(image_path, description=None, width=500):
    logs_salvos.append({
        "type": "image",
        "image_path": image_path,
        "description": description,
        "width": width})
    try:
        ext = os.path.splitext(image_path)[1].lower()
        if ext == ".svg":
            png_bytes = cairosvg.svg2png(url=image_path, output_width=width)
            image = Image.open(io.BytesIO(png_bytes))
        else:
            image = Image.open(image_path)
            width_percent = (width / float(image.size[0]))
            height = int((float(image.size[1]) * float(width_percent)))
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        img_ctk = ctk.CTkImage(light_image=image, size=image.size)
        frame = ctk.CTkFrame(log_container, fg_color="white")
        frame.pack(anchor="w", padx=15, pady=10)
        if description:
            label_desc = ctk.CTkLabel(
                frame,
                text=description,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=cinza_claro)
            label_desc.pack(anchor="w", pady=(0, 5))
        label_img = ctk.CTkLabel(frame, image=img_ctk, text="")
        label_img.image = img_ctk
        label_img.pack(anchor="w")
        root_logs.after_idle(scroll_to_end)
    except Exception as e:
        print(f"[log_image_universal error] {e}")


def scroll_to_end():
    root_logs.update_idletasks()
    log_container._parent_canvas.configure(scrollregion=log_container._parent_canvas.bbox("all"))
    log_container._parent_canvas.yview_moveto(1.0)


def encerrar(janela):
    print("👋 Aplicação encerrada pelo usuário")
    try:
        if hasattr(janela, '_after_id'):
            janela.after_cancel(janela._after_id)
    except Exception:
        pass
    janela.destroy()
    sys.exit()


def del_pasta(pasta):
    if os.path.exists(pasta) and os.path.isdir(pasta):
        shutil.rmtree(pasta)


def del_file(file):
    if os.path.exists(file) and os.path.isfile(file):
        os.remove(file)


def initialize_ee():
    access_granted = False
    while not access_granted:
        try:
            with open('Database/ee_credentials_path.txt', 'r') as file:
                lines = file.readlines()
            service_account = lines[0].strip()
            cred_path = lines[1].strip()
            print("\n🔐 Service Account:", service_account)
            print("📁 Credential Path:", cred_path)
            credentials = ee.ServiceAccountCredentials(service_account, cred_path)
            ee.Initialize(credentials)
            access_granted = True
        except Exception as e:
            access_granted = False
            print("\nFalha na inicialização do Earth Engine:", e)
            print("\nInforme o e-mail vinculado ao Earth Engine API:")
            a = input()
            print("\nSelecione o arquivo JSON com as credenciais do Earth Engine API")
            root = tk.Tk()
            root.report_callback_exception = suppress_tcl_errors
            root.withdraw()
            b = askopenfilename(title="Selecione o arquivo JSON com as credenciais do Earth Engine API")
            root.destroy()
            root.mainloop()
            with open('Database/ee_credentials_path.txt', 'w') as file:
                file.write(f"{a}\n")
                file.write(f"{b}")
            print("\nCredenciais registradas com sucesso")


def suppress_tcl_errors(*args):
    pass


class Api:
    def send_coordinates(self, coordinates):
        global captured_coordinates
        captured_coordinates = coordinates
        webview.windows[0].destroy()


def coordinates():
    if captured_coordinates:
        ne = captured_coordinates['northEast']
        sw = captured_coordinates['southWest']
        print(f"\n📍 Coordenadas capturadas:\n⬜🔼 Nordeste (NE): 🧭 Lat: {ne['lat']:.6f} | Lon: {ne['lng']:.6f}\n🔽⬜ "
              f"Sudoeste (SW): 🧭 Lat: {sw['lat']:.6f} | Lon: {sw['lng']:.6f}")
        north_east_lat_ = float(captured_coordinates['northEast']['lat'])
        north_east_lng_ = float(captured_coordinates['northEast']['lng'])
        south_west_lat_ = float(captured_coordinates['southWest']['lat'])
        south_west_lng_ = float(captured_coordinates['southWest']['lng'])
        return north_east_lat_, north_east_lng_, south_west_lat_, south_west_lng_
    else:
        print("Nenhuma região foi selecionada")
        exit(-1)


def get_copernicus_dem(coord_1, coord_2, coord_3, coord_4, output_dem):
    log(pin, "Digital Elevation Model (DEM)", color="black", font_size=14, font_weight="bold", icon_size=14)
    roi = ee.Geometry.BBox(coord_1, coord_2, coord_3, coord_4)
    dem = ee.ImageCollection("COPERNICUS/DEM/GLO30")
    if dem.size().getInfo() == 0:
        print(f'Não foram encontradas imagens para as coordenadas especificadas')
        exit(-1)
    dem = dem.select(['DEM']).mosaic().clip(roi)
    print("\n⚙️ Iniciando o download do DEM...")
    spinner = log_loading(loading, "Downloading DEM file...")
    download_url = dem.getDownloadURL({
        'scale': 30,
        'region': roi.getInfo()['coordinates'],
        'format': 'GeoTIFF'
    })
    response = requests.get(download_url)
    if response.status_code == 200:
        filename = f'dem_tmp.tif'
        with open(filename, 'wb') as f:
            f.write(response.content)
        spinner()
        print(f'✅ Download realizado com sucesso')
        reproject_dem(output_dem)
    else:
        print(f'Erro ao fazer o download: {response.status_code}')
        exit(-1)


def reproject_dem(output_dem):
    input_dem = os.path.join(os.path.dirname(__file__), "dem_tmp.tif")
    with rasterio.open(input_dem) as src:
        lon, lat = (src.bounds.left + src.bounds.right) / 2, (src.bounds.top + src.bounds.bottom) / 2
        utm_zone = int((lon + 180) // 6) + 1
        hemisphere = 'north' if lat >= 0 else 'south'
        utm_crs = CRS.from_dict({"proj": "utm", "zone": utm_zone, "datum": "WGS84", "south": hemisphere == 'south'})
        print(f"\n🌐 Sistema de projeção selecionado: {utm_crs}")
        transform, width, height = calculate_default_transform(src.crs, utm_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({'crs': utm_crs, 'transform': transform, 'width': width, 'height': height})
        with rasterio.open(output_dem, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=utm_crs,
                    resampling=Resampling.nearest)
    log(map_ico, f"Projection system: {utm_crs}")
    log(pasta, f"File: {output_dem} — Reprojected")


@lru_cache(maxsize=1)
def _load_dem_meta(dem_path):
    with rasterio.open(dem_path) as src:
        return src.crs, src.transform, src.width, src.height


def get_roads_network(bbox_coords, vuln_weights, input_geojson, input_dem, output_raster, output_excel):
    log(pin, "Road Network (OSM Data)", color="black", font_size=14, font_weight="bold", icon_size=14)
    spinner = log_loading(loading, "Downloading road network...")
    print("\n⚙️ Iniciando download da malha viária...")
    tags = {"highway": list(vuln_weights.keys())}
    roads_gdf = ox.features_from_bbox(bbox_coords, tags=tags)
    roads_gdf = roads_gdf[roads_gdf.geometry.type.isin(["LineString", "MultiLineString"])].copy().reset_index(drop=True)
    roads_gdf["burn_id"] = roads_gdf.index + 1
    roads_gdf["highway"] = roads_gdf["highway"].apply(lambda x: x[0] if isinstance(x, list) else x)
    roads_gdf["name"] = roads_gdf.get("name", "").fillna("").replace("", "Sem nome")
    roads_gdf["vuln_weight"] = (roads_gdf["highway"].map(vuln_weights).fillna(1).astype(int))
    df = roads_gdf[["burn_id", "name", "highway", "vuln_weight"]]
    df.to_excel(output_excel, index=False)
    proj, gt, x_size, y_size = _load_dem_meta(input_dem)
    gt = gt.to_gdal()
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(output_raster, x_size, y_size, 1, gdal.GDT_UInt32)
    out_ds.SetGeoTransform(gt)
    out_ds.SetProjection(proj.to_wkt())
    roads_gdf.to_file(input_geojson, driver="GeoJSON")
    src = ogr.Open(input_geojson)
    lyr = src.GetLayer()
    gdal.RasterizeLayer(out_ds, [1], lyr, options=["ATTRIBUTE=burn_id"])
    out_ds, src = None, None
    spinner()
    log(pasta, f"File: {output_raster} — Raster with assigned road IDs")
    log(pasta, f"File: {output_excel} — Road metadata table (ID, name, type, weight)")
    log_spacing()
    print("✅ Malha viária gerada com sucesso")
    return roads_gdf


def calculate_flow_accumulation(dem_path, filled_dem, flow_path, accum_path):
    wbt = WhiteboxTools()
    wbt.set_working_dir(os.getcwd())
    wbt.set_verbose_mode(False)
    dem_path = os.path.abspath(dem_path)
    filled_dem_ = os.path.abspath(filled_dem)
    flow_path_ = os.path.abspath(flow_path)
    accum_path_ = os.path.abspath(accum_path)
    wbt.fill_depressions(dem_path, filled_dem_)
    wbt.d8_pointer(filled_dem_, flow_path_)
    wbt.d8_flow_accumulation(flow_path_, output=accum_path_, pntr=True)
    log(pasta, f"File: {filled_dem} — Filled DEM (depression removal)")
    log(pasta, f"File: {flow_path} — D8 Flow Direction (Pointer)")
    log(pasta, f"File: {accum_path} — Flow Accumulation")
    return accum_path_


def get_hydrographic_network(bbox_coords, input_geojson, input_dem, output_raster):
    log_spacing()
    log(pin, "Hydrographic Network (OSM/HydroSHEDS Data)", color="black", font_size=14, font_weight="bold", icon_size=14)
    spinner = log_loading(loading, "Downloading Hydrographic network...")
    print("\n⚙️ Iniciando o download da hidrografia...")
    gdal.DontUseExceptions()
    tags = {"water": ["river", "lake"], "waterway": ["river", "stream", "canal"]}
    water_bodies = ox.features.features_from_bbox(bbox=bbox_coords, tags=tags)
    water_bodies.to_file(input_geojson, driver="GeoJSON")
    dem_ds = gdal.Open(input_dem)
    geo_transform = dem_ds.GetGeoTransform()
    projection = dem_ds.GetProjection()
    x_res = dem_ds.RasterXSize
    y_res = dem_ds.RasterYSize
    source = ogr.Open(input_geojson)
    layer = source.GetLayer()
    layer.SetAttributeFilter("OGR_GEOMETRY = 'Polygon' OR OGR_GEOMETRY = 'MultiPolygon'")
    target_ds = gdal.GetDriverByName("GTiff").Create(output_raster, x_res, y_res, 1, gdal.GDT_Byte)
    target_ds.SetGeoTransform(geo_transform)
    target_ds.SetProjection(projection)
    gdal.RasterizeLayer(target_ds, [1], layer, burn_values=[1])
    layer.SetAttributeFilter("OGR_GEOMETRY = 'LineString' OR OGR_GEOMETRY = 'MultiLineString'")
    gdal.RasterizeLayer(target_ds, [1], layer, burn_values=[1])
    target_ds, source, dem_ds = None, None, None
    spinner()
    log(pasta, f"File: {output_raster} — Permanent river mask (binary raster)")
    log_spacing()
    print("✅ Hidrografia gerada com sucesso")


def calculate_similarity(accumulated_flow, distances, thr, max_dist):
    max_flow = np.max(accumulated_flow)
    threshold_value = max_flow * (thr / 100)
    filtered_flow_ = np.where(accumulated_flow >= threshold_value, accumulated_flow, 0)
    nonzero_flow = filtered_flow_ > 0
    matching_pixels = np.sum(nonzero_flow & (distances <= max_dist))
    total_nonzero_flow = np.sum(nonzero_flow)
    similarity_percentage = (matching_pixels / total_nonzero_flow) * 100 if total_nonzero_flow > 0 else 0
    return similarity_percentage, filtered_flow_, threshold_value/10


def threshold_streams(accum_path, hidro_path, output_tif, output_img):
    log(pin, "Hydrologic Flow Analysis", color="black", font_size=14, font_weight="bold", icon_size=14)
    spinner = log_loading(loading, "Calibrating flow threshold to match hydrography...")
    print("\n⚙️ Calculando threshold do fluxo acumulado...")
    thresholds = []
    thresholds_values = []
    similarities = []
    best_similarity = -1.0
    best_filtered_flow = None
    best_threshold = None
    best_threshold_value = None
    with rasterio.open(accum_path) as src1:
        fluxo_acumulado = src1.read(1)
        profile = src1.profile
        pixel_size = src1.transform[0]
    with rasterio.open(hidro_path) as src2:
        rede_hidro = src2.read(1)
    max_distance = 1000
    rede_hidro_binaria = rede_hidro > 0
    dists = distance_transform_edt(~rede_hidro_binaria) * pixel_size
    print(f"📐 Tamanho do pixel: {pixel_size}")
    for threshold in np.arange(0.01, 50.01, 0.01):
        similarity, filtered_flow, thr_value = calculate_similarity(fluxo_acumulado, dists, threshold, max_distance)
        thresholds.append(threshold)
        similarities.append(similarity)
        thresholds_values.append(thr_value)
        if similarity > best_similarity:
            best_similarity = similarity
            best_threshold = threshold
            best_threshold_value = thr_value
            best_filtered_flow = filtered_flow.copy()
    with rasterio.open(output_tif, "w", **profile) as dst:
        nodata_value = profile.get('nodata', None)
        if nodata_value is not None:
            best_filtered_flow = np.where(best_filtered_flow == nodata_value, 0, best_filtered_flow)
        profile.pop('nodata', None)
        dst.write(best_filtered_flow.astype(rasterio.float32), 1)
    plt.figure(figsize=(10, 6))
    plt.plot(thresholds, similarities, marker='o', linestyle='-')
    plt.xlabel("Threshold (%)")
    plt.ylabel("Similarity (%)")
    plt.grid()
    plt.savefig(output_img, format="svg")
    print(f"🧠 Melhor threshold: {best_threshold_value:.0f} ({best_threshold:.2f}%) - {best_similarity:.2f}% similar")
    spinner()
    log(pasta, f"File: {output_tif} — Drainage raster (thresholded flow accumulation)")
    log(pixel, f"Pixel size: {pixel_size:.2f} m")
    log(best, f"Best threshold: {best_threshold:.2f}% ({best_threshold_value:.0f}) — {best_similarity:.2f}% match with hydro mask")
    log_image(output_img, description="Flow Threshold Calibration Curve:")


def calculate_HAND(filled_path, drainage_path, output_path):
    log(pin, "Susceptibility Calculation", color="black", font_size=14, font_weight="bold", icon_size=14)
    print("\n⚙️ Calculando o HAND...")
    wbt = WhiteboxTools()
    wbt.set_verbose_mode(False)
    DEM_HAND = os.path.join(os.path.dirname(__file__), filled_path)
    STREAMS_HAND = os.path.join(os.path.dirname(__file__), drainage_path)
    HAND = os.path.join(os.path.dirname(__file__), output_path)
    wbt.elevation_above_stream(dem=DEM_HAND, streams=STREAMS_HAND, output=HAND)
    log(pasta, f"File: {output_path} — Raw HAND values")
    print("✅ HAND calculado com sucesso")


def calcular_mrvbf(dem_path, output_path):
    print("\n⚙️ Calculando o MRVBF...")
    base_dir = os.path.dirname(__file__)
    input_dem = os.path.join(base_dir, dem_path)
    mrvbf_out = os.path.join(base_dir, output_path)
    cmd = ["saga_cmd", "ta_morphometry", "8", "-DEM", input_dem, "-MRVBF", mrvbf_out]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("❌ Erro ao calcular MRVBF com SAGA GIS:")
        print(result.stderr)
        raise RuntimeError("Falha na execução do SAGA GIS.")
    print(f"✅ MRVBF gerado com sucesso")
    log(pasta, f"File: {output_path} — Raw MRVBF values")
    return mrvbf_out


def reclassificar_hand(input_path, output_path):
    print("\n⚙️ Reclassificando HAND em 5 faixas de suscetibilidade...")
    base_dir = os.path.dirname(__file__)
    hand_path = os.path.join(base_dir, input_path)
    hand_class_path = os.path.join(base_dir, output_path)
    with rasterio.open(hand_path) as src:
        hand = src.read(1)
        profile = src.profile
        original_nodata = src.nodata
        classified = np.full_like(hand, 255, dtype=np.uint8)  # 255 = nodata para uint8
        valid_mask = (hand != original_nodata)
        classified[(hand <= 1) & valid_mask] = 5
        classified[(hand > 1) & (hand <= 2) & valid_mask] = 4
        classified[(hand > 2) & (hand <= 4) & valid_mask] = 3
        classified[(hand > 4) & (hand <= 6) & valid_mask] = 2
        classified[(hand > 6) & valid_mask] = 1
        profile.update(dtype=rasterio.uint8, count=1, nodata=255)
    with rasterio.open(hand_class_path, 'w', **profile) as dst:
        dst.write(classified, 1)
    print(f"✅ HAND reclassificado com sucesso")
    log(pasta, f"File: {output_path} — Reclassified HAND (1 to 5)")
    return hand_class_path


def reclassificar_mrvbf(input_path, output_path):
    print("\n⚙️ Reclassificando MRVBF em 5 faixas de suscetibilidade...")
    base_dir = os.path.dirname(__file__)
    mrvbf_path = os.path.join(base_dir, input_path)
    mrvbf_class_path = os.path.join(base_dir, output_path)
    with rasterio.open(mrvbf_path) as src:
        mrvbf = src.read(1)
        profile = src.profile
        original_nodata = src.nodata
        classified = np.full_like(mrvbf, 255, dtype=np.uint8)
        valid_mask = (mrvbf != original_nodata)
        classified[(mrvbf >= 0) & (mrvbf < 1) & valid_mask] = 1
        classified[(mrvbf >= 1) & (mrvbf < 3) & valid_mask] = 2
        classified[(mrvbf >= 3) & (mrvbf < 5) & valid_mask] = 3
        classified[(mrvbf >= 5) & (mrvbf < 8) & valid_mask] = 4
        classified[(mrvbf >= 8) & valid_mask] = 5
        profile.update(dtype=rasterio.uint8, count=1, nodata=255)
    with rasterio.open(mrvbf_class_path, 'w', **profile) as dst:
        dst.write(classified, 1)
    print(f"✅ MRVBF reclassificado com sucesso")
    log(pasta, f"File: {output_path} — Reclassified MRVBF (1 to 5)")
    return mrvbf_class_path


def calcular_indice_ahp(input_path_1, input_path_2, output_path, peso_hand, peso_mrvbf):
    print("\n⚙️ Calculando índice final de suscetibilidade...")
    base_dir = os.path.dirname(__file__)
    hand_path = os.path.join(base_dir, input_path_1)
    mrvbf_path = os.path.join(base_dir, input_path_2)
    output_path_ = os.path.join(base_dir, output_path)
    with rasterio.open(hand_path) as hand_src, rasterio.open(mrvbf_path) as mrvbf_src:
        hand = hand_src.read(1).astype(np.float32)
        mrvbf = mrvbf_src.read(1).astype(np.float32)
        hand_nodata = hand_src.nodata
        mrvbf_nodata = mrvbf_src.nodata
        combined_nodata = 255
        valid_mask = (hand != hand_nodata) & (mrvbf != mrvbf_nodata)
        indice = np.full_like(hand, combined_nodata, dtype=np.float32)
        indice[valid_mask] = (hand[valid_mask] * peso_hand + mrvbf[valid_mask] * peso_mrvbf)
        profile = hand_src.profile
        profile.update(dtype=rasterio.float32, nodata=combined_nodata)
    with rasterio.open(output_path_, 'w', **profile) as dst:
        dst.write(indice, 1)
    print(f"✅ Índice AHP gerado com sucesso")
    log(pasta, f"File: {output_path} — Susceptibility index (continuous values)")
    return output_path_


def reclassificar_indice_ahp(input_path, output_path):
    print("\n⚙️ Reclassificando índice AHP em 5 faixas qualitativas...")
    base_dir = os.path.dirname(__file__)
    indice_path = os.path.join(base_dir, input_path)
    classificado_path = os.path.join(base_dir, output_path)
    with rasterio.open(indice_path) as src:
        indice = src.read(1)
        profile = src.profile
        original_nodata = src.nodata
        classificado = np.full_like(indice, 255, dtype=np.uint8)
        valid_mask = (indice != original_nodata)
        classificado[(indice < 2.0) & valid_mask] = 1
        classificado[(indice >= 2.0) & (indice < 3.0) & valid_mask] = 2
        classificado[(indice >= 3.0) & (indice < 4.0) & valid_mask] = 3
        classificado[(indice >= 4.0) & (indice < 4.5) & valid_mask] = 4
        classificado[(indice >= 4.5) & valid_mask] = 5
        profile.update(dtype=rasterio.uint8, nodata=255, count=1)
    with rasterio.open(classificado_path, 'w', **profile) as dst:
        dst.write(classificado, 1)
    print(f"✅ Índice classificado com sucesso")
    log(pasta, f"File: {output_path} — Reclassified susceptibility (1 to 5)")
    return classificado_path


def smooth_recursive(input_path, output_path, mode_window, selem_radius, min_size_pixels, max_iters, tol_change):
    print("\n⚙️ Suavizando suscetibilidade...")
    with rasterio.open(input_path) as src:
        arr = src.read(1)
        profile = src.profile
        nodata = src.nodata
    selem = disk(selem_radius)
    def mode_filter(a):
        vals, cnts = np.unique(a[a != nodata], return_counts=True)
        return vals[np.argmax(cnts)] if vals.size else nodata
    prev = arr.copy()
    for i in range(1, max_iters + 1):
        spinner = log_loading(loading, f"Smoothing susceptibility ({i}/{max_iters})...")
        arr_mode = generic_filter(prev, mode_filter, size=mode_window, mode='nearest')
        arr_open = opening(arr_mode, selem)
        arr_close = closing(arr_open, selem)
        smoothed = arr_close.copy()
        structure = np.ones((3,3), dtype=int)
        labeled, nfeat = label(smoothed != nodata, structure=structure)
        for rid in range(1, nfeat+1):
            mask = (labeled == rid)
            if mask.sum() < min_size_pixels:
                border = binary_dilation(mask, structure=structure) & (~mask)
                neigh = smoothed[border]
                neigh = neigh[neigh != nodata]
                if neigh.size:
                    vals, cnts = np.unique(neigh, return_counts=True)
                    replacement = vals[np.argmax(cnts)]
                    smoothed[mask] = replacement
        nodatamask = (smoothed == nodata)
        if nodatamask.any():
            labeled_n, nf2 = label(nodatamask, structure=structure)
            for rid in range(1, nf2+1):
                mask = (labeled_n == rid)
                border = binary_dilation(mask, structure=structure) & (~mask)
                neigh = smoothed[border]
                neigh = neigh[neigh != nodata]
                if neigh.size:
                    vals, cnts = np.unique(neigh, return_counts=True)
                    replacement = vals[np.argmax(cnts)]
                    smoothed[mask] = replacement
        changes = np.count_nonzero(prev != smoothed)
        print(f"🔄 Iteração {i}/{max_iters}: pixels alterados = {changes}")
        log(info, f"Iteration {i}/{max_iters}: {changes} pixels updated")
        if tol_change > 0 and changes <= tol_change:
            print("✅ Convergido! Parando as iterações")
            prev = smoothed
            break
        prev = smoothed
        spinner()
    profile.update(dtype=rasterio.uint8, nodata=nodata, count=1)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(prev.astype(rasterio.uint8), 1)
    print("✅ Suavização realizada com sucesso")
    log(pasta, f"File: {output_path} — Smoothed final susceptibility map")
    return prev


def visualizar_suscetibilidade(susc_path_, rios_path_, vias_path_, output_path_):
    print("\n📷 Gerando visualização da suscetibilidade...")
    base_dir = os.path.dirname(__file__)
    susc_path = os.path.join(base_dir, susc_path_)
    rios_path = os.path.join(base_dir, rios_path_)
    vias_path = os.path.join(base_dir, vias_path_)
    output_path = os.path.join(base_dir, output_path_)
    with rasterio.open(susc_path) as src:
        susc_data = src.read(1)
        susc_transform = src.transform
        susc_crs = src.crs
        susc_extent = rasterio.plot.plotting_extent(src)
        susc_nodata = src.nodata
    with rasterio.open(rios_path) as rio_src:
        rios = rio_src.read(1)
    with rasterio.open(vias_path) as via_src:
        vias = via_src.read(1)
    susc_data = np.ma.masked_equal(susc_data, susc_nodata)
    cores = ["#1b5e20", "#a5d6a7", "#ffffb2", "#e6550d", "#a80000"]
    cmap = ListedColormap(cores)
    bounds = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    norm = BoundaryNorm(bounds, cmap.N)
    crs_proj = ccrs.UTM(susc_crs.to_dict()["zone"], southern_hemisphere=susc_crs.to_dict().get("south", False))
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': crs_proj})
    ax.set_extent(susc_extent, crs=crs_proj)
    ax.imshow(susc_data, cmap=cmap, norm=norm, transform=crs_proj, extent=susc_extent, interpolation='nearest', alpha=0.75)
    ax.imshow(np.ma.masked_not_equal(rios, 1), cmap=ListedColormap(["#66ccff"]), alpha=0.8, extent=susc_extent, transform=crs_proj)
    ax.imshow(np.ma.masked_where(vias == 0, vias), cmap=ListedColormap(["#303030"]), alpha=0.6, extent=susc_extent, transform=crs_proj)
    legend_labels = ['Muito Baixa', 'Baixa', 'Moderada', 'Alta', 'Muito Alta', 'Rede Hidrográfica', 'Malha Viária']
    legend_colors = cores + ["#66ccff", "#303030"]
    legend_patches = [Patch(color=cor, label=label) for cor, label in zip(legend_colors, legend_labels)]
    ax.legend(handles=legend_patches, loc='lower right', title='Suscetibilidade')
    gl = ax.gridlines(draw_labels=True, linestyle='--', linewidth=0.5)
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    ax.annotate('N', xy=(0.05, 0.95), xytext=(0.05, 0.87),
                xycoords='axes fraction', textcoords='axes fraction',
                arrowprops=dict(facecolor='white', width=4, headwidth=10),
                ha='center', va='center', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Imagem salva com sucesso")
    log(pasta, f"File: {output_path_} — Preview image of the smoothed susceptibility map")
    log_image(output_path, description="Smoothed Susceptibility Map:")
    log_spacing("\n")


def get_poi_network(bbox_coords, tags_pesos, vehicular_highways, output_geojson, output_excel):
    log(pin, "Vulnerability Calculation", color=azul_escuro, font_size=20, font_weight="bold", icon_size=20)
    log_spacing()
    log(pin, "Critical Infrastructure (Points of Interest - POIs)", color="black", font_size=14, font_weight="bold", icon_size=14)
    spinner = log_loading(loading, "Downloading POIs...")
    print("\n⚙️ Iniciando extração de POIs...")
    tags = {}
    for key,(tag,val,weight) in tags_pesos.items():
        tags.setdefault(tag, []).append(val)
    pois = ox.features_from_bbox(bbox_coords, tags=tags)
    needed = {t for t,_,_ in tags_pesos.values()} | {'bridge','tunnel','highway','name'}
    for col in needed:
        if col not in pois.columns:
            pois[col] = None
    mask_bridge = pois['bridge'].fillna('') == 'yes'
    mask_tunnel = pois['tunnel'].fillna('') == 'yes'
    mask_veh = pois['highway'].isin(vehicular_highways)
    pois = pois.loc[~(((mask_bridge | mask_tunnel) & ~mask_veh))].copy()
    pois['type'] = ''
    pois['weight'] = 0
    for key,(tag,val,weight) in tags_pesos.items():
        sel = pois[tag] == val
        pois.loc[sel,'type'] = key
        pois.loc[sel,'weight'] = weight
    mask_crit = pois['type'].isin(['bridge','tunnel'])
    critical = pois.loc[mask_crit].copy()
    rest = pois.loc[~mask_crit].copy()
    named_rows = []
    for nm, grp in critical.groupby('name'):
        if not nm.strip():
            continue
        geom = unary_union(grp.geometry.tolist())
        named_rows.append({
            'geometry': geom,
            'type':     grp['type'].iat[0],
            'weight':   grp['weight'].iat[0],
            'name':     nm
        })
    lines_gdf = gpd.GeoDataFrame(
        named_rows, geometry='geometry', crs=pois.crs
    ) if named_rows else gpd.GeoDataFrame(
        columns=['geometry','type','weight','name'],
        geometry='geometry', crs=pois.crs)
    pois = pd.concat([rest, lines_gdf], ignore_index=True)
    pois = gpd.GeoDataFrame(pois, geometry='geometry', crs=pois.crs)
    pois = pois.reset_index(drop=True)
    pois['poi_id'] = pois.index + 1
    pois['name'] = pois['name'].fillna('').replace('', 'Sem nome')
    pois[['poi_id','name','type','weight','geometry']].to_file(output_geojson, driver='GeoJSON')
    pois[['poi_id','name','type','weight']].to_excel(output_excel, index=False)
    print("✅ POIs extraídos com sucesso")
    spinner()
    log_spacing("POI categories found:", font_size=13, color="gray20")
    summary = pois['type'].value_counts().sort_index()
    for category, count in summary.items():
        log(info, f"{category.title()}:   {count}")
    log(pasta, f"File: {output_excel} — Metadata table with POI type and weight")
    return pois


def get_sector_asset_density(bbox_coords, census_gdf, pois_gdf, tags_pesos, output_gpkg, output_excel):
    print("\n⚙️ Iniciando cálculo de densidade de ativos por setor...")
    west, south, east, north = bbox_coords
    bbox_poly = Polygon([(west, south), (west, north), (east, north), (east, south)])
    mask_sectors = census_gdf.geometry.intersects(bbox_poly)
    sectors = census_gdf.loc[mask_sectors].copy().reset_index(drop=True)
    print(f"🔎 Setores na região de interesse: {len(sectors)}")
    sectors['area_km2'] = sectors.geometry.to_crs(epsg=6933).area / 1e6
    pois = pois_gdf.to_crs(sectors.crs)
    join = gpd.sjoin(
        pois[['type','geometry']],
        sectors[['CD_GEOCODI','geometry']],
        how='inner',
        predicate='intersects')
    counts = (
        join.groupby(['CD_GEOCODI','type'])
            .size()
            .unstack(fill_value=0))
    all_types = set(counts.columns) | set(tags_pesos.keys())
    for key in all_types:
        series = counts.get(key, pd.Series(0, index=sectors['CD_GEOCODI']))
        aligned = series.reindex(sectors['CD_GEOCODI'], fill_value=0)
        sectors.loc[:, f"n_{key}"] = aligned.values
    sectors['ativos_total'] = sum(
        sectors[f"n_{k}"] * w
        for k, (_, _, w) in tags_pesos.items() if w >= 4)
    sectors['densidade'] = (
        sectors['ativos_total'] /
        sectors['area_km2'].replace({0: pd.NA})).fillna(0)
    sectors.to_file(output_gpkg, driver='GPKG')
    sectors.drop(columns='geometry').to_excel(output_excel, index=False)
    print("✅ Densidade de ativos calculada e salva")
    log(info, f"Sectors in the region of interest: {len(sectors)}")
    return sectors


def visualizar_pois(pois_gdf, bbox_coords, output_path):
    print("\n⚙️ Gerando imagem dos POIs...")
    sw_lng, sw_lat, ne_lng, ne_lat = bbox_coords
    lat_diff = ne_lat - sw_lat
    lon_diff = ne_lng - sw_lng
    max_diff = max(lat_diff, lon_diff)
    if   max_diff < 0.005: zoom = 17
    elif max_diff < 0.01:  zoom = 16
    elif max_diff < 0.02:  zoom = 15
    elif max_diff < 0.05:  zoom = 14
    elif max_diff < 0.1:   zoom = 13
    elif max_diff < 0.5:   zoom = 12
    elif max_diff < 1.0:   zoom = 11
    elif max_diff < 2.0:   zoom = 10
    elif max_diff < 5.0:   zoom = 9
    elif max_diff < 10.0:  zoom = 8
    else:                  zoom = 6
    crit = pois_gdf[pois_gdf['weight'] >= 4]
    reg = pois_gdf[pois_gdf['weight'] < 4]
    osm_tiles = cimgt.OSM()
    fig = plt.figure(figsize=(12,10))
    ax = plt.axes(projection=osm_tiles.crs)
    ax.set_extent([sw_lng, ne_lng, sw_lat, ne_lat], crs=ccrs.PlateCarree())
    start = time.monotonic()
    loaded = False
    while time.monotonic() - start < 60:
        try:
            ax.add_image(osm_tiles, zoom, alpha=0.5)
            loaded = True
            break
        except URLError:
            time.sleep(1)
    if not loaded:
        print("❌ Não foi possível carregar nenhum tile OSM em 60s; imagem não gerada.")
        plt.close(fig)
        return
    line_w_reg = 1.5
    line_w_crit = 3.0
    poly_w = 1.5
    pt_size = 30
    def filtrar(gdf, tipos):
        return gdf[gdf.geometry.type.isin(tipos)]
    reg_lines = filtrar(reg,  ['LineString','MultiLineString'])
    crit_lines = filtrar(crit, ['LineString','MultiLineString'])
    if not reg_lines.empty:
        reg_lines.plot(ax=ax, transform=ccrs.PlateCarree(), linewidth=line_w_reg, color='blue')
    if not crit_lines.empty:
        crit_lines.plot(ax=ax, transform=ccrs.PlateCarree(), linewidth=line_w_crit, color='red')
    reg_polys = filtrar(reg,  ['Polygon','MultiPolygon'])
    crit_polys = filtrar(crit, ['Polygon','MultiPolygon'])
    if not reg_polys.empty:
        reg_polys.plot(ax=ax, transform=ccrs.PlateCarree(), facecolor='none', edgecolor='blue', linewidth=poly_w)
    if not crit_polys.empty:
        crit_polys.plot(ax=ax, transform=ccrs.PlateCarree(), facecolor='none', edgecolor='red', linewidth=poly_w)
    reg_pts = filtrar(reg,  ['Point','MultiPoint'])
    crit_pts = filtrar(crit, ['Point','MultiPoint'])
    if not reg_pts.empty:
        reg_pts.plot(ax=ax, transform=ccrs.PlateCarree(), marker='o', color='blue', markersize=pt_size)
    if not crit_pts.empty:
        crit_pts.plot(ax=ax, transform=ccrs.PlateCarree(), marker='o', color='red', markersize=pt_size)
    ax.annotate('N', xy=(0.05,0.95), xytext=(0.05,0.87),
                xycoords='axes fraction', textcoords='axes fraction',
                arrowprops=dict(facecolor='black', width=5, headwidth=15),
                ha='center', va='center', fontsize=14, fontweight='bold')
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, linestyle='--', color='gray')
    gl.top_labels = False
    gl.right_labels = False
    legend = [Patch(color='blue', label='POIs regulares'), Patch(color='red',  label='POIs críticos')]
    ax.legend(handles=legend, loc='lower left')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ Mapa de POIs gerado com sucesso")
    log_image(output_path, description="Map of Critical and Regular POIs:")
    log_spacing()


def compute_rho_prime(census_full, sectors_df, output_excel, output_gpkg):
    log_spacing("Municipalities in the selected region:", font_size=13, color="gray20")
    print("\n⚙️ Iniciando cálculo de ρ' (rho_prime)...")
    pop_dict = census_full.groupby('NM_MUNICIP')['Residentes'].sum().to_dict()
    df = sectors_df.copy()
    df['population'] = df['NM_MUNICIP'].map(pop_dict).fillna(0).astype(int)
    def categorize(p):
        if p < 20000: return 'C1'
        if p < 50000: return 'C2'
        if p < 150000: return 'C3'
        if p < 500000: return 'C4'
        if p < 1000000: return 'C5'
        return 'C6'
    df['category'] = df['population'].apply(categorize)
    for m in df['NM_MUNICIP'].unique():
        pop = df.loc[df['NM_MUNICIP'] == m, 'population'].iat[0]
        cat = df.loc[df['NM_MUNICIP'] == m, 'category'].iat[0]
        print(f"📌 Município {m}: pop={pop}, categoria={cat}")
        log(map_ico, f"{m.capitalize()}: {pop} residents — Category {cat}")
    def map_group(row):
        t, cat = row['TIPO'].lower(), row['category']
        if t == 'rural':
            if cat in ['C2', 'C3', 'C4']: return 'R1'
            if cat in ['C1', 'C6']: return 'R2'
            return 'R3'
        else:
            if cat in ['C1', 'C2', 'C3', 'C4', 'C5']: return 'U1'
            return 'U2'
    df['group'] = df.apply(map_group, axis=1)
    rho_crit_map = {
        'R1': 0.0324, 'R2': 0.2067, 'R3': 5.1928,
        'U1': 26.5637, 'U2': 81.4377}
    df['rho_prime'] = df['densidade'] / (df['densidade'] + df['group'].map(rho_crit_map))
    df.drop(columns='geometry').to_excel(output_excel, index=False)
    df.to_file(output_gpkg, driver='GPKG')
    print("✅ ρ' calculado com sucesso")
    log(pasta, f"File: {output_gpkg} — GeoPackage with all sector variables")
    log(pasta, f"File: {output_excel} — Table of sector census attributes")
    return df


def visualizar_setores(df, bbox_coords, output_path):
    print("\n⚙️ Gerando mapa dos setores...")
    sw_lng, sw_lat, ne_lng, ne_lat = bbox_coords
    bbox_poly = box(sw_lng, sw_lat, ne_lng, ne_lat)
    lat_diff = ne_lat - sw_lat
    lon_diff = ne_lng - sw_lng
    max_diff = max(lat_diff, lon_diff)
    if max_diff < 0.005: zoom = 17
    elif max_diff < 0.01:  zoom = 16
    elif max_diff < 0.02:  zoom = 15
    elif max_diff < 0.05:  zoom = 14
    elif max_diff < 0.1:   zoom = 13
    elif max_diff < 0.5:   zoom = 12
    elif max_diff < 1.0:   zoom = 11
    elif max_diff < 2.0:   zoom = 10
    elif max_diff < 5.0:   zoom = 9
    elif max_diff < 10.0:  zoom = 8
    else:                  zoom = 6
    osm_tiles = cimgt.OSM()
    fig = plt.figure(figsize=(12,10))
    ax = plt.axes(projection=osm_tiles.crs)
    ax.set_extent([sw_lng, ne_lng, sw_lat, ne_lat],
                  crs=ccrs.PlateCarree())
    try:
        ax.add_image(osm_tiles, zoom, alpha=0.5)
    except URLError:
        print("⚠️ Não foi possível carregar tiles do OSM; gerando sem basemap.")
    munis = sorted(df['NM_MUNICIP'].unique())
    n = len(munis)
    color_map = {m: colorsys.hsv_to_rgb(i/n, 0.3, 0.9) for i, m in enumerate(munis)}
    for m in munis:
        subset = df[df['NM_MUNICIP'] == m]
        subset.plot(ax=ax, facecolor=color_map[m], edgecolor='white', linewidth=1.5, transform=ccrs.PlateCarree())
    def relative_pos(x, y):
        return ((x - sw_lng) / (ne_lng - sw_lng), (y - sw_lat) / (ne_lat - sw_lat))
    base_dx, base_dy = 50, 30
    for m in munis:
        subset = df[df['NM_MUNICIP'] == m]
        uni = unary_union(subset.geometry)
        clip = uni.intersection(bbox_poly)
        pt = clip.centroid if not clip.is_empty else uni.centroid
        pop = int(subset['population'].iat[0])
        cat = subset['category'].iat[0]
        pop_fmt = f"{pop:,}".replace(",", ".")
        txt = f"{m} ({cat})\n{pop_fmt}"
        rx, ry = relative_pos(pt.x, pt.y)
        dx = base_dx if rx < 0.5 else -base_dx
        dy = base_dy if ry < 0.5 else -base_dy
        ax.annotate(
            txt,
            xy=(pt.x, pt.y),
            xycoords=ccrs.PlateCarree()._as_mpl_transform(ax),
            xytext=(dx, dy),
            textcoords='offset points',
            ha='center', va='center',
            fontsize=10, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.6, boxstyle='round,pad=0.2'),
            arrowprops=dict(arrowstyle='-', linewidth=1, color='black'))
    ax.annotate('N', xy=(0.05,0.95), xytext=(0.05,0.87),
                xycoords='axes fraction', textcoords='axes fraction',
                arrowprops=dict(facecolor='black', width=5, headwidth=15),
                ha='center', va='center', fontsize=14, fontweight='bold')
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, linestyle='--', color='gray')
    gl.top_labels = False
    gl.right_labels = False
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ Mapa de setores gerado com sucesso")
    log_image(output_path, description="Census Sectors Map:")
    log_spacing()


def compute_zeta_index(census_gdf, roads_gdf, road_raster_path, dem_path, rho_excel, output_raster_path, weights):
    log(pin, "Vulnerability & Risk Evaluation", color="black", font_size=14, font_weight="bold", icon_size=14)
    spinner = log_loading(loading, f"Computing Composite Vulnerability Index (ζ)...")
    print("\n⚙️ Iniciando cálculo do índice composto ζ...")
    w_pd, w_road, w_rho, w_ec = weights
    rho_df = pd.read_excel(rho_excel, dtype={'CD_GEOCODI': str})
    census = census_gdf.merge(
        rho_df[['CD_GEOCODI', 'rho_prime']],
        on='CD_GEOCODI', how='left')
    crs, transform, width, height = _load_dem_meta(dem_path)
    print(f"🌐 Usando CRS do DEM reprojetado: {crs}")
    census_utm = census.to_crs(crs)
    roads_utm = roads_gdf.to_crs(crs)
    roads_utm['kappa_score'] = roads_utm['vuln_weight'] / 5.0
    joined = gpd.sjoin(
        roads_utm[['burn_id','name','highway','kappa_score','geometry']],
        census_utm[['CD_GEOCODI','PD_prime','rho_prime','EC_prime','Interpolado','geometry']],
        how='left', predicate='intersects')
    agg = joined.groupby('burn_id').agg(
        name=('name', 'first'),
        highway=('highway', 'first'),
        kappa_score=('kappa_score', 'first'),
        PD_prime=('PD_prime', 'mean'),
        rho_prime=('rho_prime', 'mean'),
        EC_prime=('EC_prime', 'mean'),
        interpolado=('Interpolado', lambda s: 'yes' if (s == 'yes').any() else 'no'),).reset_index()
    agg['zeta'] = (w_pd * agg['PD_prime'] + w_road * agg['kappa_score'] + w_rho * agg['rho_prime'] + w_ec * agg['EC_prime'])
    max_id = int(agg['burn_id'].max())
    lut_kap = np.zeros(max_id+1, dtype=np.float32)
    lut_PD = np.zeros(max_id+1, dtype=np.float32)
    lut_rho = np.zeros(max_id+1, dtype=np.float32)
    lut_EC = np.zeros(max_id+1, dtype=np.float32)
    lut_zeta = np.zeros(max_id+1, dtype=np.float32)
    lut_flag = np.zeros(max_id+1, dtype=np.uint8)
    for _, row in agg.iterrows():
        bid = int(row['burn_id'])
        lut_kap[bid] = row['kappa_score']
        lut_PD[bid] = row['PD_prime']
        lut_rho[bid] = row['rho_prime']
        lut_EC[bid] = row['EC_prime']
        lut_zeta[bid] = row['zeta']
        lut_flag[bid] = 1 if row['interpolado'] == 'yes' else 0
    with rasterio.open(road_raster_path) as src:
        road_ids = src.read(1)
        profile = src.profile.copy()
    bands = np.stack([
        road_ids.astype(np.float32),
        lut_kap[road_ids],
        lut_PD[road_ids],
        lut_rho[road_ids],
        lut_EC[road_ids],
        lut_zeta[road_ids],
        lut_flag[road_ids].astype(np.float32)])
    profile.update(count=7, dtype=rasterio.float32, compress='lzw')
    with rasterio.open(output_raster_path, 'w', **profile) as dst:
        dst.write(bands)
        dst.set_band_description(1, "burn_id")
        dst.set_band_description(2, "kappa_score")
        dst.set_band_description(3, "PD_prime")
        dst.set_band_description(4, "rho_prime")
        dst.set_band_description(5, "EC_prime")
        dst.set_band_description(6, "zeta")
        dst.set_band_description(7, "interpolado_flag")
    print(f"✅ Índice ζ gerado com sucesso")
    spinner()
    return agg


def compute_social_elasticity_index(sectors_gdf, census_gdf, output_gpkg, output_excel):
    print("\n⚙️ Iniciando cálculo do Social Elasticity Index (γ)...")
    census_full = census_gdf.copy()
    census_full['CD_GEOCODI'] = census_full['CD_GEOCODI'].astype(str)
    census_full['state'] = census_full['CD_GEOCODI'].str[:2]
    census_full['cv_raw'] = census_full['Variancia'] / census_full['Renda'].replace({0: np.nan})
    census_full['cv_pct'] = census_full.groupby(['state','TIPO'])['cv_raw'].rank(pct=True).fillna(0)
    gdf = sectors_gdf.merge(
        census_full[['CD_GEOCODI','cv_raw','cv_pct']],
        on='CD_GEOCODI',
        how='left')
    gdf['pop_5mais'] = (gdf['Residentes'] - gdf['Criancas_0a4']).clip(lower=0)
    gdf['illiteracy_rate'] = 1 - (gdf['Alfabetizados'] / gdf['pop_5mais'].replace({0: np.nan}))
    gdf['gamma'] = (gdf['cv_pct'] * gdf['illiteracy_rate']).fillna(0).round(4)
    gdf.to_file(output_gpkg, driver='GPKG')
    gdf.drop(columns='geometry').to_excel(output_excel, index=False)
    print(f"✅ SEI calculado com sucesso")
    return gdf[['CD_GEOCODI', 'cv_raw', 'cv_pct', 'illiteracy_rate', 'gamma']]


def clean_sector_outputs(gpkg_path, excel_path):
    print("\n🧹 Limpando arquivos de setores...")
    cols_to_remove = [
        'CD_GEOCODB', 'NM_BAIRRO', 'CD_GEOCODS', 'NM_SUBDIST',
        'CD_GEOCODD', 'NM_DISTRIT', 'CD_GEOCODM', 'NM_MICRO',
        'NM_MESO', 'ID1', 'Cod_setor']
    gdf = gpd.read_file(gpkg_path)
    gdf_cleaned = gdf.drop(columns=[col for col in cols_to_remove if col in gdf.columns])
    gdf_cleaned.to_file(gpkg_path, driver="GPKG")
    print(f"🗂️ GPKG limpo e sobrescrito com {len(gdf_cleaned.columns)} colunas.")
    df = pd.read_excel(excel_path, dtype=str)
    df_cleaned = df.drop(columns=[col for col in cols_to_remove if col in df.columns])
    df_cleaned.to_excel(excel_path, index=False)
    print(f"📄 Excel limpo e sobrescrito com {len(df_cleaned.columns)} colunas.")
    print("✅ Limpeza concluída com sucesso")


def compute_critical_interdependence_index(susc_raster_path, pois_geojson_path):
    print("\n⚙️ Iniciando cálculo do Critical Interdependence Index (θ)...")
    pois = gpd.read_file(pois_geojson_path)
    total_assets = len(pois)
    total_weight = pois['weight'].sum()
    print(f"🔢 Total de ativos: {total_assets}")
    print(f"🔣 Soma de pesos total: {total_weight:.0f}")
    log(info, f"Total POIs in the region: {total_assets}")
    log(info, f"Sum of weights for all POIs: {total_weight}")
    with rasterio.open(susc_raster_path) as src:
        arr = src.read(1)
        transform = src.transform
        src_crs = src.crs
    pois = pois.to_crs(src_crs)
    susc_values = []
    for geom in pois.geometry:
        mask = rasterio.features.geometry_mask(
            [mapping(geom)],
            invert=True,
            transform=transform,
            out_shape=arr.shape)
        vals = arr[mask]
        susc_values.append(int(vals.max()) if vals.size else np.nan)
    pois['susc'] = susc_values
    crit = pois.loc[(pois['weight'] > 3) & (pois['susc'] == 5)]
    num_crit = len(crit)
    sum_crit = crit['weight'].sum()
    theta = float(sum_crit / total_weight) if total_weight > 0 else 0.0
    print(f"🔢 Ativos críticos em muito alta suscetibilidade: {num_crit}")
    print(f"🔣 Soma de pesos críticos: {sum_crit:.0f}")
    log(info, f"Critical POIs in very high susceptibility zones: {num_crit}")
    log(info, f"Sum of weights for critical POIs in susceptible zones: {sum_crit}")
    log(info, f"Global Critical Interdependence Index (θ): {theta:.4f}")
    print(f"✅ Critical Interdependence Index (θ): {theta:.4f}")
    return theta


def compute_svci(sectors_gdf, burn_raster_path, output_raster_path, theta, k, lam, phi):
    print("\n⚙️ Iniciando cálculo do SVCI multibanda para rodovias...")
    with rasterio.open(burn_raster_path) as src:
        zeta_bands = src.read()
        burn_id = zeta_bands[0].astype(np.int32)
        zeta_r = zeta_bands[5]
        profile = src.profile.copy()
    if not isinstance(sectors_gdf, gpd.GeoDataFrame):
        sectors_gdf = gpd.GeoDataFrame(sectors_gdf, geometry='geometry', crs=profile['crs'])
    sectors_proj = sectors_gdf.to_crs(profile['crs'])
    shapes = ((row.geometry, row['gamma']) for _, row in sectors_proj.iterrows())
    gamma = rasterize(shapes, out_shape=burn_id.shape, transform=profile['transform'], fill=0, dtype=np.float32)
    sigma_zeta = 1.0 / (1.0 + np.exp(-k * (zeta_r - 0.5)))
    mu = 1.0 + lam * theta + phi * gamma
    vsci = (5.0 - 4.0 * (1.0 - sigma_zeta) ** mu).astype(np.float32)
    vulner = np.rint(vsci).clip(1, 5).astype(np.float32)
    nodata_mask = burn_id == 0
    nodata_value = -9999.0
    burn_id_f = burn_id.astype(np.float32)
    burn_id_f[nodata_mask] = nodata_value
    zeta_r[nodata_mask] = nodata_value
    gamma[nodata_mask] = nodata_value
    sigma_zeta[nodata_mask] = nodata_value
    mu[nodata_mask] = nodata_value
    vsci[nodata_mask] = nodata_value
    vulner[nodata_mask] = nodata_value
    bands = np.vstack([zeta_bands, gamma[np.newaxis, :, :], sigma_zeta[np.newaxis, :, :], mu[np.newaxis, :, :], vsci[np.newaxis, :, :], vulner[np.newaxis, :, :]])
    profile.update(count=12, dtype=rasterio.float32, compress='lzw', nodata=nodata_value)
    with rasterio.open(output_raster_path, 'w', **profile) as dst:
        dst.write(bands)
        dst.set_band_description(1, "burn_id")
        dst.set_band_description(2, "kappa_score")
        dst.set_band_description(3, "PD_prime")
        dst.set_band_description(4, "rho_prime")
        dst.set_band_description(5, "EC_prime")
        dst.set_band_description(6, "zeta")
        dst.set_band_description(7, "interpolado_flag")
        dst.set_band_description(8, "gamma")
        dst.set_band_description(9, "sigma_zeta")
        dst.set_band_description(10, "mu")
        dst.set_band_description(11, "SVCI")
        dst.set_band_description(12, "vulnerability")
    del_file(burn_raster_path)
    print(f"✅ SVCI calculado com sucesso")
    log(pasta, f"File: {output_raster_path} — Raster with SVCI and vulnerability classification")
    return burn_id, vulner, profile


def compute_risk(burn_id, vulner, prev, base_profile, output_path):
    print("\n⚙️ Calculando o risco da infraestrutura viária...")
    if not (burn_id.shape == vulner.shape == prev.shape):
        raise ValueError("Todos os arrays devem ter o mesmo shape.")
    nodata = -9999
    mask = (burn_id != 0)
    burn_f = burn_id.astype(np.float32)
    vuln_f = vulner.astype(np.float32)
    susc_f = prev.astype(np.float32)
    burn_f[~mask] = nodata
    vuln_f[~mask] = nodata
    susc_f[~mask] = nodata
    vuln_f = np.nan_to_num(vuln_f, nan=1.0)
    susc_f = np.nan_to_num(susc_f, nan=1.0)
    v_int = vuln_f.astype(np.int32)
    p_int = susc_f.astype(np.int32)
    prod_raw = v_int * p_int
    prod_raw[~mask] = nodata
    bin_edges = [5, 10, 15, 20]
    prod_norm = np.full_like(prod_raw, nodata, dtype=np.float32)
    valid = prod_raw[mask]
    classes = np.digitize(valid, bins=bin_edges, right=True) + 1
    prod_norm[mask] = classes.astype(np.float32)
    bands = np.stack([burn_f, vuln_f, susc_f, prod_norm], axis=0)
    profile = base_profile.copy()
    profile.update(count=4, dtype=rasterio.float32, nodata=nodata, compress='lzw')
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(bands)
        dst.set_band_description(1, "burn_id")
        dst.set_band_description(2, "vulnerabilidade")
        dst.set_band_description(3, "suscetibilidade")
        dst.set_band_description(4, "risco")
    print("✅ Risco calculado com sucesso")
    log(pasta, f"File: {output_path} — Final raster map with flood risk to road infrastructure")


def visualizar_risco(risk_raster_path, bbox_coords, output_path):
    print("\n⚙️ Gerando mapa de risco...")
    sw_lng, sw_lat, ne_lng, ne_lat = bbox_coords
    lat_diff = ne_lat - sw_lat
    lon_diff = ne_lng - sw_lng
    max_diff = max(lat_diff, lon_diff)
    if max_diff < 0.005: zoom = 17
    elif max_diff < 0.01:  zoom = 16
    elif max_diff < 0.02:  zoom = 15
    elif max_diff < 0.05:  zoom = 14
    elif max_diff < 0.1:   zoom = 13
    elif max_diff < 0.5:   zoom = 12
    elif max_diff < 1.0:   zoom = 11
    elif max_diff < 2.0:   zoom = 10
    elif max_diff < 5.0:   zoom = 9
    elif max_diff < 10.0:  zoom = 8
    else:                  zoom = 6
    with rasterio.open(risk_raster_path) as src:
        risk = src.read(4).astype(np.int32)
        transform = src.transform
        raster_crs = src.crs
    if raster_crs.is_projected:
        d = raster_crs.to_dict()
        if d.get('proj') == 'utm':
            zone = int(d['zone'])
            south = d.get('south', False)
            data_crs = ccrs.UTM(zone, southern_hemisphere=south)
        else:
            data_crs = ccrs.PlateCarree()
    else:
        data_crs = ccrs.PlateCarree()
    osm_tiles = cimgt.OSM()
    fig = plt.figure(figsize=(12, 10))
    ax = plt.axes(projection=osm_tiles.crs)
    ax.set_extent([sw_lng, ne_lng, sw_lat, ne_lat],
                  crs=ccrs.PlateCarree())
    try:
        ax.add_image(osm_tiles, zoom, alpha=0.5)
    except URLError:
        print("⚠️ Não foi possível carregar tiles OSM; gerando sem basemap.")
    levels = [1,2,3,4,5]
    colors = {
        1: '#006400',
        2: '#7CFC00',
        3: '#FFD700',
        4: '#FF8C00',
        5: '#8B0000',}
    labels = {
        1: 'Muito Baixo',
        2: 'Baixo',
        3: 'Moderado',
        4: 'Alto',
        5: 'Muito Alto',}
    for lvl in levels:
        mask = (risk == lvl)
        if not mask.any():
            continue
        ske = skeletonize(mask)
        rows, cols = np.nonzero(ske)
        xs, ys = rasterio.transform.xy(transform, rows, cols, offset='center')
        ax.scatter(xs, ys, s=4, color=colors[lvl], transform=data_crs, label=labels[lvl])
    ax.annotate('N', xy=(0.05, 0.95), xytext=(0.05, 0.87),
                xycoords='axes fraction', textcoords='axes fraction',
                arrowprops=dict(facecolor='black', width=5, headwidth=15),
                ha='center', va='center', fontsize=14, fontweight='bold')
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, linestyle='--', color='gray')
    gl.top_labels = False
    gl.right_labels = False
    legend_elems = [
        Line2D([0],[0], color=colors[l], lw=2, label=f'Risco {labels[l]}')
        for l in levels if (risk == l).any()]
    ax.legend(handles=legend_elems, loc='lower left', title='Níveis de Risco')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ Mapa de risco gerado com sucesso")
    log_image(output_path, description="Road infrastructure risk map:")
    log_spacing()


def top10_rodovias(risk_raster_path, path_inforoads, output_excel=None):
    print("\n⚙️ Calculando top-10...")
    with rasterio.open(risk_raster_path) as src:
        burn_id = src.read(1).astype(int)
        risk = src.read(4).astype(int)
        nodata = src.nodata
    mask = (burn_id != 0) & (risk != nodata)
    bids = burn_id[mask].ravel()
    rvals = risk[mask].ravel()
    df = pd.DataFrame({'burn_id': bids, 'risk': rvals})
    cnt = df.groupby(['burn_id', 'risk']).size().unstack(fill_value=0)
    for lvl in range(1, 6):
        if lvl not in cnt.columns:
            cnt[lvl] = 0
    cnt = cnt[[5, 4, 3, 2, 1]].rename(columns={5: 'c5', 4: 'c4', 3: 'c3', 2: 'c2', 1: 'c1'})
    cnt_sorted = cnt.sort_values(by=['c5', 'c4', 'c3', 'c2', 'c1'], ascending=False)
    roads = pd.read_excel(path_inforoads, dtype={'burn_id': int})
    roads = roads.set_index('burn_id')['name']
    texto = {5: 'Muito Alto', 4: 'Alto', 3: 'Moderado', 2: 'Baixo', 1: 'Muito Baixo'}
    result = []
    result_ids = []
    seen = set()
    for bid, row in cnt_sorted.iterrows():
        name = roads.get(bid, None)
        if not name or name in seen:
            continue
        seen.add(name)
        for lvl in [5, 4, 3, 2, 1]:
            if row[f'c{lvl}'] > 0:
                label = texto[lvl]
                break
        result.append((name, label))
        result_ids.append(bid)
        if len(result) == 10:
            break
    df_top10 = pd.DataFrame({
        'Position': list(range(1, len(result) + 1)),
        'Burn_ID': result_ids,
        'Name': [nm for nm, _ in result],
        'Risk': [lbl for _, lbl in result]})
    if output_excel:
        df_top10.to_excel(output_excel, index=False)
        print(f"✅ Top‑10 exportado com sucesso")
    print("\nTop 10 Rodovias por Ocorrência de Pixel de Risco:\n")
    log(alerta, "Top 10 High Risk Roads:", color="black", font_size=14, font_weight="bold", icon_size=14)
    for i, (nm, lbl) in enumerate(result, 1):
        print(f"{i:2d}. {nm} ({lbl})")
        log_spacing(f"{i:2d}. {nm} ({lbl})", font_size=13, color="gray20")
    log(pasta, f"File: {output_excel} — Roads Ranked by Frequency of High Risk Segments")


def visualizar_top10(risk_raster_path, path_top10, bbox_coords, output_path):
    print("\n⚙️ Gerando mapa do Top‑10 rodovias de maior risco…")
    sw_lng, sw_lat, ne_lng, ne_lat = bbox_coords
    lat_diff, lon_diff = ne_lat - sw_lat, ne_lng - sw_lng
    max_diff = max(lat_diff, lon_diff)
    if   max_diff < 0.005: zoom = 17
    elif max_diff < 0.01:  zoom = 16
    elif max_diff < 0.02:  zoom = 15
    elif max_diff < 0.05:  zoom = 14
    elif max_diff < 0.1:   zoom = 13
    elif max_diff < 0.5:   zoom = 12
    elif max_diff < 1.0:   zoom = 11
    elif max_diff < 2.0:   zoom = 10
    elif max_diff < 5.0:   zoom = 9
    elif max_diff < 10.0:  zoom = 8
    else:                  zoom = 6
    with rasterio.open(risk_raster_path) as src:
        burn_id = src.read(1).astype(int)
        risk = src.read(4).astype(int)
        transform = src.transform
        raster_crs = src.crs
        nodata = src.nodata
    if raster_crs.is_projected:
        transformer = Transformer.from_crs(raster_crs, CRS.from_epsg(4326), always_xy=True)
    else:
        transformer = None
    df_top10 = pd.read_excel(path_top10, dtype={'Burn_ID': int})
    df_top10 = df_top10.sort_values('Position')
    label_to_color = {
        'Muito Baixo': '#006400',
        'Baixo':       '#7CFC00',
        'Moderado':    '#FFD700',
        'Alto':        '#FF8C00',
        'Muito Alto':  '#8B0000',}
    osm_tiles = cimgt.OSM()
    fig = plt.figure(figsize=(12,10))
    ax = plt.axes(projection=osm_tiles.crs)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    ax.set_extent([sw_lng, ne_lng, sw_lat, ne_lat], crs=ccrs.PlateCarree())
    try:
        ax.add_image(osm_tiles, zoom, alpha=0.5, zorder=1)
    except URLError:
        print("⚠️ Não foi possível carregar tiles do OSM; gerando sem basemap.")
    lon_mid = (sw_lng + ne_lng) / 2
    lat_mid = (sw_lat + ne_lat) / 2
    lon_off = (ne_lng - sw_lng) * 0.02
    lat_off = (ne_lat - sw_lat) * 0.02
    for row in df_top10.itertuples(index=False):
        idx = row.Position
        bid = row.Burn_ID
        label = row.Risk
        color = label_to_color.get(label, '#000000')
        mask = (burn_id == bid)
        rows, cols = np.nonzero(mask)
        xs_map, ys_map = rasterio.transform.xy(transform, rows, cols, offset='center')
        if transformer:
            lons, lats = transformer.transform(xs_map, ys_map)
        else:
            lons, lats = xs_map, ys_map
        ax.scatter(lons, lats, s=30, color=color, transform=ccrs.PlateCarree(), zorder=3)
        cx, cy = np.mean(lons), np.mean(lats)
        dx = lon_off if cx < lon_mid else -lon_off
        dy = lat_off if cy < lat_mid else -lat_off
        ax.text(
            cx + dx, cy + dy,
            str(idx),
            transform=ccrs.PlateCarree(),
            ha='center', va='center',
            fontsize=14, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.3'),
            zorder=4)
    ax.annotate('N', xy=(0.05,0.95), xytext=(0.05,0.87),
                xycoords='axes fraction', textcoords='axes fraction',
                arrowprops=dict(facecolor='black', width=5, headwidth=15),
                ha='center', va='center', fontsize=14, fontweight='bold',
                zorder=5)
    gl = ax.gridlines(draw_labels=True, linestyle='--', linewidth=0.5, color='gray')
    gl.top_labels = False
    gl.right_labels = False
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    time_end = datetime.now()
    duracao = time_end - time_start
    total_segundos = int(duracao.total_seconds())
    print("✅ Mapa do Top‑10 gerado com sucesso")
    log_image(output_path, description="Top 10 High Risk Roads Map:")
    if total_segundos < 60:
        log_spacing(f"Elapsed time: {total_segundos} seconds")
    elif total_segundos < 3600:
        minutos = total_segundos // 60
        segundos = total_segundos % 60
        log_spacing(f"Elapsed time: {minutos} min {segundos} s")
    else:
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60
        log_spacing(f"Elapsed time: {horas} h {minutos} min")
    log_spacing()
    log(check, "Risk analysis completed successfully!", color="black", font_size=14, font_weight="bold", icon_size=14)


def run_start():
    # Inicializar o Earth Engine
    initialize_ee()

    # Verifica se a pasta de resultados existe
    base_dir = os.path.dirname(__file__)
    resultados_dir = os.path.join(base_dir, "Resultados")
    os.makedirs(resultados_dir, exist_ok=True)

    # Inicializar mapa
    ICON_FILE = os.path.join(base_dir, "Icons", "logo_ico.ico")
    api = Api()
    webview.create_window("Select the region of interest", html=open("Database/map.html", "r").read(), width=1180, height=720, js_api=api)
    webview.start(gui='qt', icon=ICON_FILE)
    north_east_lat, north_east_lng, south_west_lat, south_west_lng = coordinates()

    # Iniciar o PRIORI
    mostrar_tela_logs(north_east_lat, north_east_lng, south_west_lat, south_west_lng)


def run_priori(north_east_lat, north_east_lng, south_west_lat, south_west_lng):
    bbox = (south_west_lng, south_west_lat, north_east_lng, north_east_lat)

    # Obter o DEM
    get_copernicus_dem(
        coord_1=south_west_lng,
        coord_2=south_west_lat,
        coord_3=north_east_lng,
        coord_4=north_east_lat,
        output_dem=path_dem)

    # Reprojetar o DEM e calcular o fluxo acumulado
    flow_accum_path = calculate_flow_accumulation(
        dem_path=path_dem,
        filled_dem=path_filled,
        flow_path=path_d8,
        accum_path=path_flow)

    # Obter a rede hidrográfica
    get_hydrographic_network(
        bbox_coords=bbox,
        input_geojson=path_geohydro,
        input_dem=path_dem,
        output_raster=path_hydro)

    # Obter a malha viária
    roads = get_roads_network(
        bbox_coords=bbox,
        vuln_weights=vuln_weights,
        input_geojson=path_georoads,
        input_dem=path_dem,
        output_raster=path_rasroads,
        output_excel=path_inforoads)

    # Determinar o threshold do fluxo acumulado
    threshold_streams(
        accum_path=path_flow,
        hidro_path=path_hydro,
        output_tif=path_drai,
        output_img=path_thres)

    # Calculo HAND e MRVBF
    calculate_HAND(
        filled_path=path_filled,
        drainage_path=path_drai,
        output_path=path_handraw)
    calcular_mrvbf(
        dem_path=path_dem,
        output_path=path_mrvbfraw)

    # Reclassificação de variáveis
    reclassificar_hand(
        input_path=path_handraw,
        output_path=path_handclass)
    reclassificar_mrvbf(
        input_path=path_mrvbfraw,
        output_path=path_mrvbfclass)

    # Cálculo suscetibilidade
    calcular_indice_ahp(
        input_path_1=path_handclass,
        input_path_2=path_mrvbfclass,
        output_path=path_ahp,
        peso_hand=0.5,
        peso_mrvbf=0.5)
    reclassificar_indice_ahp(
        input_path=path_ahp,
        output_path=path_susclass)
    prev = smooth_recursive(
        input_path=path_susclass,
        output_path=path_susc,
        mode_window=5,
        selem_radius=2,
        min_size_pixels=500,
        max_iters=10,
        tol_change=0)
    visualizar_suscetibilidade(
        susc_path_=path_susc,
        rios_path_=path_hydro,
        vias_path_=path_rasroads,
        output_path_=path_susimg)

    # Extrair Pontos de Interesse
    pois = get_poi_network(
        bbox_coords=bbox,
        tags_pesos=tags_pois,
        vehicular_highways=vehicular_highways,
        output_geojson=path_geopoi,
        output_excel=path_xlsxpoi)

    visualizar_pois(
        pois_gdf=pois,
        bbox_coords=bbox,
        output_path=path_pois_img)

    # Carregar o gpkg do censo
    print("\n⚙️ Carregando dados do censo...")
    log(pin, "Census Analysis", color="black", font_size=14, font_weight="bold", icon_size=14)
    spinner = log_loading(loading, "Loading census data...")
    census = gpd.read_file(path_census)
    spinner()
    print("✅ Censo carregado com sucesso")

    # Calcular a densidade de ativos
    sectors = get_sector_asset_density(
        bbox_coords=bbox,
        census_gdf=census,
        pois_gdf=pois,
        tags_pesos=tags_pois,
        output_gpkg=path_sectors,
        output_excel=path_xlsxsec)

    # Calcular o índice de densidade de ativos
    sectors = compute_rho_prime(
        census_full=census,
        sectors_df=sectors,
        output_excel=path_xlsxsec,
        output_gpkg=path_sectors)

    visualizar_setores(
        df=sectors,
        bbox_coords=bbox,
        output_path=path_sectors_img)

    # Calcular Z
    zeta = compute_zeta_index(
        census_gdf=census,
        roads_gdf=roads,
        road_raster_path=path_rasroads,
        output_raster_path=path_zeta,
        dem_path=path_dem,
        rho_excel=path_xlsxsec,
        weights=[0.30, 0.25, 0.25, 0.20])

    # Calcular ìndice de elasticidade social
    sectors = compute_social_elasticity_index(
        sectors_gdf=sectors,
        census_gdf=census,
        output_gpkg=path_sectors,
        output_excel=path_xlsxsec)

    # Limpando arquivos dos setores
    clean_sector_outputs(
        gpkg_path=path_sectors,
        excel_path=path_xlsxsec)

    # Calcular índice de interdependência crítica
    theta = compute_critical_interdependence_index(
        susc_raster_path=path_susc,
        pois_geojson_path=path_geopoi)

    # Calcular equação SVCI
    sectors = sectors.merge(census[['CD_GEOCODI', 'geometry']], on='CD_GEOCODI', how='left')
    sectors = gpd.GeoDataFrame(sectors, geometry='geometry', crs=census.crs)
    burn_id, vulner, profile = compute_svci(
        sectors_gdf=sectors,
        burn_raster_path=path_zeta,
        output_raster_path=path_vuln,
        theta=theta,
        k=10,
        lam=0.3,
        phi=0.2)

    # Cálculo do risco
    compute_risk(
        burn_id=burn_id,
        vulner=vulner,
        prev=prev,
        base_profile=profile,
        output_path=path_risk)

    # Imagem do risco:
    visualizar_risco(
        risk_raster_path=path_risk,
        bbox_coords=bbox,
        output_path=path_risk_img)

    # Top 10
    top10_rodovias(
        risk_raster_path=path_risk,
        path_inforoads=path_inforoads,
        output_excel=path_top10)

    # Imagem Top 10
    visualizar_top10(
        risk_raster_path=path_risk,
        path_top10=path_top10,
        bbox_coords=bbox,
        output_path=path_top10_img)

    # Deletar arquivos e pastas
    del_pasta("cache")
    del_file("dem_tmp.tif")
    del_file("Flow_accumulation_withnodata.tif")
    del_file(path_geohydro)
    del_file(path_georoads)


if __name__ == "__main__":
    # Nomenclatura e descrição dos arquivos
    path_dem = "Resultados/dem_reproj.tif"                  # DEM reprojetada
    path_filled = "Resultados/dem_filled.tif"               # Preenchimento de depressões do DEM
    path_d8 = "Resultados/dem_d8.tif"                       # Direção de fluxo (D8 Pointer) do DEM
    path_flow = "Resultados/dem_flowacc.tif"                # Fluxo acumulado do DEM
    path_drai = "Resultados/dem_drainage.tif"               # Fluxo acumulado após threshold
    path_thres = "Resultados/flowacc_threshold.svg"         # Gráfico de obtenção do threshold
    path_geohydro = "hydro_tmp.geojson"                     # Geojson temporário da rede hidrográfica
    path_hydro = "Resultados/hydro_mask.tif"                # Raster binário da rede hidrográfica
    path_georoads = "Resultados/roads_tmp.geojson"          # Malha viária OSM (dados completos)
    path_rasroads = "Resultados/roads.tif"                  # Raster contendo os ids da malha viária
    path_inforoads = "Resultados/roads_info.xlsx"           # ID, nome, tipo, peso
    path_handraw = "Resultados/hand_raw.tif"                # HAND conforme metodologia original
    path_handclass = "Resultados/hand_class.tif"            # HAND reclassificado de 1 a 5
    path_mrvbfraw = "Resultados/mrvbf_raw.tif"              # MRVBF conforme metodologia original
    path_mrvbfclass = "Resultados/mrvbf_class.tif"          # MRVBF reclassificado de 1 a 5
    path_ahp = "Resultados/susceptibility_ahp.tif"          # Combinação AHP do HAND e MRVBF contínua
    path_susclass = "Resultados/susceptibility_class.tif"   # Suscetibilidade reclassificada de 1 a 5
    path_susc = "Resultados/susceptibility.tif"             # Arquivo final da suscetibilidade com suavização
    path_susimg = "Resultados/susceptibility.png"           # Imagem da suscetibilidade da região
    path_geopoi = "Resultados/pois.geojson"                 # Geojson com localização da infraestrutura funcional
    path_xlsxpoi = "Resultados/pois_info.xlsx"              # ID, nome, tipo, peso
    path_census = "Database/Censo_2010.gpkg"                # Base de dados IBGE 2010
    path_sectors = "Resultados/sectors.gpkg"                # Setores e metadados completos
    path_xlsxsec = "Resultados/sectors_info.xlsx"           # Identificação, variáveis IBGE e parâmetros calculados
    path_zeta = "Resultados/zeta_tmp.tif"                   # Cálculo da variável Zeta para as rodovias
    path_vuln = "Resultados/vulnerability.gpkg"             # Vulnerabilidade final e valores intermediários
    path_risk = "Resultados/risk.tif"                       # Risco de inundação dos ativos viários
    path_pois_img = "Resultados/pois_map.png"               # Imagem: POIs críticos em vermelho e regulares em azul
    path_sectors_img = "Resultados/sectors_map.png"         # Imagem: visualização dos setores com categoria e população
    path_risk_img = "Resultados/risk_map.png"               # Imagem: visualização do risco nas rodovias
    path_top10 = "Resultados/top_10.xlsx"                   # Tabela com top 10 das rodovias com maior risco
    path_top10_img = "Resultados/top_10.png"                # Imagem: top 10 das rodovias com maior risco

    # Parâmetros ajustáveis
    vuln_weights = {
        'motorway': 5,
        'trunk': 5,
        'primary': 4,
        'secondary': 3,
        'tertiary': 2,
        'residential': 1,
        'unclassified': 1,
        'service': 1
    }
    tags_pois = {
        "hospital": ("amenity", "hospital", 5),
        "airport": ("aeroway", "aerodrome", 5),
        "bridge": ("bridge", "yes", 5),
        "tunnel": ("tunnel", "yes", 5),
        "police": ("amenity", "police", 4),
        "fire_station": ("amenity", "fire_station", 4),
        "clinic": ("amenity", "clinic", 2),
        "school": ("amenity", "school", 2),
        "university": ("amenity", "university", 2)
    }
    vehicular_highways = [
        "motorway",
        "trunk",
        "primary",
        "secondary",
        "tertiary",
        "residential",
        "unclassified",
        "service"
    ]

    # Iniciando interface gráfica
    initialize_tela_inicial()
