# codexra.py
import streamlit as st
from PIL import Image
import numpy as np
import colorsys
import json
import io

# ----------------- CONFIG -----------------
st.set_page_config(page_title="CodexRa - Decode the Light Within", layout="wide", page_icon="🌈")

# Custom CSS for smaller, centered layout
st.markdown(
    """
    <style>
    .main {
        max-width: 700px;
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
        results.append(((r,g,b), pct))
    return results

# ---------- COLOR SCORING ----------
def score_color(rgb, pct):
    """Hybrid score: area + saturation + brightness."""
    h, s, v = rgb_to_hsv_deg(*rgb)
    # Ignore nearly grey / desaturated colors
    if s < 0.15 and v > 0.15:
        return pct * 0.2
    return (pct**0.7) * (0.5 + 0.5*s) * (0.4 + 0.6*v)

def choose_dominant_and_accents(palette, n_dom=3, n_accents=2):
    scored = [(rgb, pct, score_color(rgb, pct)) for rgb, pct in palette]
    # Dominants: top 3 by score
    dominants = sorted(scored, key=lambda x: x[2], reverse=True)[:n_dom]
    # Accents: most saturated + bright from rest
    rest = [x for x in scored if x not in dominants]
    accents = sorted(rest, key=lambda x: (rgb_to_hsv_deg(*x[0])[1], rgb_to_hsv_deg(*x[0])[2]), reverse=True)[:n_accents]
    return dominants, accents
# -----------------------------------

def safe_get_meaning(key):
    return color_db.get(key.lower(), {})

def make_summary_text(shorts):
    return " • ".join(shorts)

# ----------------- UI -----------------
st.title("🌈 CodexRa — Decode the Light Within")
st.write("Upload an image and CodexRa will extract 3 dominant colors and 2 accents, then classify them into hues with quick + extended interpretations.")

uploaded_file = st.file_uploader("Upload image (jpg/png)", type=["jpg","jpeg","png"])

if not uploaded_file:
    st.info("Upload an image to start analysis.")
    st.stop()

try:
    image = Image.open(uploaded_file).convert("RGB")
except Exception:
    st.error("Could not open image. Try another file.")
    st.stop()

st.image(image, caption="Analyzed image", use_container_width=True)

# extract palette (more colors for better clustering)
palette = get_palette_pillow(image, colors=24)

# pick dominants & accents
dominants, accents = choose_dominant_and_accents(palette)

# Show dominants
st.header("🎨 Dominant colors")
summary_shorts = []
cols = st.columns(len(dominants))
for i, (rgb, pct, score) in enumerate(dominants):
    hexc = rgb_to_hex(rgb)
    key = hexc
    meaning = safe_get_meaning(key)
    short = meaning.get("short", "")
    with cols[i]:
        st.markdown(f"<div class='color-box' style='background:{hexc}'></div>", unsafe_allow_html=True)
        st.markdown(f"`{hexc}` {pct*100:.1f}%")
    summary_shorts.append(short)

# Show accents
if accents:
    st.header("✨ Accent colors")
    cols = st.columns(len(accents))
    for i, (rgb, pct, score) in enumerate(accents):
        hexc = rgb_to_hex(rgb)
        with cols[i]:
            st.markdown(f"<div class='color-box' style='background:{hexc}'></div>", unsafe_allow_html=True)
            st.markdown(f"`{hexc}` {pct*100:.1f}%")

# Combined summary
if summary_shorts:
    st.header("🌀 Combined summary")
    st.markdown("**Quick combined:** " + make_summary_text(summary_shorts))
