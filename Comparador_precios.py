import streamlit as st
import pandas as pd
import json
import glob
import os

# Configurar la página
st.set_page_config(page_title="Comparador de Precios", layout="wide")

# ---- SECCIÓN DEL CARRITO ----
st.header("🛍️ Lista de Compra para Imprimir")

if "carrito" not in st.session_state:
    st.session_state.carrito = []

if not st.session_state.carrito:
    st.info("Tu carrito está vacío. Agrega productos para empezar.")
else:
    carrito_df = pd.DataFrame(st.session_state.carrito)
    total_compra = carrito_df["precio"].sum()

    st.write(f"💰 **Total de la compra:** {total_compra:.2f}€")

    # 📜 Generación de lista de compra en formato TXT
    lista_compra_txt = "🛒 **Lista de Compra**\n\n"

    for supermercado in carrito_df["supermercado"].unique():
        lista_compra_txt += f"🏪 {supermercado}\n"
        lista_compra_txt += "-" * len(supermercado) + "\n"

        productos_super = carrito_df[carrito_df["supermercado"] == supermercado]
        for categoria in productos_super["categoria"].unique():
            lista_compra_txt += f"  📂 {categoria}\n"
            lista_compra_txt += "  " + "-" * len(categoria) + "\n"

            productos_cat = productos_super[productos_super["categoria"] == categoria]
            for _, row in productos_cat.iterrows():
                lista_compra_txt += f"    [ ] {row['titulo']} - {row['precio']:.2f}€\n"

        lista_compra_txt += "\n"

    # Mostrar la lista en la interfaz
    st.text_area("📜 Copia esta lista:", lista_compra_txt, height=300)

    # 📥 Descargar TXT
    st.download_button(
        label="📥 Descargar Lista de Compra (TXT)",
        data=lista_compra_txt,
        file_name="lista_compra.txt",
        mime="text/plain"
    )

    # 📥 Descargar JSON
    lista_compra_json = json.dumps(st.session_state.carrito, indent=4, ensure_ascii=False)
    st.download_button(
        label="📥 Descargar Lista de Compra (JSON)",
        data=lista_compra_json,
        file_name="lista_compra.json",
        mime="application/json"
    )

    # Botón para vaciar todo el carrito
    if st.button("🛒 Vaciar Todo el Carrito"):
        st.session_state.carrito = []
        st.rerun()
