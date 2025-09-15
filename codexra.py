import streamlit as st
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import json

# --- Load color meaning database ---
with open("colors.json", "r", encoding="utf-8") as f:
    color_data = json.load(f)

# Function: find closest color in database
def closest_color_name(rgb):
    min_dist = float("inf")
    closest = None
    for c in color_data:
        cr, cg, cb = color_data[c]["rgb"]
        dist = np.linalg.norm(np.array(rgb) - np.array([cr, cg, cb]))
        if dist < min_dist:
            min_dist = dist
            closest = c
    return closest

# Function: get dominant colors
def get_dominant_colors(image, n_colors=3):
    img = image.resize((150, 150))  # resize for speed
    img_data = np.array(img).reshape(-1, 3)

    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    labels = kmeans.fit_predict(img_data)

    counts = np.bincount(labels)
    centers = kmeans.cluster_centers_.astype(int)

    # sort by frequency
    sorted_idx = np.argsort(-counts)
    percentages = counts[sorted_idx] / sum(counts) * 100
    colors = centers[sorted_idx]

    return colors, percentages

# --- Streamlit UI ---
st.set_page_config(page_title="CodexRa - Decode the Light Within", layout="wide", page_icon="🌈")

st.title("🌈 CodexRa: Decode the Light Within")
st.write("Upload an image to analyze its **3 dominant colors**, their **frequency, chakra meaning, and effects**.")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_column_width=True)

    colors, percentages = get_dominant_colors(image)

    st.header("✨ Color Analysis")
    summaries = []

    for i, (col, pct) in enumerate(zip(colors, percentages)):
        hex_color = "#{:02x}{:02x}{:02x}".format(col[0], col[1], col[2])
        name = closest_color_name(col)
        chakra = color_data[name]["chakra"]
        short = color_data[name]["short"]
        long = color_data[name]["long"]

        with st.container():
            st.markdown(f"### 🎨 Color {i+1}: {name} ({pct:.1f}%)")
            st.markdown(f"**Hex:** {hex_color} | **RGB:** {col}")
            st.color_picker("Preview", hex_color, key=f"picker_{i}", label_visibility="collapsed")

            st.markdown(f"**Chakra:** {chakra}")
            st.markdown(f"**Meaning:** {short}")

            with st.expander("🔮 More about this color"):
                st.write(long)

            summaries.append(name)

    # --- Summary Section ---
    st.header("🌌 Combined Meaning")
    joined = ", ".join(summaries)
    st.write(f"Your image radiates mainly **{joined}** energies. Together, they create a unique frequency mix that influences both **mind and body**.")

else:
    st.info("⬆️ Please upload an image to start analysis.")
