Python 3.13.2 (tags/v3.13.2:4f8bb39, Feb  4 2025, 15:23:48) [MSC v.1942 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
>>> import streamlit as st
... from PIL import Image
... import numpy as np
... from collections import Counter
... import colorsys
... 
... st.set_page_config(page_title="Codex-Ra", page_icon="🌈", layout="centered")
... 
... st.title("🌈 Codex-Ra: Decode the Light Within")
... st.write("Upload an image and discover its **dominant color frequencies**.")
... 
... # Upload image
... uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
... 
... def rgb_to_hex(rgb):
...     return '#%02x%02x%02x' % rgb
... 
... if uploaded_file is not None:
...     # Open image
...     image = Image.open(uploaded_file)
...     st.image(image, caption="Uploaded Image", use_container_width=True)
... 
...     # Resize for speed
...     small_img = image.resize((150, 150))
...     result = small_img.convert('RGB')
...     pixels = np.array(result).reshape(-1, 3)
... 
...     # Count colors
...     counts = Counter(map(tuple, pixels))
...     most_common = counts.most_common(3)
... 
...     st.subheader("🎨 Dominant Colors")
...     for i, (col, count) in enumerate(most_common):
...         hex_col = rgb_to_hex(col)
...         percent = (count / sum(counts.values())) * 100
...         st.markdown(
...             f"**{i+1}. {hex_col}** - {percent:.2f}%"
        )
        st.color_picker("Color", hex_col, key=f"color_{i}")

    st.success("✨ Decoding complete!")
