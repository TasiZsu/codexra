# codexra.py
import streamlit as st
from PIL import Image
import numpy as np
import colorsys
import json
import io

# ----------------- CONFIG -----------------
st.set_page_config(page_title="CodexRa - Decode the Light Within",
                   layout="centered", page_icon="🌈")

# Custom CSS for centered, max-width layout
st.markdown(
    """
    <style>
    .main {
        max-width: 900px;
        margin: auto;
        padding-top: 2rem;
    }
    .color-box {
        width: 60px;
        height: 60px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

COLORS_JSON = "colors.json"

# ----------------- HELPERS -----------------
def load_color_db(path=COLORS_JSON):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Could not load {path}: {e}")
        return {}

color_db = load_color_db()

def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def rgb_to_hsv_deg(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    return h * 360.0, s, v

def classify_by_hue(rgb):
    """Very simple classifier to connect to color_db keys"""
    h, s, v = rgb_to_hsv_deg(*rgb)
    if v <= 0.06:
        return "black"
    if s <= 0.12 and v >= 0.92:
        return "white"
    if s <= 0.18:
        return "grey"
    if (h >= 10 and h < 45) and v < 0.65:
        return "brown"
    if h >= 150 and h < 185 and s > 0.18:
        return "turquoise"
    if (h >= 320 and h < 345) or (h >= 275 and h < 320):
        return "violet"
    if h < 15 or h >= 345:
        return "red"
    if 15 <= h < 45:
        return "orange"
    if 45 <= h < 65:
        return "yellow"
    if 65 <= h < 150:
        return "green"
    if 180 <= h < 240:
        return "blue"
    if 240 <= h < 275:
        return "indigo"
    if 320 <= h < 345:
        return "pink"
    return "unknown"

def get_palette_pillow(image: Image.Image, colors=24):
    """Return list of ((r,g,b), pct) using Pillow adaptive palette."""
    img = image.convert("RGB")
    w, h = img.size
    max_dim = 400
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)

    pal = img.convert("P", palette=Image.ADAPTIVE, colors=colors)
    palette = pal.getpalette()
    color_counts = pal.getcolors()
    if not color_counts:
        arr = np.array(img).reshape(-1,3)
        vals, counts = np.unique(arr, axis=0, return_counts=True)
        total = counts.sum()
        return [(tuple(vals[i].tolist()), counts[i]/total) for i in np.argsort(-counts)[:colors]]

    total = sum(c[0] for c in color_counts)
    color_counts.sort(reverse=True, key=lambda x: x[0])
    results = []
    for count, idx in color_counts[:colors]:
        r = palette[idx*3]
        g = palette[idx*3 + 1]
        b = palette[idx*3 + 2]
        pct = count / total
