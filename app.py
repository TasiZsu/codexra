import streamlit as st
import colorsys
from PIL import Image
import numpy as np
import json

# Betöltjük a színek jelentését (colors.json fájlból)
def load_color_meanings():
    try:
        with open("colors.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

color_meanings = load_color_meanings()

st.title("🌈 Codex-Ra – Color Frequency Analyzer")

uploaded_file = st.file_uploader("📸 Tölts fel egy képet elemzéshez", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Feltöltött kép", use_column_width=True)

    # Kép numpy tömbbé alakítása
    img_array = np.array(image)
    pixels = img_array.reshape(-1, 3)

    # Átlag szín
    avg_color = pixels.mean(axis=0).astype(int)
    hex_color = '#%02x%02x%02x' % tuple(avg_color)

    st.markdown(f"🎨 **Domináns átlag szín:** `{hex_color}`")
    st.color_picker("Szín előnézet", hex_color, disabled=True)

    # Megnézzük van-e jelentés hozzá
    if hex_color.lower() in color_meanings:
        short_text = color_meanings[hex_color.lower()]["short"]
        long_text = color_meanings[hex_color.lower()]["long"]

        st.markdown(f"**🌟 Rövid jelentés:** {short_text}")
        with st.expander("📖 Részletesebb értelmezés"):
            st.write(long_text)
    else:
        st.info("Ehhez a színhez még nincs jelentés az adatbázisban.")
