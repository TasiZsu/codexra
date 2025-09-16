# codexra.py
import streamlit as st
from PIL import Image
import numpy as np
import colorsys
import json
import io
from collections import OrderedDict

# ----------------- CONFIG -----------------
st.set_page_config(page_title="CodexRa - Decode the Light Within", layout="wide", page_icon="🌈")

# Path to your colors.json in the repo
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
    # returns h (0..360), s (0..1), v (0..1)
    h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    return h * 360.0, s, v

def classify_by_hue(rgb):
    """Return a color key matching our DB (lowercase)."""
    r, g, b = rgb
    h, s, v = rgb_to_hsv_deg(r, g, b)

    # black / white / grey rules
    if v <= 0.06:
        return "black"
    if s <= 0.12 and v >= 0.92:
        return "white"
    if s <= 0.18:
        return "grey"

    # brown detection: orange-ish hue + low value
    if (h >= 10 and h < 45) and v < 0.65:
        return "brown"
    # turquoise: green-blue zone with moderate hue
    if h >= 150 and h < 185 and s > 0.18:
        return "turquoise"
    # magenta/purple detection
    if (h >= 320 and h < 345) or (h >= 275 and h < 320 and r>120 and b>120):
        # use magenta for hot pink-like hues
        if h >= 320 and s > 0.25:
            return "magenta"
        if 275 <= h < 320:
            return "violet"
    # basic hue ranges
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
    # fallback
    return "white"

def get_palette_pillow(image: Image.Image, colors=8):
    """
    Return palette list [(r,g,b), pct] using Pillow adaptive palette.
    """
    img = image.convert("RGB")
    w, h = img.size
    # downscale for speed
    max_dim = 400
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)

    pal = img.convert("P", palette=Image.ADAPTIVE, colors=colors)
    palette = pal.getpalette()  # [r,g,b, r,g,b, ...]
    color_counts = pal.getcolors()  # list of (count, palette_index)
    if not color_counts:
        arr = np.array(img).reshape(-1,3)
        vals, counts = np.unique(arr, axis=0, return_counts=True)
        total = counts.sum()
        items = []
        idxs = np.argsort(-counts)[:colors]
        for i in idxs:
            items.append((tuple(vals[i].tolist()), counts[i]/total))
        return items

    total = sum(c[0] for c in color_counts)
    # sort desc
    color_counts.sort(reverse=True, key=lambda x: x[0])
    results = []
    for count, idx in color_counts[:colors]:
        r = palette[idx*3]
        g = palette[idx*3 + 1]
        b = palette[idx*3 + 2]
        pct = count / total
        results.append(((r,g,b), pct))
    return results

def choose_dominant_and_accents(palette, n_dom=3, n_accents=2):
    """
    palette: list of ((r,g,b), pct) sorted descending by pct
    returns: dominants list, accents list
    """
    # ensure palette sorted by pct
    palette_sorted = sorted(palette, key=lambda x: -x[1])
    dominants = palette_sorted[:n_dom]
    # for accents, pick colors with higher saturation among the rest
    rest = palette_sorted[n_dom:]
    # compute saturation for each candidate
    sat_list = []
    for (rgb, pct) in rest:
        h, s, v = rgb_to_hsv_deg(*rgb)
        sat_list.append(((rgb, pct), s))
    sat_list.sort(key=lambda x: -x[1])
    accents = [item[0] for item in sat_list[:n_accents]]
    # fallback if not enough accents: take next from rest by pct
    if len(accents) < n_accents:
        for (rgb,pct) in rest:
            if (rgb,pct) not in accents:
                accents.append((rgb,pct))
                if len(accents) >= n_accents:
                    break
    return dominants, accents

def safe_get_meaning(key):
    k = key.lower()
    return color_db.get(k, {})

def make_summary_text(shorts):
    # join compressed summary
    return " • ".join(shorts)

# ----------------- UI -----------------
st.title("🌈 CodexRa — Decode the Light Within")
st.write("Upload an image and CodexRa will extract the 3 dominant colors and 2 accent colors, classify them into main/intermediate hues, and show quick + extended interpretations (chakra, symbolic, scientific).")

col1, col2 = st.columns([3,1])
with col2:
    st.markdown("**Settings**")
    colors_count = st.slider("Palette colors (quality vs speed)", 5, 12, 8)
    sample_button = st.button("Use sample gradient")

uploaded_file = st.file_uploader("Upload image (jpg/png)", type=["jpg","jpeg","png"])

if sample_button:
    # generate sample gradient image
    w, h = 800, 480
    c = Image.new("RGB", (w,h))
    draw = c.load()
    for x in range(w):
        for y in range(h):
            r = int(255 * (x / w))
            g = int(200 * (y / h))
            b = int(255 * (1 - x / w))
            draw[x,y] = (r,g,b)
    uploaded_file = io.BytesIO()
    c.save(uploaded_file, format="PNG")
    uploaded_file.seek(0)
    uploaded_image = Image.open(uploaded_file).convert("RGB")
    image = uploaded_image
else:
    if uploaded_file:
        try:
            image = Image.open(uploaded_file).convert("RGB")
        except Exception as e:
            st.error("Could not open image. Try another file.")
            st.stop()
    else:
        st.info("Upload an image to start analysis (or use the sample).")
        st.stop()

st.image(image, caption="Analyzed image", use_column_width=True)

# extract palette
palette = get_palette_pillow(image, colors=colors_count)

# pick dominants & accents
dominants, accents = choose_dominant_and_accents(palette, n_dom=3, n_accents=2)

# Display dominants
st.header("🎨 Dominant colors (3) — separate blocks")
summary_shorts = []

for i, (rgb, pct) in enumerate(dominants, start=1):
    hexc = rgb_to_hex(rgb)
    key = classify_by_hue(rgb)
    meaning = safe_get_meaning(key)
    short = meaning.get("short", "No short meaning.")
    long = meaning.get("long", "No extended meaning available.")
    chakra = meaning.get("chakra", "")

    st.markdown(f"### {i}. {key.capitalize()}  — `{hexc}`  ({pct*100:.1f}%)")
    cols = st.columns([1,3])
    with cols[0]:
        st.markdown(f"<div style='width:100%;height:80px;border-radius:8px;background:{hexc};border:1px solid rgba(255,255,255,0.08)'></div>", unsafe_allow_html=True)
    with cols[1]:
        if chakra:
            st.markdown(f"**Chakra:** {chakra}")
        st.markdown(f"**Quick:** {short}")
        with st.expander("🔮 More about this color"):
            st.write(long)

    summary_shorts.append(short)

# Display accent colors
if accents:
    st.header("✨ Accent colors (2) — high saturation / contrast")
    acc_cols = []
    for (rgb, pct) in accents:
        hexc = rgb_to_hex(rgb)
        key = classify_by_hue(rgb)
        meaning = safe_get_meaning(key)
        short = meaning.get("short", "")
        acc_cols.append(f"{key.capitalize()} `{hexc}` ({pct*100:.1f}%): {short}")
    for a in acc_cols:
        st.markdown("- " + a)

# Combined summary
st.header("🌀 Combined summary")
if summary_shorts:
    st.markdown("**Quick combined:** " + make_summary_text(summary_shorts))
    keys = [classify_by_hue(rgb) for (rgb,_) in dominants]
    human_readable = ", ".join(k.capitalize() for k in keys)
    st.write(f"The image mainly resonates with **{human_readable}** energies. Each color contributes its effect; together they form the energetic fingerprint of the image.")
else:
    st.info("No colors found to summarize.")

# CSV export (optional)
def export_csv(all_colors):
    import csv, tempfile
    csv_rows = [["rank","key","hex","r","g","b","percent","short"]]
    idx = 1
    for (rgb,pct) in dominants:
        key = classify_by_hue(rgb)
        csv_rows.append([idx, key, rgb_to_hex(rgb), rgb[0], rgb[1], rgb[2], f"{pct*100:.2f}", safe_get_meaning(key).get("short","")])
        idx += 1
    for (rgb,pct) in accents:
        key = classify_by_hue(rgb)
        csv_rows.append([idx, key, rgb_to_hex(rgb), rgb[0], rgb[1], rgb[2], f"{pct*100:.2f}", safe_get_meaning(key).get("short","")])
        idx += 1
    # build csv bytes
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(csv_rows)
    return buf.getvalue().encode("utf-8")

st.download_button("Export results (CSV)", data=export_csv(None), file_name="codexra_colors.csv", mime="text/csv")
