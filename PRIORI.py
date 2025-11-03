# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Igor Sieczkowski Moreira

# PRIORI.py
__version__ = "2.0.0"

import re
import sys
import threading
import time
from datetime import datetime
from whitebox.whitebox_tools import WhiteboxTools
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import subprocess
from cartopy import crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import rasterio.plot
from matplotlib.patches import Patch
from functools import lru_cache
import ee
import tkinter as tk
from tkinter import filedialog, messagebox
import rasterio
import requests
import osmnx as ox
from osgeo import ogr, gdal
import geopandas as gpd
from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_bounds
from rasterio import CRS
from rasterio.windows import Window
from scipy.ndimage import distance_transform_edt, uniform_filter
import os
import json
import argparse
import shutil
import pandas as pd
import rasterio.plot
import numpy as np
from shapely.geometry import Polygon
from rasterio.features import rasterize, shapes
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
import warnings
import logging
import math
from pathlib import Path
from hashlib import sha256


# Silencia avisos indesejados
os.environ.setdefault("PYWEBVIEW_GUI", "edgechromium")
os.environ.setdefault("WEBVIEW_GUI", "edgechromium")
os.environ.setdefault("PYWEBVIEW_LOG", "error")
logging.getLogger("pywebview").setLevel(logging.ERROR)
logging.getLogger("webview").setLevel(logging.ERROR)
logging.getLogger("qtpy").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", category=UserWarning)
import webview
_orig_stderr = sys.stderr
_orig_stdout = sys.stdout

class _StreamFilter(io.TextIOBase):
    _ignore_tokens = (
        # Tcl/Tk "after" noise
        "invalid command name", '("after" script)', "check_dpi_scaling", "_click_animation",
        # pywebview/Qt noise
        "[pywebview] QT cannot be loaded", "qtpy", "QtWebEngineCore", "QtModuleNotInstalledError",
        "QtWebKitWidgets", "webview.platforms.qt")
    def __init__(self, real):
        self._real = real
    def write(self, s):
        try:
            if any(tok in s for tok in self._ignore_tokens):
                return len(s)
        except Exception:
            pass
        return self._real.write(s)
    def flush(self):
        try:
            self._real.flush()
        except Exception:
            pass
sys.stderr = _StreamFilter(_orig_stderr)
sys.stdout = _StreamFilter(_orig_stdout)

def silence_tcl_bgerrors(root):
    try:
        root.tk.eval('proc bgerror {msg} {}')
    except Exception:
        pass


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
RUN_MODE = "full"
DEFAULT_MODELS = [
    {
        "path": "Database/model_rf.joblib",
        "sha256": "C1E02E41FE6B6CA0E8C65C4FDF235F41A93454DAB1F8C5DB6B447DCE4F20FF7B",
        "urls": [
            "https://github.com/igorsiecz/PRIORI/releases/download/v2.0.0/model_rf.joblib",
        ],
    },
    {
        "path": "Database/model_hgbr.joblib",
        "sha256": "4C767E0F862EC243AD9B72AC56D98EC130F2F062849C9F0ADD24EEC7B6BE9B89",
        "urls": [
            "https://github.com/igorsiecz/PRIORI/releases/download/v2.0.0/model_hgbr.joblib",
        ],
    },
]

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
pasta = "Icons/dir.png"
pixel = "Icons/pixel_size.png"
best = "Icons/best.png"
update = "Icons/update.png"
info = "Icons/info.png"
check = "Icons/check.png"
alerta = "Icons/alert.png"
error = "Icons/error.png"
logo = "Icons/logo_horizontal.png"
logo_ico = "Icons/logo_ico.ico"


def _sha256(path: str) -> str:
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _download_with_progress(url: str, dest: str, chunk=1024 * 1024, timeout=120) -> bool:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    spinner = log_loading(loading, f"Downloading {os.path.basename(dest)} …")
    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", "0") or 0)
            read = 0
            with open(tmp, "wb") as f:
                for blk in r.iter_content(chunk_size=chunk):
                    if not blk:
                        continue
                    f.write(blk)
                    read += len(blk)
                    if total:
                        pct = int(read * 100 / total)
                        print(f"\r{os.path.basename(dest)} {pct}%", end="")
        os.replace(tmp, dest)
        return True
    except Exception as e:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except:
            pass
        print(f"[download] {url} → error: {e}")
        return False
    finally:
        try:
            spinner()
        except:
            pass

def _resolve_manifest():
    cfg_path = os.path.join("Database", "config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        models = cfg.get("models") or cfg.get("model_urls")
        if isinstance(models, list) and models:
            return models
    except Exception:
        pass
    return DEFAULT_MODELS

def ensure_models():
    models = _resolve_manifest()
    missing = []
    for m in models:
        path = m["path"]
        expected = (m.get("sha256") or "").lower()
        if os.path.exists(path) and expected:
            try:
                if _sha256(path).lower() == expected:
                    log(check, f"OK: {path} (verified)")
                    continue
                else:
                    print(f"[integrity] {path} checksum mismatch. Redownloading.")
                    os.remove(path)
            except Exception:
                pass
        if os.path.exists(path) and not expected:
            log(check, f"OK: {path}")
            continue
        missing.append(m)
    for m in missing:
        path = m["path"]; urls = m.get("urls") or []; ok = False
        for url in urls:
            log(info, f"Fetching model from:\n{url}")
            if _download_with_progress(url, path):
                if m.get("sha256"):
                    got = _sha256(path).lower()
                    if got != m["sha256"].lower():
                        print(f"[integrity] SHA256 mismatch for {path}; deleting.")
                        try: os.remove(path)
                        except: pass
                        continue
                log(pasta, f"File: {path} — downloaded")
                ok = True
                break
        if not ok:
            raise RuntimeError(
                f"Could not obtain required model: {path}\n"
                f"Tried URLs: {urls}\n"
                "Publish the Release assets (or provide a Zenodo URL) and run again.")


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
    silence_tcl_bgerrors(root)
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




def prompt_module_choice():
    BG = "#ffffff"
    ACCENT = "#111827"
    SUB = "#6b7280"
    TRANSPARENT = "#010101"
    root = tk.Tk()
    silence_tcl_bgerrors(root)
    root.report_callback_exception = suppress_tcl_errors
    _center_window(root, 560, 320)
    canvas, card = _make_rounded_card(root, radius=24, pad=8, transparent=TRANSPARENT, bg=BG)

    def start_move(e):
        root._dragx, root._dragy = e.x_root, e.y_root

    def on_move(e):
        dx, dy = e.x_root - root._dragx, e.y_root - root._dragy
        root.geometry(f"+{root.winfo_x()+dx}+{root.winfo_y()+dy}")
        root._dragx, root._dragy = e.x_root, e.y_root

    card.bind("<Button-1>", start_move)
    card.bind("<B1-Motion>", on_move)
    header = tk.Frame(card, bg=BG)
    header.pack(fill="x", pady=(18, 8), padx=22)
    tk.Label(header, text="Select modules to run", bg=BG, fg=ACCENT, font=("Segoe UI", 14, "bold")).pack(side="left")

    def _cancel():
        root.destroy()
        raise RuntimeError("Canceled by the user.")

    tk.Label(header, text="✕", bg=BG, fg=SUB, cursor="hand2", font=("Segoe UI", 12, "bold")).pack(side="right")
    header.winfo_children()[-1].bind("<Button-1>", lambda e: _cancel())
    body = tk.Frame(card, bg=BG)
    body.pack(fill="both", expand=True, padx=22, pady=(2, 10))
    choice = tk.StringVar(value="full")
    full_frame = tk.Frame(body, bg=BG)
    full_frame.pack(fill="x", pady=(6, 0))
    tk.Radiobutton(
        full_frame, text="Full Risk (Susceptibility + Vulnerability)", variable=choice, value="full",
        bg=BG, fg=ACCENT, activebackground=BG, activeforeground=ACCENT, selectcolor=BG,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w")
    tk.Label(
        full_frame, text="Note: Vulnerability module is currently limited to Brazil.",
        bg=BG, fg=SUB, font=("Segoe UI", 9)
    ).pack(anchor="w", padx=(26, 0), pady=(2, 0))
    susc_frame = tk.Frame(body, bg=BG)
    susc_frame.pack(fill="x", pady=(16, 0))
    tk.Radiobutton(
        susc_frame, text="Susceptibility only", variable=choice, value="susc_only",
        bg=BG, fg=ACCENT, activebackground=BG, activeforeground=ACCENT, selectcolor=BG,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w")
    footer = tk.Frame(card, bg=BG)
    footer.pack(fill="x", pady=(8, 18), padx=22)
    btn = tk.Button(footer, text="Run", bg=ACCENT, fg="#ffffff", relief="flat", padx=14, pady=8,
                    activebackground=ACCENT, activeforeground="#ffffff", cursor="hand2",
                    command=root.quit)
    btn.pack(side="right")
    root.mainloop()
    try: root.destroy()
    except: pass
    return choice.get()


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
    root_logs.report_callback_exception = suppress_tcl_errors
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
        try:
            for stopper in list(spinner_registry.values()):
                try:
                    stopper()
                except:
                    pass
            spinner_registry.clear()
        except Exception:
            pass
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
            args=(north_east_lat, north_east_lng, south_west_lat, south_west_lng, RUN_MODE),
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


def suppress_tcl_errors(exc, val, tb):
    print("[Tkinter] Erro capturado:", val)
EMAIL_REGEX = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')


def _center_window(win, w=520, h=320):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = int((sw - w) / 2)
    y = int((sh - h) / 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


def _make_rounded_card(root, radius=20, pad=10, transparent='#010101', bg='#ffffff'):
    supports_transparency = sys.platform.startswith('win')
    if supports_transparency:
        root.overrideredirect(True)
        root.config(bg=transparent)
        try:
            root.wm_attributes('-transparentcolor', transparent)
        except tk.TclError:
            supports_transparency = False
            root.overrideredirect(False)
            root.config(bg=bg)
    canvas = tk.Canvas(root, highlightthickness=0, bd=0, bg=(transparent if supports_transparency else bg))
    canvas.pack(fill="both", expand=True)


    def draw():
        canvas.delete("all")
        w = root.winfo_width()
        h = root.winfo_height()
        x0, y0 = pad, pad
        x1, y1 = w - pad, h - pad
        r = radius
        canvas.create_arc(x0, y0, x0+2*r, y0+2*r, start=90, extent=90, fill=bg, outline=bg)
        canvas.create_arc(x1-2*r, y0, x1, y0+2*r, start=0, extent=90, fill=bg, outline=bg)
        canvas.create_arc(x1-2*r, y1-2*r, x1, y1, start=270, extent=90, fill=bg, outline=bg)
        canvas.create_arc(x0, y1-2*r, x0+2*r, y1, start=180, extent=90, fill=bg, outline=bg)
        canvas.create_rectangle(x0+r, y0, x1-r, y1, fill=bg, outline=bg)
        canvas.create_rectangle(x0, y0+r, x1, y1-r, fill=bg, outline=bg)
    root.bind("<Configure>", lambda e: draw())
    draw()
    inner = tk.Frame(canvas, bg=bg)
    inner.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0)
    inner.pack_propagate(False)
    return canvas, inner


def prompt_ee_credentials_gui():
    root = tk.Tk()
    silence_tcl_bgerrors(root)
    root.report_callback_exception = suppress_tcl_errors
    _center_window(root, 560, 360)
    TITLE = "Connect to Google Earth Engine"
    BG = "#ffffff"
    ACCENT = "#111827"
    SUB = "#6b7280"
    BTN_BG = "#111827"
    BTN_FG = "#ffffff"
    DISABLED_BG = "#9ca3af"
    TRANSPARENT = "#010101"
    canvas, card = _make_rounded_card(root, radius=24, pad=8, transparent=TRANSPARENT, bg=BG)

    def start_move(e):
        root._dragx, root._dragy = e.x_root, e.y_root

    def on_move(e):
        dx = e.x_root - root._dragx
        dy = e.y_root - root._dragy
        x = root.winfo_x() + dx
        y = root.winfo_y() + dy
        root.geometry(f"+{x}+{y}")
        root._dragx, root._dragy = e.x_root, e.y_root

    card.bind("<Button-1>", start_move)
    card.bind("<B1-Motion>", on_move)
    header = tk.Frame(card, bg=BG)
    header.pack(fill="x", pady=(18, 8), padx=22)
    title = tk.Label(header, text=TITLE, bg=BG, fg=ACCENT, font=("Segoe UI", 14, "bold"))
    title.pack(side="left")

    def _close():
        root.destroy()
        raise RuntimeError("Canceled by the user.")

    close_btn = tk.Label(header, text="✕", bg=BG, fg=SUB, cursor="hand2", font=("Segoe UI", 12, "bold"))
    close_btn.pack(side="right")
    close_btn.bind("<Button-1>", lambda e: _close())
    body = tk.Frame(card, bg=BG)
    body.pack(fill="both", expand=True, pady=(0, 10), padx=22)
    email_lbl = tk.Label(body, text="E-mail do Service Account", bg=BG, fg=ACCENT, font=("Segoe UI", 10, "bold"))
    email_lbl.pack(anchor="w", pady=(4, 4))
    email_var = tk.StringVar()
    email_entry = tk.Entry(body, textvariable=email_var, bg="#f9fafb", bd=0, highlightthickness=1, relief="flat",
                           highlightbackground="#e5e7eb", highlightcolor="#2563eb", font=("Segoe UI", 10))
    email_entry.configure(insertbackground="#111827")
    email_entry.pack(fill="x", ipady=8)
    email_entry.focus_set()
    email_hint = tk.Label(body, text="Use email as it is on your Service Account", bg=BG, fg=SUB, font=("Segoe UI", 9))
    email_hint.pack(anchor="w", pady=(6, 14))
    email_err = tk.Label(body, text="", bg=BG, fg="#dc2626", font=("Segoe UI", 9))
    email_err.pack(anchor="w")
    json_lbl = tk.Label(body, text="Credentials (.json file)", bg=BG, fg=ACCENT, font=("Segoe UI", 10, "bold"))
    json_lbl.pack(anchor="w", pady=(14, 4))
    file_frame = tk.Frame(body, bg=BG)
    file_frame.pack(fill="x")
    json_path_var = tk.StringVar(value="")
    json_entry = tk.Entry(file_frame, textvariable=json_path_var, bg="#f9fafb", bd=0, highlightthickness=1, relief="flat",
                          highlightbackground="#e5e7eb", highlightcolor="#2563eb", font=("Segoe UI", 10))
    json_entry.configure(insertbackground="#111827")
    json_entry.pack(side="left", fill="x", expand=True, ipady=8)

    def browse_json():
        path = filedialog.askopenfilename(
            title="Select the Earth Engine JSON file",
            filetypes=[("JSON files", "*.json")])
        if path:
            json_path_var.set(path)
            validate_form()

    browse_btn = tk.Button(file_frame, text="Procurar…", command=browse_json, bg="#f3f4f6", fg=ACCENT, relief="flat",
                           activebackground="#e5e7eb", activeforeground=ACCENT, padx=10, pady=6)
    browse_btn.pack(side="left", padx=(8, 0))
    json_err = tk.Label(body, text="", bg=BG, fg="#dc2626", font=("Segoe UI", 9))
    json_err.pack(anchor="w", pady=(4, 0))
    footer = tk.Frame(card, bg=BG)
    footer.pack(fill="x", pady=(8, 18), padx=22)
    status_lbl = tk.Label(footer, text="", bg=BG, fg=SUB, font=("Segoe UI", 9))
    status_lbl.pack(side="left")

    def set_btn_state(enabled):
        if enabled:
            save_btn.config(state="normal", bg=BTN_BG, fg=BTN_FG, cursor="hand2")
        else:
            save_btn.config(state="disabled", bg=DISABLED_BG, fg="#f3f4f6", cursor="arrow")

    save_btn = tk.Button(footer, text="Save and connect", bg=DISABLED_BG, fg="#f3f4f6", relief="flat", padx=14, pady=8,
                         state="disabled", activebackground=BTN_BG, activeforeground=BTN_FG)
    save_btn.pack(side="right")

    def is_valid_email(s: str) -> bool:
        return bool(EMAIL_REGEX.match(s.strip()))

    def validate_form(*_):
        ok_email = is_valid_email(email_var.get())
        ok_json  = os.path.isfile(json_path_var.get())
        email_err.config(text="" if ok_email or not email_var.get().strip() else "Invalid email.")
        json_err.config(text="" if ok_json or not json_path_var.get().strip() else "Select a valid .json file.")
        set_btn_state(ok_email and ok_json)

    email_var.trace_add("write", validate_form)
    json_path_var.trace_add("write", validate_form)
    result = {"email": None, "json": None}

    def do_save():
        sa = email_var.get().strip()
        jp = json_path_var.get().strip()
        try:
            status_lbl.config(text="Connecting to Earth Engine…")
            root.update_idletasks()
            creds = ee.ServiceAccountCredentials(sa, jp)
            ee.Initialize(creds)
            # Ok — salva e fecha
            result["email"] = sa
            result["json"]  = jp
            messagebox.showinfo("Success", "Earth Engine access granted ✔️")
            root.quit()
        except Exception as e:
            messagebox.showerror("Connection failed",
                                 f"Unable to initialize with the provided credentials.\n\nDetails:\n{e}")
        finally:
            status_lbl.config(text="")
    save_btn.config(command=do_save)
    root.mainloop()
    try:
        root.destroy()
    except Exception:
        pass
    if not (result["email"] and result["json"]):
        raise RuntimeError("Operation canceled by user.")
    return result["email"], result["json"]


def initialize_ee():
    os.makedirs("Database", exist_ok=True)
    cred_file = os.path.join("Database", "ee_credentials_path.txt")
    def try_init_from_file(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]
        if len(lines) < 2:
            raise ValueError("Arquivo de credenciais incompleto.")
        service_account, cred_path = lines[0], lines[1]
        creds = ee.ServiceAccountCredentials(service_account, cred_path)
        ee.Initialize(creds)
        return service_account, cred_path
    try:
        sa, jp = try_init_from_file(cred_file)
        print(f"\n🔐 Service Account: {sa}\n📁 Credential Path: {jp}")
        return sa, jp
    except Exception as e:
        print("\n[EE] Tentativa inicial falhou — abrindo assistente gráfico…")
        print("Motivo:", e)
    sa, jp = prompt_ee_credentials_gui()
    try:
        with open(cred_file, "w", encoding="utf-8") as f:
            f.write(f"{sa}\n{jp}\n")
        print("\nCredenciais registradas com sucesso.")
        return sa, jp
    except Exception as e:
        raise RuntimeError(f"Não foi possível salvar o caminho das credenciais: {e}")


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


def get_copernicus_dem(coord_1, coord_2, coord_3, coord_4, output_dem, native_scale_m=30, max_side_px=10_000,
                       max_request_bytes=50_331_648, bytes_per_pixel_est=4.5,safety_margin=0.90,
                       retry_http_statuses=(500, 502, 503, 504), max_retries=5, backoff_shrink=0.85, request_timeout=180):
    log(pin, "Digital Elevation Model (DEM)", color="black", font_size=14, font_weight="bold", icon_size=14)
    w, s, e, n = coord_1, coord_2, coord_3, coord_4
    cx = (w + e) / 2.0
    cy = (s + n) / 2.0
    dem_ic = ee.ImageCollection("COPERNICUS/DEM/GLO30")
    if dem_ic.size().getInfo() == 0:
        raise RuntimeError("Não foram encontradas imagens para as coordenadas especificadas.")
    m_per_lat = 110_574.0
    m_per_lon = 111_320.0 * math.cos(math.radians(cy))
    width_deg = max(e - w, 1e-12)
    height_deg = max(n - s, 1e-12)
    width_m = width_deg * m_per_lon
    height_m = height_deg * m_per_lat
    native_w_px = width_m / native_scale_m
    native_h_px = height_m / native_scale_m
    aspect = native_w_px / max(native_h_px, 1e-12)
    max_pixels_by_bytes = int((max_request_bytes * safety_margin) // bytes_per_pixel_est)
    w_by_bytes = int(math.floor(math.sqrt(max_pixels_by_bytes * aspect)))
    h_by_bytes = int(math.floor(math.sqrt(max_pixels_by_bytes / aspect)))
    if aspect >= 1.0:
        w_by_dim = max_side_px
        h_by_dim = max(1, int(math.floor(w_by_dim / aspect)))
    else:
        h_by_dim = max_side_px
        w_by_dim = max(1, int(math.floor(h_by_dim * aspect)))
    target_w_px = max(1, min(w_by_bytes, w_by_dim))
    target_h_px = max(1, min(h_by_bytes, h_by_dim))
    need_expand = (native_w_px < target_w_px) or (native_h_px < target_h_px)
    if need_expand:
        new_width_m = target_w_px * native_scale_m
        new_height_m = target_h_px * native_scale_m
        new_width_deg = new_width_m / m_per_lon
        new_height_deg = new_height_m / m_per_lat
        w2 = cx - new_width_deg / 2.0
        e2 = cx + new_width_deg / 2.0
        s2 = cy - new_height_deg / 2.0
        n2 = cy + new_height_deg / 2.0
    else:
        w2, s2, e2, n2 = w, s, e, n
    roi_final = ee.Geometry.BBox(w2, s2, e2, n2)
    dem = dem_ic.select(['DEM']).mosaic().clip(roi_final)

    def _try(dim_w, dim_h):
        params = {
            'region': roi_final.getInfo()['coordinates'],
            'format': 'GeoTIFF', 'dimensions': f"{int(dim_w)}x{int(dim_h)}"}
        print(f"\n⚙️ Iniciando o download do DEM... (dimensions={params['dimensions']})")
        spinner = log_loading(loading, "Downloading DEM file...")
        try:
            url = dem.getDownloadURL(params)
        except Exception as e:
            msg = str(e)
            m = re.search(r"Total request size \((\d+) bytes\) must be less than or equal to (\d+) bytes", msg)
            spinner()
            if m:
                requested = int(m.group(1))
                allowed = int(m.group(2))
                print(f"⚠️ EE limit: requested={requested:,} bytes > allowed={allowed:,} bytes")
                return None, (requested, allowed)
            raise
        resp = requests.get(url, timeout=request_timeout)
        spinner()
        if resp.status_code == 200:
            with open('dem_tmp.tif', 'wb') as f:
                f.write(resp.content)
            print('✅ Download realizado com sucesso')
            reproject_dem(output_dem)
            return True, None
        else:
            print(f"⚠️ Erro HTTP ao baixar: {resp.status_code}")
            return False, resp.status_code
    cur_w, cur_h = target_w_px, target_h_px
    for attempt in range(1, max_retries + 1):
        ok, info = _try(cur_w, cur_h)
        if ok is True:
            # sucesso
            return (w2, s2, e2, n2)
        if ok is None and isinstance(info, tuple):
            requested_bytes, allowed_bytes = info
            shrink = math.sqrt(allowed_bytes / max(requested_bytes, 1)) * 0.90
            cur_w = max(1, int(cur_w * shrink))
            cur_h = max(1, int(cur_h * shrink))
            print(f"↩️ Reajustando dimensions (bytes): fator={shrink:.3f} → {cur_w}x{cur_h} (tentativa {attempt+1}/{max_retries})")
            continue
        if ok is False and (info in retry_http_statuses or isinstance(info, int)):
            cur_w = max(1, int(cur_w * backoff_shrink))
            cur_h = max(1, int(cur_h * backoff_shrink))
            print(f"↩️ Reajustando dimensions (HTTP {info}): fator={backoff_shrink:.2f} → {cur_w}x{cur_h} (tentativa {attempt+1}/{max_retries})")
            continue
        break
    raise RuntimeError("Não foi possível baixar o DEM dentro dos limites/retries do getDownloadURL.")


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


def clip_raster_to_bbox_wgs84(path_in: str, path_out: str, bbox_wgs84: tuple):
    w, s, e, n = bbox_wgs84
    if w > e: w, e = e, w
    if s > n: s, n = n, s
    with rasterio.open(path_in) as src:
        src_crs = src.crs
        if src_crs is None:
            raise ValueError("Raster sem CRS; não é possível reprojetar a bbox.")
        left, bottom, right, top = transform_bounds("EPSG:4326", src_crs, w, s, e, n, densify_pts=0)
        rb = src.bounds
        left = max(left,   rb.left)
        right = min(right,  rb.right)
        bottom = max(bottom, rb.bottom)
        top = min(top,    rb.top)
        if not (left < right and bottom < top):
            raise ValueError(
                "A bbox de corte não intersecta o raster.\n"
                f"Raster bounds: {rb}\n"
                f"BBox (no CRS do raster): left={left}, bottom={bottom}, right={right}, top={top}\n"
                "Verifique se a bbox está mesmo em WGS84 (lon/lat).")
        row_top, col_left = src.index(left,  top)
        row_bottom, col_right = src.index(right, bottom)
        row_off = max(0, min(row_top, row_bottom))
        col_off = max(0, min(col_left, col_right))
        row_max = min(src.height, max(row_top, row_bottom))
        col_max = min(src.width,  max(col_left, col_right))
        height_px = row_max - row_off
        width_px = col_max - col_off
        if height_px <= 0 or width_px <= 0:
            raise ValueError("Janela de recorte vazia após ajuste aos limites do raster.")
        win = Window.from_slices((row_off, row_max), (col_off, col_max))
        out_transform = src.window_transform(win)
        profile = src.profile.copy()
        profile.update({
            "height": height_px,
            "width":  width_px,
            "transform": out_transform})
        tmp_out = path_out + ".clip_tmp.tif"
        with rasterio.open(tmp_out, "w", **profile) as dst:
            for b in range(1, src.count + 1):
                dst.write(src.read(b, window=win), b)
    os.replace(tmp_out, path_out)


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
    roads_gdf["name"] = roads_gdf.get("name", "").fillna("").replace("", "Unnamed")
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
    threshold_value = max_flow * (thr / 100.0)
    filtered_flow_ = np.where(accumulated_flow >= threshold_value, accumulated_flow, 0)
    nonzero_flow = filtered_flow_ > 0
    matching_pixels = np.sum(nonzero_flow & (distances <= max_dist))
    total_nonzero_flow = np.sum(nonzero_flow)
    similarity_percentage = (matching_pixels / total_nonzero_flow) * 100 if total_nonzero_flow > 0 else 0
    return similarity_percentage, filtered_flow_, threshold_value / 10.0


def threshold_streams(accum_path, hidro_path, output_tif, output_img):
    log(pin, "Hydrologic Flow Analysis", color="black", font_size=14, font_weight="bold", icon_size=14)
    spinner = log_loading(loading, "Calibrating flow threshold to match hydrography...")
    print("\n⚙️ Calculando threshold do fluxo acumulado...")
    max_distance = 1000
    with rasterio.open(accum_path) as src1:
        fluxo_acumulado = src1.read(1)
        profile = src1.profile.copy()
        pixel_size = src1.transform[0]
    with rasterio.open(hidro_path) as src2:
        rede_hidro = src2.read(1)
    print(f"📐 Tamanho do pixel: {pixel_size}")
    rede_hidro_binaria = rede_hidro > 0
    del rede_hidro
    dist_px = distance_transform_edt(~rede_hidro_binaria).astype(np.float32, copy=False)
    max_px = max_distance / float(pixel_size)
    within_maxdist = dist_px <= max_px
    del dist_px, rede_hidro_binaria
    flow = fluxo_acumulado.astype(np.float32, copy=False)
    F = flow.ravel()
    M = within_maxdist.ravel()
    valid = np.isfinite(F)
    if not np.all(valid):
        F = F[valid]
        M = M[valid]
    if F.size == 0:
        thresholds = np.arange(0.01, 50.01, 0.01, dtype=np.float32)
        similarities = np.zeros_like(thresholds, dtype=np.float32)
        plt.figure(figsize=(10, 6))
        plt.plot(thresholds, similarities, marker='o', linestyle='-')
        plt.xlabel("Threshold (%)")
        plt.ylabel("Similarity (%)")
        plt.grid()
        plt.savefig(output_img, format="svg")
        plt.close()
        best_filtered_flow = np.zeros_like(flow, dtype=np.float32)
        nodata_value = profile.get('nodata', None)
        if nodata_value is not None:
            best_filtered_flow = np.where(best_filtered_flow == nodata_value, 0, best_filtered_flow)
            profile.pop('nodata', None)
        profile.update(dtype='float32', count=1, compress='lzw', BIGTIFF='IF_SAFER')
        with rasterio.open(output_tif, "w", **profile) as dst:
            dst.write(best_filtered_flow, 1)
        print(f"🧠 Melhor threshold: 0 (0.00%) - 0.00% similar")
        spinner()
        log(pasta, f"File: {output_tif} — Drainage raster (thresholded flow accumulation)")
        log(pixel, f"Pixel size: {pixel_size:.2f} m")
        log(best, f"Best threshold: {0.00:.2f}% ({0:.0f}) — {0.00:.2f}% match with hydro mask")
        log_image(output_img, description="Flow Threshold Calibration Curve:")
        return
    order = np.argsort(F, kind="stable")
    F_sorted = F[order]
    M_sorted = M[order].astype(np.int64, copy=False)
    del F, M
    cum_M_asc = np.cumsum(M_sorted)
    total_M = int(cum_M_asc[-1]) if cum_M_asc.size else 0
    N = F_sorted.size
    maxF = float(F_sorted[-1])
    thresholds = np.arange(0.01, 50.01, 0.01, dtype=np.float32)
    if maxF <= 0:
        similarities = np.zeros_like(thresholds, dtype=np.float32)
        best_idx = 0
        best_threshold = float(thresholds[best_idx])
        best_similarity = float(similarities[best_idx])
        best_threshold_value = 0.0
        best_tau = 0.0
    else:
        tau_vals = (thresholds / 100.0) * maxF
        idxs = np.searchsorted(F_sorted, tau_vals, side='left')
        k = (N - idxs).astype(np.int64)
        cum_M_geq = np.empty_like(k, dtype=np.int64)
        nonzero = idxs > 0
        cum_M_geq[nonzero]  = total_M - cum_M_asc[idxs[nonzero] - 1]
        cum_M_geq[~nonzero] = total_M
        with np.errstate(divide='ignore', invalid='ignore'):
            similarities = np.where(k > 0, (cum_M_geq / k) * 100.0, 0.0).astype(np.float32)
        best_idx = int(np.argmax(similarities)) if similarities.size else 0
        best_threshold = float(thresholds[best_idx])
        best_similarity = float(similarities[best_idx])
        best_tau = (best_threshold / 100.0) * maxF
        best_threshold_value = (best_tau / 10.0)
    best_filtered_flow = np.where(flow >= best_tau, flow, 0).astype(np.float32, copy=False)
    nodata_value = profile.get('nodata', None)
    if nodata_value is not None:
        best_filtered_flow = np.where(best_filtered_flow == nodata_value, 0, best_filtered_flow)
        profile.pop('nodata', None)
    profile.update(dtype='float32', count=1, compress='lzw', BIGTIFF='IF_SAFER')
    with rasterio.open(output_tif, "w", **profile) as dst:
        dst.write(best_filtered_flow, 1)
    plt.figure(figsize=(10, 6))
    plt.plot(thresholds, similarities, marker='o', linestyle='-')
    plt.xlabel("Threshold (%)")
    plt.ylabel("Similarity (%)")
    plt.grid()
    plt.savefig(output_img, format="svg")
    plt.close()
    print(f"🧠 Melhor threshold: {best_threshold_value:.0f} ({best_threshold:.2f}%) - {best_similarity:.2f}% similar")
    spinner()
    log(pasta, f"File: {output_tif} — Drainage raster (thresholded flow accumulation)")
    log(pixel, f"Pixel size: {pixel_size:.2f} m")
    log(best, f"Best threshold: {best_threshold:.2f}% ({best_threshold_value:.0f}) — {best_similarity:.2f}% match with hydro mask")
    log_image(output_img, description="Flow Threshold Calibration Curve:")


def calculate_HAND(filled_path, drainage_path, output_path, bbox_ext=None):
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
    if bbox_ext is not None:
        print("✂️  Recortando o HAND à bbox (WGS84)…")
        clip_raster_to_bbox_wgs84(HAND, HAND, bbox_ext)
        print("✅ Recorte concluído")
    return HAND


def _find_saga_cmd():
    hint = os.environ.get("SAGA_CMD")
    if hint:
        if os.path.isdir(hint):
            c = os.path.join(hint, "saga_cmd.exe")
            if os.path.isfile(c):
                return c
        elif os.path.isfile(hint):
            return hint
    candidates = [
        os.path.join(sys.prefix, "Library", "bin", "saga_cmd.exe"),
        os.path.join(sys.prefix, "bin", "saga_cmd.exe"),
        os.path.join(sys.prefix, "Scripts", "saga_cmd.exe"),]
    candidates += [
        r"C:\OSGeo4W64\bin\saga_cmd.exe",
        r"C:\OSGeo4W\bin\saga_cmd.exe",
        r"C:\Program Files\SAGA-GIS\saga_cmd.exe",
        r"C:\Program Files\SAGA GIS LTR\saga_cmd.exe",
        r"C:\Users\igors\Documents\saga-9.8.0_x64\saga_cmd.exe",]
    which = shutil.which("saga_cmd.exe") or shutil.which("saga_cmd")
    if which:
        candidates.insert(0, which)
    for c in candidates:
        if os.path.isfile(c):
            return c
    raise FileNotFoundError(
        "saga_cmd.exe não encontrado.\n"
        "Defina SAGA_CMD com o caminho para saga_cmd.exe ou instale SAGA (OSGeo/standalone).")


def _detect_mrvbf_tool_id(saga_cmd_path: str) -> str:
    try:
        out = subprocess.run([saga_cmd_path, "ta_morphometry", "-h"], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, check=True).stdout
        m = re.search(r'\[(\d+)\]\s.*MRVBF', out, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "8"


def _prepare_saga_env_from_exe(saga_exe: str):
    env = os.environ.copy()
    saga_dir = Path(saga_exe).parent
    env["PATH"] = str(saga_dir) + os.pathsep + env.get("PATH", "")
    candidates = [
        saga_dir / "modules",
        saga_dir / "tools",
        saga_dir.parent / "apps" / "saga" / "modules",
        saga_dir.parent / "apps" / "saga" / "tools",]
    for c in candidates:
        if c.is_dir():
            env.setdefault("SAGA_MLB", str(c))
            env.setdefault("SAGA_TLB", str(c))
            break
    return env, str(saga_dir)


def calcular_mrvbf(dem_path, output_path, wmax_px=243, bbox_ext=None):
    print("\n⚙️ Calculando o MRVBF (6 níveis, Wmax=243 px)…")
    spinner = log_loading(loading, "Calculating MRVBF...")
    base_dir = os.path.dirname(__file__)
    input_dem = os.path.join(base_dir, dem_path)
    mrvbf_out = os.path.join(base_dir, output_path)
    with rasterio.open(input_dem) as ds:
        width_px, height_px = ds.width, ds.height
        transform = ds.transform
        crs = ds.crs
        res_x = abs(transform.a)
        res_y = abs(transform.e)
        if crs and crs.is_geographic:
            bounds = ds.bounds
            lat_c = 0.5 * (bounds.top + bounds.bottom)
            m_per_lat = 110_574.0
            m_per_lon = 111_320.0 * math.cos(math.radians(lat_c))
            res_m_x = res_x * m_per_lon
            res_m_y = res_y * m_per_lat
        else:
            res_m_x = res_x
            res_m_y = res_y
        res_m = 0.5 * (res_m_x + res_m_y)
        D_px = math.hypot(width_px, height_px)
    t_slope = 116.57 * (res_m ** -0.62)
    max_res_percent = 100.0 * (wmax_px / D_px)
    max_res_percent = max(0.0001, min(max_res_percent, 100.0))
    print(f"   • Resolução média ≈ {res_m:.2f} m")
    print(f"   • T_SLOPE (RSAGA) = {t_slope:.3f}")
    print(f"   • Diâmetro (px) = {D_px:.1f}  →  -MAX_RES = {max_res_percent:.6f}% (Wmax={wmax_px}px)")
    saga_exe = _find_saga_cmd()
    tool_id = _detect_mrvbf_tool_id(saga_exe)
    env, cwd = _prepare_saga_env_from_exe(saga_exe)
    if not os.path.isfile(input_dem):
        raise FileNotFoundError(f"DEM not found: {input_dem}")
    cmd = [
        saga_exe, "ta_morphometry", tool_id,
        "-DEM", input_dem,
        "-MRVBF", mrvbf_out,
        "-T_SLOPE", f"{t_slope:.3f}",
        "-MAX_RES", f"{max_res_percent:.6f}",
        "-CLASSIFY", "0"]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=cwd)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "saga_cmd.exe não foi encontrado. Instale o SAGA ou defina a variável de ambiente SAGA_CMD "
            "apontando para o executável (ex.: C:\\OSGeo4W64\\bin\\saga_cmd.exe)."
        ) from e
    if result.returncode != 0:
        print("❌ Erro ao calcular MRVBF com SAGA GIS")
        print("---- STDOUT ----")
        print(result.stdout.strip())
        print("---- STDERR ----")
        print(result.stderr.strip())
        raise RuntimeError("Falha na execução do SAGA GIS.")
    if result.returncode != 0:
        print("❌ Erro ao calcular MRVBF com SAGA GIS:")
        print(result.stderr)
        raise RuntimeError("Falha na execução do SAGA GIS.")
    print("✅ MRVBF gerado com sucesso")
    if bbox_ext is not None:
        print("✂️  Recortando o MRVBF à bbox (WGS84)…")
        clip_raster_to_bbox_wgs84(mrvbf_out, mrvbf_out, bbox_ext)
        print("✅ Recorte concluído")
        spinner()
    try:
        log(pasta, f"File: {output_path} — Raw MRVBF values")
    except Exception:
        pass
    meta = {
        "t_slope": t_slope,
        "max_res_percent": max_res_percent,
        "wmax_px": wmax_px,
        "res_m": res_m,
        "clipped": bbox_ext is not None}
    return mrvbf_out, meta

def mix_cuts_by_proto(th_json, K, sig_new, allow_extrapolation=True):
        proto = th_json.get("proto", None)
        if not proto:
            return None, None, None
        keys = proto.get("keys", [])
        if len(keys) != 2:
            return None, None, None
        k0, k1 = keys[0], keys[1]
        sig_p = proto["signature"]["p"]
        qa = np.array(proto["signature"][k0]["q"], dtype=float)
        qb = np.array(proto["signature"][k1]["q"], dtype=float)
        if sig_new is None or len(sig_new) != len(qa):
            return None, None, None
        v = qb - qa
        denom = float(np.dot(v, v)) + 1e-12
        alpha = float(np.dot(sig_new - qa, v) / denom)
        if not allow_extrapolation:
            alpha = max(0.0, min(1.0, alpha))
        Ka = np.array(proto["cuts"][k0][str(K)], dtype=float)
        Kb = np.array(proto["cuts"][k1][str(K)], dtype=float)
        mixed = Ka + alpha * (Kb - Ka)
        for i in range(1, mixed.size):
            if not (mixed[i] > mixed[i-1]):
                mixed[i] = np.nextafter(mixed[i-1], np.inf)
        return mixed.astype(float), alpha, (k0, k1)


def _read_river_geoms(river_path, ref_shape, ref_transform, ref_crs):
    from rasterio.warp import reproject, Resampling
    from shapely.geometry import shape as shp_shape
    geoms_out = []
    ext = os.path.splitext(river_path.lower())[1]
    if ext in (".tif", ".tiff"):
        with rasterio.open(river_path) as src:
            arr = src.read(1)
            nod = src.nodata
            if nod is not None:
                arr = np.where(arr == nod, 0, arr)
            dst = np.zeros(ref_shape, dtype=np.uint8)
            reproject(
                source=(arr > 0).astype(np.uint8),
                destination=dst,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=ref_transform,
                dst_crs=ref_crs,
                src_nodata=0,
                dst_nodata=0,
                resampling=Resampling.nearest)
        mask = dst.astype(np.uint8)
        for geom, val in shapes(mask, mask=mask, transform=ref_transform):
            if val == 1:
                g = shp_shape(geom)
                if not g.is_empty:
                    geoms_out.append(g)
        return geoms_out  # já no ref_crs
    gdf = gpd.read_file(river_path)
    if gdf.empty:
        return []
    if gdf.crs is None:
        raise ValueError("Vetor de rios sem CRS.")
    gdf = gdf.to_crs(ref_crs)
    for g in gdf.geometry:
        if g is None or g.is_empty:
            continue
        try:
            if not g.is_valid:
                g = g.buffer(0)
        except Exception:
            pass
        if g is not None and not g.is_empty:
            geoms_out.append(g)
    return geoms_out


def calculate_susceptibility(path_handraw, path_mrvbfraw, path_rivermask, path_rfmodel,path_susc, BUFFER_M, MRVBF_HIGH_LEVEL, CHUNK_PRED, K=5):
    from joblib import load
    from threadpoolctl import threadpool_limits
    spinner = log_loading(loading, "Calculating susceptibility...")
    for var in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(var, "1")
    hds = rasterio.open(path_handraw)
    H, W = hds.height, hds.width
    transform, crs = hds.transform, hds.crs
    hand = hds.read(1).astype(np.float32)
    if hds.nodata is not None:
        hand[hand == hds.nodata] = np.nan
    mds = rasterio.open(path_mrvbfraw)
    vrt_mrv = rasterio.vrt.WarpedVRT(
        mds, crs=crs, transform=transform, width=W, height=H,
        resampling=Resampling.bilinear)
    mrv = vrt_mrv.read(1).astype(np.float32)
    nod_mrv = vrt_mrv.nodata if vrt_mrv.nodata is not None else mds.nodata
    if nod_mrv is not None:
        mrv = np.where(mrv == nod_mrv, np.nan, mrv)
    mrv[~np.isfinite(mrv)] = np.nan  # garante NaN

    def _river_core_full():
        ext = os.path.splitext(path_rivermask.lower())[1]
        if ext in (".tif", ".tiff"):
            rsrc = rasterio.open(path_rivermask)
            vrt_riv = rasterio.vrt.WarpedVRT(
                rsrc, crs=crs, transform=transform, width=W, height=H,
                resampling=Resampling.nearest)
            arr = vrt_riv.read(1)
            nod = vrt_riv.nodata if vrt_riv.nodata is not None else rsrc.nodata
            if nod is not None:
                arr = np.where(arr == nod, 0, arr)
            core = (arr > 0)
            vrt_riv.close(); rsrc.close()
            return core
        else:
            gdf = gpd.read_file(path_rivermask)
            if gdf.empty:
                return np.zeros((H, W), dtype=bool)
            if gdf.crs is None:
                raise ValueError("Vetor de rios sem CRS.")
            gdf = gdf.to_crs(crs)
            union = unary_union(gdf.geometry)
            if union is None or union.is_empty:
                return np.zeros((H, W), dtype=bool)
            mk = rasterize(
                [(union, 1)], out_shape=(H, W), transform=transform,
                fill=0, dtype="uint8", all_touched=True)
            return mk.astype(bool)
    river_core = _river_core_full()
    valid = np.isfinite(hand) & np.isfinite(mrv)
    n_valid = int(np.count_nonzero(valid))
    if n_valid == 0:
        vrt_mrv.close(); mds.close(); hds.close()
        raise RuntimeError("Sem píxeis válidos (verifique overlap/CRS/NoData dos rasters).")
    model = load(os.path.join(path_rfmodel, "model_hgbr.joblib"))
    feat_order = json.load(open(os.path.join(path_rfmodel, "feature_order.json"), "r", encoding="utf-8"))["feature_names"]
    thresholds_json = json.load(open(os.path.join(path_rfmodel, "score_thresholds.json"), "r", encoding="utf-8"))
    ps = thresholds_json["proto"]["signature"]["p"]

    def _px_m(tr):
        return float((abs(tr.a) + abs(tr.e))/2.0)
    px_m = _px_m(transform)

    dist_pix = distance_transform_edt(~river_core)
    max_pix = int(np.ceil(BUFFER_M / max(px_m, 1e-6))) + 1
    dist_pix = np.minimum(dist_pix, max_pix).astype(np.float32)
    dist_m = dist_pix * px_m
    log_dst = np.log1p(dist_m).astype(np.float32)
    in_buffer = (dist_m <= float(BUFFER_M)).astype(np.float32)
    k = max(1, int(round(float(BUFFER_M) / max(px_m, 1e-6))) * 2 + 1)
    mrv_high = (np.isfinite(mrv) & (mrv >= float(MRVBF_HIGH_LEVEL))).astype(np.float32)
    plain_frac100 = uniform_filter(mrv_high, size=k, mode="nearest")
    m_buf = mrv[(in_buffer > 0) & np.isfinite(mrv)]
    ctx_planarity = float(np.mean(m_buf >= float(MRVBF_HIGH_LEVEL))) if m_buf.size else 0.0
    ctx_mrvbf_p90 = float(np.percentile(m_buf, 90)) if m_buf.size else 0.0
    need = set(feat_order)
    mu_hand = sd_hand = None
    hand_z = None
    hand_rank = None
    if "HAND_z" in need:
        hv = hand[np.isfinite(hand)]
        mu_hand = float(np.nanmean(hv)) if hv.size else 0.0
        sd_hand = float(np.nanstd(hv) + 1e-6) if hv.size else 1.0
        hand_z = ((hand - mu_hand) / sd_hand).astype(np.float32)
    if "HAND_rank" in need:
        hv = hand[np.isfinite(hand)]
        if hv.size:
            hs = np.sort(hv)
            idx_valid = np.searchsorted(hs, hand[np.isfinite(hand)], side="right").astype(np.float32)
            hand_rank = np.zeros_like(hand, dtype=np.float32)
            hand_rank[np.isfinite(hand)] = idx_valid / float(hs.size)
        else:
            hand_rank = np.zeros_like(hand, dtype=np.float32)
    feat_arrays = {}
    if "HAND" in need: feat_arrays["HAND"] = hand
    if "MRVBF" in need: feat_arrays["MRVBF"] = mrv
    if "in_channel" in need: feat_arrays["in_channel"] = river_core.astype(np.float32)
    if "dist_to_channel_m" in need: feat_arrays["dist_to_channel_m"] = dist_m
    if "log_dist_m" in need: feat_arrays["log_dist_m"] = log_dst
    if "in_buffer" in need: feat_arrays["in_buffer"] = in_buffer
    if "plain_frac100" in need: feat_arrays["plain_frac100"] = plain_frac100
    if "HAND_scaled_1" in need:
        feat_arrays["HAND_scaled_1"] = hand / (1.0 + 0.75*plain_frac100 + 1e-6)
    if "HAND_scaled_2" in need:
        feat_arrays["HAND_scaled_2"] = hand * (1.0 - 0.50*plain_frac100)
    if "HAND_eff" in need:
        feat_arrays["HAND_eff"] = hand / (1e-3 + plain_frac100)
    if "HANDxMRVBF" in need:
        feat_arrays["HANDxMRVBF"] = hand * mrv
    if "HAND_z" in need:
        feat_arrays["HAND_z"] = hand_z
    if "HAND_rank" in need:
        feat_arrays["HAND_rank"] = hand_rank
    score = np.full((H, W), np.nan, dtype=np.float32)
    idx_all = np.flatnonzero(valid.ravel())

    def _build_X_chunk(idxs_flat):
        cols = []
        for name in feat_order:
            if name == "ctx_planarity":
                cols.append(np.full(idxs_flat.size, ctx_planarity, np.float32))
            elif name == "ctx_mrvbf_p90":
                cols.append(np.full(idxs_flat.size, ctx_mrvbf_p90, np.float32))
            else:
                col = feat_arrays[name].ravel()[idxs_flat].astype(np.float32, copy=False)
                cols.append(col)
        return np.column_stack(cols).astype(np.float32, copy=False)

    with threadpool_limits(limits=1, user_api="blas"), \
         threadpool_limits(limits=1, user_api="openmp"):
        s = 0
        while s < idx_all.size:
            e = min(s + CHUNK_PRED, idx_all.size)
            sel = idx_all[s:e]
            Xb = _build_X_chunk(sel)
            yb = model.predict(Xb).astype(np.float32, copy=False)
            score.ravel()[sel] = yb
            s = e
    sv = score[valid]
    if sv.size == 0:
        vrt_mrv.close(); mds.close(); hds.close()
        raise RuntimeError("Score sem válidos após predição.")
    sig_new = np.quantile(sv, np.array(ps, dtype=float)/100.0).astype(float)
    cuts, alpha, proto_keys = mix_cuts_by_proto(thresholds_json, K, sig_new, allow_extrapolation=True)
    if cuts is None:
        vrt_mrv.close(); mds.close(); hds.close()
        raise RuntimeError("Cortes 'proto' indisponíveis em score_thresholds.json.")
    out_z = np.full((H, W), 255, dtype=np.uint8)
    z = np.digitize(sv, cuts) + 1
    z = (K + 1) - z
    z = np.clip(z, 1, K).astype(np.uint8)
    out_z[valid] = z
    out_z[river_core & valid] = K
    out_profile = hds.profile.copy()
    out_profile.update(dtype=rasterio.uint8, count=1, nodata=255, compress="deflate")
    os.makedirs(os.path.dirname(path_susc) or ".", exist_ok=True)
    with rasterio.open(path_susc, "w", **out_profile) as dst:
        dst.write(out_z, 1)
        dst.update_tags(
            DESCRIPTION=f"Susceptibility 1..{K}; 1=least critical, {K}=most critical; forced {K} on river core",
            BUFFER_M=str(BUFFER_M),
            MRVBF_HIGH_LEVEL=str(MRVBF_HIGH_LEVEL),
            CUT_POLICY="proto",
            K=str(K),
            FEATURES=json.dumps(feat_order, ensure_ascii=False),
            LABEL_ORIENTATION="1=least_critical;K=most_critical",
            PROTO_KEYS=(json.dumps(proto_keys) if proto_keys else ""),
            PROTO_ALPHA=(f"{alpha:.6f}" if alpha is not None else ""))
    vrt_mrv.close(); mds.close(); hds.close()
    spinner()
    return out_z


def _reproject_match_array(src_arr, src_prof, dst_transform, dst_crs, dst_height, dst_width, resampling=Resampling.nearest):
    dst = np.full((dst_height, dst_width), 0, dtype=src_arr.dtype)
    reproject(
        source=src_arr,
        destination=dst,
        src_transform=src_prof['transform'],
        src_crs=src_prof['crs'],
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        src_nodata=src_prof.get('nodata', None),
        dst_nodata=0,
        resampling=resampling)
    return dst


def _cartopy_crs_from_rasterio(crs):
    try:
        epsg = crs.to_epsg()
        if epsg:
            return ccrs.epsg(epsg)
    except Exception:
        pass
    try:
        if crs.is_geographic:
            return ccrs.PlateCarree()
    except Exception:
        pass
    return ccrs.PlateCarree()


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
        H, W = src.height, src.width
    susc_masked = np.ma.masked_equal(susc_data, susc_nodata)
    with rasterio.open(rios_path) as rio_src:
        rios_arr = rio_src.read(1)
        rios_prof = rio_src.profile.copy()
    rios_match = _reproject_match_array(
        rios_arr, rios_prof,
        dst_transform=susc_transform, dst_crs=susc_crs,
        dst_height=H, dst_width=W,
        resampling=Resampling.nearest)
    rios_mask = np.ma.masked_less_equal(rios_match, 0)
    with rasterio.open(vias_path) as via_src:
        vias_arr = via_src.read(1)
        vias_prof = via_src.profile.copy()
    vias_match = _reproject_match_array(
        vias_arr, vias_prof,
        dst_transform=susc_transform, dst_crs=susc_crs,
        dst_height=H, dst_width=W,
        resampling=Resampling.nearest)
    vias_mask = np.ma.masked_less_equal(vias_match, 0)
    cores = ["#1b5e20", "#a5d6a7", "#ffffb2", "#e6550d", "#a80000"]  # 1..5
    cmap = ListedColormap(cores)
    bounds = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    norm = BoundaryNorm(bounds, cmap.N)
    crs_proj = _cartopy_crs_from_rasterio(susc_crs)
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': crs_proj})
    ax.set_extent(susc_extent, crs=crs_proj)
    ax.imshow(
        susc_masked,
        cmap=cmap, norm=norm,
        transform=crs_proj, extent=susc_extent,
        interpolation='nearest', alpha=0.75)
    ax.imshow(
        rios_mask,
        cmap=ListedColormap(["#66ccff"]),
        alpha=0.8, extent=susc_extent, transform=crs_proj, interpolation='nearest')
    ax.imshow(
        vias_mask,
        cmap=ListedColormap(["#303030"]),
        alpha=0.6, extent=susc_extent, transform=crs_proj, interpolation='nearest')
    legend_labels = ['Very Low', 'Low', 'Moderate', 'High', 'Very High', 'Hydrographic Network', 'Road Network']
    legend_colors = cores + ["#66ccff", "#303030"]
    legend_patches = [Patch(color=cor, label=label) for cor, label in zip(legend_colors, legend_labels)]
    ax.legend(handles=legend_patches, loc='lower right', title='Susceptibility')
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
    log(pasta, f"File: {output_path_} — Preview image of the susceptibility map")
    log_image(output_path, description="Susceptibility Map:")
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
            'name':     nm})
    lines_gdf = gpd.GeoDataFrame(
        named_rows, geometry='geometry', crs=pois.crs
    ) if named_rows else gpd.GeoDataFrame(
        columns=['geometry','type','weight','name'],
        geometry='geometry', crs=pois.crs)
    pois = pd.concat([rest, lines_gdf], ignore_index=True)
    pois = gpd.GeoDataFrame(pois, geometry='geometry', crs=pois.crs)
    pois = pois.reset_index(drop=True)
    pois['poi_id'] = pois.index + 1
    pois['name'] = pois['name'].fillna('').replace('', 'Unnamed')
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
    legend = [Patch(color='blue', label='Regular POIs'), Patch(color='red',  label='Critical POIs')]
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
    ax.set_extent([sw_lng, ne_lng, sw_lat, ne_lat], crs=ccrs.PlateCarree())
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
    census = census_gdf.merge(rho_df[['CD_GEOCODI', 'rho_prime']], on='CD_GEOCODI', how='left')
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
    gdf = sectors_gdf.merge( census_full[['CD_GEOCODI','cv_raw','cv_pct']], on='CD_GEOCODI', how='left')
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

    def _to_float_series(s):
        s = s.astype(str).str.strip()
        s = s.str.replace('−', '-', regex=False).str.replace(',', '.', regex=False)
        s = s.str.replace(r'[^0-9\.\-]+', '', regex=True)
        return pd.to_numeric(s, errors='coerce').astype('float64').fillna(0.0)

    if 'weight' not in pois.columns:
        pois['weight'] = 1.0
    else:
        pois['weight'] = _to_float_series(pois['weight'])
    total_assets = int(len(pois))
    total_weight = float(pois['weight'].sum())
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
            [mapping(geom)], invert=True, transform=transform, out_shape=arr.shape)
        vals = arr[mask]
        susc_values.append(int(vals.max()) if vals.size else np.nan)
    pois['susc'] = susc_values
    crit = pois.loc[(pois['weight'] > 3.0) & (pois['susc'] > 3)]
    num_crit = int(len(crit))
    sum_crit = float(crit['weight'].sum())
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
        dst.set_band_description(7, "interpolated_flag")
        dst.set_band_description(8, "gamma")
        dst.set_band_description(9, "sigma_zeta")
        dst.set_band_description(10, "mu")
        dst.set_band_description(11, "SVCI")
        dst.set_band_description(12, "vulnerability")
    del_file(burn_raster_path)
    print(f"✅ SVCI calculado com sucesso")
    log(pasta, f"File: {output_raster_path} — Raster with SVCI and vulnerability classification")
    return burn_id, vulner, profile


def _align_to_profile(src_arr, src_prof, dst_prof, *, is_class=True):
    if src_prof is None:
        raise ValueError("Profile de origem requerido para alinhar raster.")
    dst = np.full((dst_prof['height'], dst_prof['width']), np.nan, dtype=np.float32)
    reproject(
        source=src_arr.astype(np.float32),
        destination=dst,
        src_transform=src_prof['transform'],
        src_crs=src_prof['crs'],
        dst_transform=dst_prof['transform'],
        dst_crs=dst_prof['crs'],
        src_nodata=src_prof.get('nodata', None),
        dst_nodata=np.nan,
        resampling=Resampling.nearest if is_class else Resampling.bilinear)
    return dst


def compute_risk(burn_id, vulner, prev, base_profile, output_path, *, burn_profile=None, vulner_profile=None):
    print("\n⚙️ Calculando o risco da infraestrutura viária...")
    H, W = base_profile['height'], base_profile['width']
    if burn_id.shape != (H, W):
        burn_id = _align_to_profile(burn_id, burn_profile, base_profile, is_class=True)
    if vulner.shape != (H, W):
        vulner = _align_to_profile(vulner, vulner_profile, base_profile, is_class=True)
    if not (burn_id.shape == vulner.shape == prev.shape):
        raise ValueError("Todos os arrays devem ter o mesmo shape.")
    print("shapes -> burn:", burn_id.shape, "vulner:", vulner.shape, "prev:", prev.shape)
    if not (burn_id.shape == vulner.shape == prev.shape):
        raise ValueError(
            f"Todos os arrays devem ter o mesmo shape. "
            f"burn={burn_id.shape}, vulner={vulner.shape}, prev={prev.shape}")
    nodata = -9999
    mask = (burn_id != 0)
    burn_f = burn_id.astype(np.float32)
    vuln_f = vulner.astype(np.float32)
    susc_f = prev.astype(np.float32)
    if np.issubdtype(prev.dtype, np.integer):
        susc_f[prev == 255] = np.nan
    if np.issubdtype(vulner.dtype, np.integer):
        vuln_f[vulner == 255] = np.nan
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
        dst.set_band_description(2, "vulnerability")
        dst.set_band_description(3, "susceptibility")
        dst.set_band_description(4, "risk")
    print("✅ Risco calculado com sucesso")
    log(pasta, f"File: {output_path} — Final raster map with flood risk to road infrastructure")


def visualizar_risco(risk_raster_path, bbox_coords, output_path):
    print("\n⚙️ Gerando mapa de risco...")
    sw_lng, sw_lat, ne_lng, ne_lat = bbox_coords
    lat_diff = ne_lat - sw_lat
    lon_diff = ne_lng - sw_lng
    max_diff = max(lat_diff, lon_diff)
    if max_diff < 0.005: zoom = 17
    elif max_diff < 0.01: zoom = 16
    elif max_diff < 0.02: zoom = 15
    elif max_diff < 0.05: zoom = 14
    elif max_diff < 0.1: zoom = 13
    elif max_diff < 0.5: zoom = 12
    elif max_diff < 1.0: zoom = 11
    elif max_diff < 2.0: zoom = 10
    elif max_diff < 5.0: zoom = 9
    elif max_diff < 10.0: zoom = 8
    else: zoom = 6
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
    ax.set_extent([sw_lng, ne_lng, sw_lat, ne_lat], crs=ccrs.PlateCarree())
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
        1: 'Very Low',
        2: 'Low',
        3: 'Moderate',
        4: 'High',
        5: 'Very High',}
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
    ax.legend(handles=legend_elems, loc='lower left', title='Risk Levels')
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
    texto = {5: 'Very High', 4: 'High', 3: 'Moderate', 2: 'Low', 1: 'Very Low'}
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
    elif max_diff < 0.01: zoom = 16
    elif max_diff < 0.02: zoom = 15
    elif max_diff < 0.05: zoom = 14
    elif max_diff < 0.1: zoom = 13
    elif max_diff < 0.5: zoom = 12
    elif max_diff < 1.0: zoom = 11
    elif max_diff < 2.0: zoom = 10
    elif max_diff < 5.0: zoom = 9
    elif max_diff < 10.0: zoom = 8
    else: zoom = 6
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
        'Very Low': '#006400',
        'Low':       '#7CFC00',
        'Moderate':    '#FFD700',
        'High':        '#FF8C00',
        'Very High':  '#8B0000',}
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


def _finalize_and_cleanup(total_segundos):
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
    del_pasta("cache")
    del_file("dem_tmp.tif")
    del_file("Flow_accumulation_withnodata.tif")
    del_file(path_geohydro)
    del_file(path_georoads)


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
    webview.start(gui='edgechromium', icon=ICON_FILE, debug=False)
    north_east_lat, north_east_lng, south_west_lat, south_west_lng = coordinates()

    global RUN_MODE
    RUN_MODE = prompt_module_choice()

    # Iniciar o PRIORI
    mostrar_tela_logs(north_east_lat, north_east_lng, south_west_lat, south_west_lng)


def run_priori(north_east_lat, north_east_lng, south_west_lat, south_west_lng, run_mode="full"):
    bbox = (south_west_lng, south_west_lat, north_east_lng, north_east_lat)

    ensure_models()

    # Obter o DEM
    get_copernicus_dem(
        coord_1=south_west_lng,
        coord_2=south_west_lat,
        coord_3=north_east_lng,
        coord_4=north_east_lat,
        output_dem=path_dem)

    # Reprojetar o DEM e calcular o fluxo acumulado
    calculate_flow_accumulation(
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
        output_path=path_handraw,
        bbox_ext=bbox)
    calcular_mrvbf(
        dem_path=path_dem,
        output_path=path_mrvbfraw,
        bbox_ext=bbox)

    # Cálculo suscetibilidade
    prev = calculate_susceptibility(
        path_handraw=path_handraw,
        path_mrvbfraw=path_mrvbfraw,
        path_rivermask=path_hydro,
        path_rfmodel=path_rfmodel,
        path_susc=path_susc,
        BUFFER_M=max_chunk_suscept,
        MRVBF_HIGH_LEVEL=mrvbf_plain_level,
        CHUNK_PRED=river_buffer_suscept)
    visualizar_suscetibilidade(
        susc_path_=path_susc,
        rios_path_=path_hydro,
        vias_path_=path_rasroads,
        output_path_=path_susimg)

    # Verificar run mode
    if run_mode == "susc_only":
        total_segundos = int((datetime.now() - time_start).total_seconds()) if time_start else 0
        _finalize_and_cleanup(total_segundos)
        return

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
    census = gpd.read_file(path_census, engine="fiona")
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
    with rasterio.open(path_susc) as src_susc:
        susc_profile = src_susc.profile.copy()
    compute_risk(
        burn_id=burn_id,
        vulner=vulner,
        prev=prev,
        base_profile=susc_profile,
        output_path=path_risk,
        burn_profile=profile,
        vulner_profile=profile)

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

    parser = argparse.ArgumentParser(description="PRIORI — Protocol for Road Infrastructure Operational Risk due to Inundation")
    parser.add_argument("--version", action="store_true", help="Show PRIORI version and exit")
    args = parser.parse_args()
    if args.version:
        print(__version__)
        raise SystemExit(0)

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
    path_mrvbfraw = "Resultados/mrvbf_raw.tif"              # MRVBF conforme metodologia original
    path_susc = "Resultados/susceptibility.tif"             # Arquivo final da suscetibilidade com suavização
    path_susimg = "Resultados/susceptibility.png"           # Imagem da suscetibilidade da região
    path_geopoi = "Resultados/pois.geojson"                 # Geojson com localização da infraestrutura funcional
    path_xlsxpoi = "Resultados/pois_info.xlsx"              # ID, nome, tipo, peso
    path_census = "Database/BR_Census.gpkg"                 # Base de dados IBGE 2010
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
    path_rfmodel = "Database"                               # Pasta: artefatos do modelo random forest

    # Parâmetros ajustáveis
    max_chunk_suscept = 300_000
    mrvbf_plain_level = 6.0
    river_buffer_suscept = 100

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
