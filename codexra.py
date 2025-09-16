import streamlit as st
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
from PIL import Image
import webcolors
import json

st.set_page_config(page_title="Codex-Ra", layout="wide")

# --- Színadatbázis (bővíthető JSON formában is) ---
color_db = {
    "red": {
        "short": "Vitality, strength, and passion.",
        "long": "Red is linked to the Root Chakra (Muladhara). It represents life force, courage, grounding, and primal energy. Psychologically, it stimulates attention and determination."
    },
    "orange": {
        "short": "Creativity, sexuality, and joy.",
        "long": "Orange resonates with the Sacral Chakra (Svadhisthana). It symbolizes warmth, emotional flow, and creative energy. It is associated with pleasure, sociability, and optimism."
    },
    "yellow": {
        "short": "Energy, intellect, and clarity.",
        "long": "Yellow is connected to the Solar Plexus Chakra (Manipura). It represents willpower, focus, and confidence. Scientifically, it activates mental clarity and optimism."
    },
    "green": {
        "short": "Harmony, balance, and healing.",
        "long": "Green corresponds to the Heart Chakra (Anahata). It symbolizes compassion, growth, and renewal. It relaxes the nervous system and creates emotional stability."
    },
    "blue": {
        "short": "Calmness, communication, and truth.",
        "long": "Blue resonates with the Throat Chakra (Vishuddha). It encourages self-expression, serenity, and clear thought. Physiologically, blue tones lower stress and aid concentration."
    },
    "indigo": {
        "short": "Intuition, depth, and perception.",
        "long": "Indigo aligns with the Third Eye Chakra (Ajna). It reflects wisdom, imagination, and spiritual insight. It connects to higher awareness and inner vision."
    },
    "violet": {
        "short": "Spirituality, transformation, and inspiration.",
        "long": "Violet is linked to the Crown Chakra (Sahasrara). It symbolizes transcendence, unity, and divine wisdom. It has historically represented mystical knowledge and higher states."
    },
    # Köztes színek
    "brown": {
        "short": "Stability, grounding, and earth connection.",
        "long": "Brown is associated with security, reliability, and natural cycles. Psychologically it connects to simplicity, humility, and comfort."
    },
    "turquoise": {
        "short": "Healing, balance, and communication.",
        "long": "Turquoise blends green and blue energies. It enhances clarity, emotional healing, and spiritual protection. In many cultures, it symbolizes truth and sacred connection."
    },
    "magenta": {
        "short": "Transformation, harmony, and spiritual balance.",
        "long": "Magenta combines red’s vitality with violet’s spirituality. It symbolizes alchemy, renewal, and higher emotional awareness."
    },
    "white": {
        "short": "Purity, unity, and openness.",
        "long": "White holds all colors of light. It represents spiritual wholeness, clarity, and transcendence. It resets the mind and clears energetic fields."
    },
    "black": {
        "short": "Mystery, protection, and depth.",
        "long": "Black absorbs all light. It symbolizes the unknown, the void, and transformation. It provides grounding and authority."
    },
    "grey": {
        "short": "Neutrality, balance, and calm.",
        "long": "Grey reflects detachment and neutrality. It creates a stabilizing field, but too much may feel dull or lifeless."
    }
}

# --- Szín hozzárendelés ---
def match_color_name(rgb):
    r, g, b = rgb
    if max(rgb) < 40: return "black"
    if min(rgb) > 220: return "white"
    if abs(r-g) < 15 and abs(g-b) < 15: return "grey"

    if r > 150 and g < 100 and b < 100: return "red"
    if r > 200 and 100 < g < 180 and b < 100: return "orange"
    if r > 200 and g > 200 and b < 100: return "yellow"
    if g > 120 and b < 120 and r < 120: return "green"
    if b > 150 and g > 100 and r < 100: return "turquoise"
    if b > 180 and r < 100 and g < 150: return "blue"
    if r > 100 and b > 150 and g < 100: return "violet"
    if r > 150 and b > 150 and g < 150: return "magenta"
    if r > 100 and g < 80 and b < 50: return "brown"
    if r > 75 and g > 75 and b > 75: return "grey"

    return "indigo"

# --- Színdominancia elemzés ---
def extract_colors(image, num_colors=5):
    img = image.resize((150, 150))
    img_data = np.array(img).reshape(-1, 3)

    # KMeans a domináns színekre
    kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
    labels = kmeans.fit_predict(img_data)
    counts = Counter(labels)

    total = sum(counts.values())
    colors = []
    for idx, count in counts.most_common(num_colors):
        rgb = kmeans.cluster_centers_[idx].astype(int)
        hex_val = webcolors.rgb_to_hex(tuple(rgb))
        name = match_color_name(rgb)
        percent = round((count / total) * 100, 2)
        colors.append((hex_val, rgb, name, percent))
    return colors

# --- Streamlit UI ---
st.title("🌈 Codex-Ra: Decode the Light Within")
st.write("Upload an image to analyze its **dominant & accent colors** with symbolic and scientific insights.")

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_column_width=True)

    colors = extract_colors(image, num_colors=5)

    st.subheader("🎨 Dominant & Accent Colors")
    for idx, (hex_val, rgb, name, percent) in enumerate(colors):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"<div style='background-color:{hex_val}; width:50px; height:50px; border-radius:8px'></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{name.capitalize()}** ({percent}%) – {hex_val}")

            if name in color_db:
                st.write(color_db[name]["short"])
                with st.expander("More about this color..."):
                    st.write(color_db[name]["long"])
