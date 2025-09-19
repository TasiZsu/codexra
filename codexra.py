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
    """Simple classifier for mapping to color_db keys"""
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
    if 185 <= h < 250:
        return "blue"
    if 250 <= h < 275:
        return "indigo"
    if 320 <= h < 340:
        return "pink"
    return "neutral"

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

# ---------- COLOR SCORING & BUCKETS ----------
def color_distance(rgb1, rgb2):
    return np.linalg.norm(np.array(rgb1) - np.array(rgb2))

def score_color(rgb, pct, palette):
    h, s, v = rgb_to_hsv_deg(*rgb)
    if s < 0.25 or v < 0.2 or v > 0.95:
        return pct * 0.05
    if len(palette) > 1:
        distances = [color_distance(rgb, other) for (other, _) in palette if not np.array_equal(rgb, other)]
        uniqueness = np.mean(distances) / 255.0
    else:
        uniqueness = 1.0
    return (pct**0.6) * (0.4 + 0.6*s) * (0.5 + 0.5*v) * (0.8 + 0.2*uniqueness)

def bucket_hue(h):
    if h < 20 or h >= 340:
        return "red"
    if 20 <= h < 45:
        return "orange"
    if 45 <= h < 65:
        return "yellow"
    if 65 <= h < 150:
        return "green"
    if 150 <= h < 185:
        return "cyan"
    if 185 <= h < 250:
        return "blue"
    if 250 <= h < 275:
        return "indigo"
    if 275 <= h < 320:
        return "violet"
    if 320 <= h < 340:
        return "pink"
    return "neutral"

def choose_dominant_and_accents(palette, n_dom=3, n_accents=2):
    scored = []
    for rgb, pct in palette:
        h, s, v = rgb_to_hsv_deg(*rgb)
        sc = score_color(rgb, pct, palette)
        scored.append((rgb, pct, sc, h, s, v, bucket_hue(h)))

    # Bucketbe rendezés
    buckets = {}
    for item in scored:
        bucket = item[6]
        if bucket not in buckets:
            buckets[bucket] = []
        buckets[bucket].append(item)

    # Minden bucketből a legjobb score
    best_per_bucket = []
    for bucket, items in buckets.items():
        best = max(items, key=lambda x: x[2])
        best_per_bucket.append(best)

    # Dominánsok: top score külön bucketekből
    dominants = sorted(best_per_bucket, key=lambda x: x[2], reverse=True)[:n_dom]

    # Accent: a maradék bucketekből a legélénkebb színek
    rest = [x for x in best_per_bucket if x not in dominants]
    accents = sorted(rest, key=lambda x: (x[4], x[5]), reverse=True)[:n_accents]

    return dominants, accents
# -----------------------------------

def safe_get_meaning(key):
    return color_db.get(key.lower(), {})

def make_summary_text(shorts):
    return " • ".join(shorts)

# ----------------- UI -----------------
st.title("🌈 CodexRa — Decode the Light Within")
st.write("Upload an image and CodexRa will extract diverse dominant colors and accents, classify them, and show quick + extended interpretations.")

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

# extract palette
palette = get_palette_pillow(image, colors=24)

# choose dominants & accents
dominants, accents = choose_dominant_and_accents(palette)

# ----------------- SHOW DOMINANTS -----------------
st.header("🎨 Dominant colors")
summary_shorts = []
for i, (rgb, pct, score, h, s, v, bucket) in enumerate(dominants, start=1):
    hexc = rgb_to_hex(rgb)
    key = classify_by_hue(rgb)
    meaning = safe_get_meaning(key)
    short = meaning.get("short", "No short meaning.")
    long = meaning.get("long", "No extended meaning available.")
    chakra = meaning.get("chakra", "")

    st.markdown(f"### {i}. {bucket.capitalize()} — {key.capitalize()} — `{hexc}` ({pct*100:.1f}%)")
    st.markdown(f"<div class='color-box' style='background:{hexc}'></div>", unsafe_allow_html=True)
    if chakra:
        st.markdown(f"**Chakra:** {chakra}")
    st.markdown(f"**Quick:** {short}")
    with st.expander("🔮 More about this color"):
        st.write(long)

    summary_shorts.append(short)

# ----------------- SHOW ACCENTS -----------------
if accents:
    st.header("✨ Accent colors")
    for (rgb, pct, score, h, s, v, bucket) in accents:
        hexc = rgb_to_hex(rgb)
        key = classify_by_hue(rgb)
        meaning = safe_get_meaning(key)
        short = meaning.get("short", "")
        st.markdown(f"- {bucket.capitalize()} — {key.capitalize()} `{hexc}` ({pct*100:.1f}%): {short}")

# ----------------- SUMMARY -----------------
if summary_shorts:
    st.header("🌀 Combined summary")
    st.markdown("**Quick combined:** " + make_summary_text(summary_shorts))
