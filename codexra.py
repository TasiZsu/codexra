# codexra.py
import streamlit as st
from PIL import Image
import numpy as np
import colorsys
import json
import io

# ----------------- CONFIG -----------------
st.set_page_config(page_title="CodexRa - Decode the Light Within", layout="centered", page_icon="🌈")

# 🌌 Custom background image (CSS injection)
page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
[data-testid="stHeader"] {background: rgba(0,0,0,0);}
[data-testid="stToolbar"] {visibility: hidden;}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# Path to your colors.json
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
    r, g, b = rgb
    h, s, v = rgb_to_hsv_deg(r, g, b)

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
    if (h >= 320 and h < 345) or (h >= 275 and h < 320 and r > 120 and b > 120):
        if h >= 320 and s > 0.25:
            return "magenta"
        if 275 <= h < 320:
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
    if 275 <= h < 320:
        return "violet"
    if 320 <= h < 345:
        return "pink"
    return "white"

def get_palette_pillow(image: Image.Image, colors=8):
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
        arr = np.array(img).reshape(-1, 3)
        vals, counts = np.unique(arr, axis=0, return_counts=True)
        total = counts.sum()
        items = []
        idxs = np.argsort(-counts)[:colors]
        for i in idxs:
            items.append((tuple(vals[i].tolist()), counts[i]/total))
        return items

    total = sum(c[0] for c in color_counts)
    color_counts.sort(reverse=True, key=lambda x: x[0])
    results = []
    for count, idx in color_counts[:colors]:
        r = palette[idx*3]
        g = palette[idx*3 + 1]
        b = palette[idx*3 + 2]
        pct = count / total
        results.append(((r, g, b), pct))
    return results

def choose_dominant_and_accents(palette, n_dom=3, n_accents=2):
    """
    Palette mode:
    - 3 dominant colors: from the top 3 most represented hue groups.
    - 2 accents: from smaller groups with high saturation/brightness.
    """

    # 1. Csoportosítás
    groups = {}
    for (rgb, pct) in palette:
        key = classify_by_hue(rgb)
        if key not in groups:
            groups[key] = {"total_pct": 0, "candidates": []}
        groups[key]["total_pct"] += pct
        groups[key]["candidates"].append((rgb, pct))

    # 2. Legjellemzőbb szín minden csoportból
    group_reps = []
    for key, data in groups.items():
        rgb, pct = max(data["candidates"], key=lambda x: x[1])  # legdominánsabb árnyalat a csoportban
        group_reps.append((rgb, pct, key, data["total_pct"]))

    # 3. Rendezés: csoport összes arány szerint
    group_reps.sort(key=lambda x: -x[3])

    # 4. Domináns = top 3 külön csoport
    dominants = group_reps[:n_dom]

    # 5. Accents = maradék, de élénk színek
    rest = group_reps[n_dom:]
    scored = []
    for (rgb, pct, key, total_pct) in rest:
        h, s, v = rgb_to_hsv_deg(*rgb)
        score = s * 0.7 + v * 0.3  # élénkség súlyozva
        scored.append((rgb, pct, key, total_pct, score))
    scored.sort(key=lambda x: -x[4])
    accents = [(rgb, pct, key, total_pct) for (rgb, pct, key, total_pct, _) in scored[:n_accents]]

    return dominants, accents


def safe_get_meaning(key):
    if not isinstance(key, str):
        key = str(key)
    return color_db.get(key.lower(), {})

def make_summary_text(shorts):
    return " • ".join(shorts)

# ----------------- UI -----------------
st.title("🌈 CodexRa — Decode the Light Within")
st.write("Upload an image and CodexRa will extract dominant + accent colors, classify them into hue groups, and show symbolic, chakra, alchemical, and mythological meanings.")

uploaded_file = st.file_uploader("Upload image (jpg/png)", type=["jpg","jpeg","png"])

if uploaded_file:
    try:
        image = Image.open(uploaded_file).convert("RGB")
    except Exception as e:
        st.error("Could not open image. Try another file.")
        st.stop()
else:
    st.info("Upload an image to start analysis.")
    st.stop()

st.image(image, caption="Analyzed image", width=900)

palette = get_palette_pillow(image, colors=10)
dominants, accents = choose_dominant_and_accents(palette, n_dom=3, n_accents=2)

# Dominant colors
st.header("🎨 Dominant colors")
summary_shorts = []

for i, item in enumerate(dominants, start=1):
    rgb, pct, key, total_pct = item
    hexc = rgb_to_hex(rgb)
    meaning = safe_get_meaning(key)
    short = meaning.get("quick", "No quick meaning.")
    long = meaning.get("extended", "No extended meaning available.")
    chakra = meaning.get("chakra", "")
    element = meaning.get("element", "")
    wavelength = meaning.get("wavelength_nm", "")
    frequency = meaning.get("frequency_thz", "")
    mythology = meaning.get("mythology", "")
    alchemy = meaning.get("alchemy", "")

    st.markdown(f"### {i}. {key.capitalize()} — `{hexc}`  ({total_pct*100:.1f}% of image)")
    cols = st.columns([1,3])
    with cols[0]:
        st.markdown(
            f"<div style='width:100%;height:80px;border-radius:8px;background:{hexc};border:1px solid rgba(255,255,255,0.08)'></div>",
            unsafe_allow_html=True
        )
    with cols[1]:
        if chakra: st.markdown(f"**Chakra:** {chakra}")
        if element: st.markdown(f"**Element:** {element}")
        if wavelength and frequency:
            st.markdown(f"**Wave:** {wavelength} nm • {frequency} THz")
        st.markdown(f"**Quick:** {short}")
        with st.expander("🔮 Extended meaning"):
            st.write(long)
        if mythology or alchemy:
            with st.expander("📜 Mythology & Alchemy"):
                if mythology: st.write(f"**Mythology:** {mythology}")
                if alchemy: st.write(f"**Alchemy:** {alchemy}")

    summary_shorts.append(short)

# Accent colors
if accents:
    st.header("✨ Accent colors")
    for item in accents:
        rgb, pct, key, total_pct = item
        hexc = rgb_to_hex(rgb)
        meaning = safe_get_meaning(key)
        short = meaning.get("quick", "")
        long = meaning.get("extended", "")
        chakra = meaning.get("chakra", "")
        element = meaning.get("element", "")
        mythology = meaning.get("mythology", "")
        alchemy = meaning.get("alchemy", "")

        cols = st.columns([1,3])
        with cols[0]:
            st.markdown(
                f"<div style='width:100%;height:60px;border-radius:8px;background:{hexc};border:1px solid rgba(255,255,255,0.08)'></div>",
                unsafe_allow_html=True
            )
        with cols[1]:
            st.markdown(f"**{key.capitalize()}** — `{hexc}` ({total_pct*100:.1f}% of image)")
            if chakra: st.markdown(f"**Chakra:** {chakra}")
            if element: st.markdown(f"**Element:** {element}")
            if short: st.markdown(f"**Quick:** {short}")
            if long:
                with st.expander("🔮 Extended meaning"):
                    st.write(long)
            if mythology or alchemy:
                with st.expander("📜 Mythology & Alchemy"):
                    if mythology: st.write(f"**Mythology:** {mythology}")
                    if alchemy: st.write(f"**Alchemy:** {alchemy}")

# Combined summary
st.header("🌀 Combined summary")
if summary_shorts:
    st.markdown("**Quick combined:** " + make_summary_text(summary_shorts))
else:
    st.info("No colors found to summarize.")

