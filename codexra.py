import streamlit as st
from PIL import Image
import numpy as np
import json
import colorsys
import io

# ----- load color meanings -----
def load_color_data(path="colors.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning("Could not load colors.json — defaulting to minimal set.")
        return {}

color_data = load_color_data()

# ----- helpers -----
def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def rgb_to_hsv_deg(r,g,b):
    # r,g,b 0-255 -> returns h (0..360), s (0..1), v (0..1)
    h,s,v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    return h*360, s, v

def classify_by_hue(r,g,b):
    h, s, v = rgb_to_hsv_deg(r,g,b)
    # black / white / silver
    if v <= 0.06:
        return "black"
    if s <= 0.12 and v >= 0.92:
        return "white"
    if s <= 0.18:
        return "silver"

    # main hue ranges (degrees)
    if h < 15 or h >= 345:
        return "red"
    if 15 <= h < 45:
        return "orange"
    if 45 <= h < 65:
        return "yellow"
    if 65 <= h < 150:
        return "green"
    if 150 <= h < 180:
        return "turquoise"
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

def get_top_colors_pillow(image: Image.Image, n_colors=3):
    """
    Use Pillow adaptive palette to get top colors.
    Returns list of tuples: ( (r,g,b), percentage )
    """
    # ensure RGB
    img = image.convert("RGB")
    # resize to speed up
    w,h = img.size
    max_dim = 300
    if max(w,h) > max_dim:
        scale = max_dim / max(w,h)
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)

    pal = img.convert("P", palette=Image.ADAPTIVE, colors=n_colors)
    palette = pal.getpalette()  # list [r,g,b, r,g,b,...]
    color_counts = pal.getcolors()  # list of (count, palette_index)

    if not color_counts:
        # fallback sampling
        arr = np.array(img).reshape(-1,3)
        vals, counts = np.unique(arr, axis=0, return_counts=True)
        top_idx = np.argsort(-counts)[:n_colors]
        total = counts.sum()
        return [ (tuple(vals[i]), counts[i]/total) for i in top_idx ]

    total = sum(c[0] for c in color_counts)
    # sort by count desc
    color_counts.sort(reverse=True, key=lambda x: x[0])
    results = []
    for count, idx in color_counts[:n_colors]:
        r = palette[idx*3]
        g = palette[idx*3 + 1]
        b = palette[idx*3 + 2]
        pct = count / total
        results.append(((r,g,b), pct))
    return results

# ----- Streamlit UI -----
st.set_page_config(page_title="CodexRa - Decode the Light Within", layout="centered", page_icon="🌈")
st.title("🌈 CodexRa — Decode the Light Within")
st.write("Upload an image and CodexRa will analyze the 3 dominant colors, map them to chakra & frequency meanings, and give a short + extended interpretation.")

uploaded_file = st.file_uploader("Upload an image (jpg/png)", type=["jpg","jpeg","png"])

if uploaded_file is None:
    st.info("Upload an image to start. You can also drag&drop.")
    st.markdown("**Tip:** use photos or paintings. Try the sample images after upload if you like.")
else:
    # open image
    try:
        image = Image.open(io.BytesIO(uploaded_file.read())).convert("RGB")
    except Exception:
        st.error("Failed to open image. Try a different file.")
        st.stop()

    st.image(image, caption="Uploaded image", use_column_width=True)

    # get top colors
    top = get_top_colors_pillow(image, n_colors=3)
    if not top:
        st.error("Could not analyze image colors.")
        st.stop()

    st.header("🎨 Dominant Colors")
    summaries = []
    # display each as its own block
    for i, (rgb, pct) in enumerate(top, start=1):
        hexc = rgb_to_hex(rgb)
        # classify by hue to one of the color keys
        key = classify_by_hue(*rgb)
        meaning = color_data.get(key, {})
        short = meaning.get("short", "No short meaning available.")
        long = meaning.get("long", "No extended meaning available.")
        chakra = meaning.get("chakra", "")

        # Block
        st.markdown(f"### {i}. {key.capitalize()} — `{hexc}` — {pct*100:.1f}%")
        cols = st.columns([1,3])
        with cols[0]:
            st.write("")
            sw = st.empty()
            sw.markdown(f"<div style='width:100%;height:80px;border-radius:8px;background:{hexc};border:1px solid rgba(255,255,255,0.08)'></div>", unsafe_allow_html=True)
        with cols[1]:
            if chakra: st.markdown(f"**Chakra:** {chakra}")
            st.markdown(f"**Quick:** {short}")
            with st.expander("🔮 More about this color"):
                st.write(long)

        summaries.append(short)

    # Combined summary
    st.header("🌀 Combined Summary")
    if summaries:
        combined = " • ".join(summaries)
        st.markdown(f"**Quick combined:** {combined}")
        st.write("")
        # small friendly sentence
        keys = [classify_by_hue(*rgb) for rgb,_ in top]
        human_readable = ", ".join(k.capitalize() for k in keys)
        st.markdown(f"The image mainly resonates with **{human_readable}** energies. Each color brings its influence — together they create a unique emotional and energetic fingerprint.")
    else:
        st.info("No summary available.")
