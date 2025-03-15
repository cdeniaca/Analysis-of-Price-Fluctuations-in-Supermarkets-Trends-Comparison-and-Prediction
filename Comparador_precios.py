import streamlit as st
import pandas as pd
import json
import glob
import os

# Configurar la página
st.set_page_config(page_title="Comparador de Precios", layout="wide")

# ---- SECCIÓN DEL CARRITO ----
st.header("🛍️ Tu Carrito de Compras")

if "carrito" not in st.session_state:
    st.session_state.carrito = []

if not st.session_state.carrito:
    st.info("Tu carrito está vacío. Agrega productos para empezar.")
else:
    carrito_df = pd.DataFrame(st.session_state.carrito)
    total_compra = carrito_df["precio"].sum()

    st.write(f"💰 **Total de la compra:** {total_compra:.2f}€")

    # 📜 Estructura del JSON organizado por supermercado y categoría
    carrito_organizado = {}
    for supermercado in carrito_df["supermercado"].unique():
        productos_super = carrito_df[carrito_df["supermercado"] == supermercado]
        carrito_organizado[supermercado] = {}

        for categoria in productos_super["categoria"].unique():
            productos_cat = productos_super[productos_super["categoria"] == categoria]
            carrito_organizado[supermercado][categoria] = [
                {
                    "producto": row["titulo"],
                    "precio": row["precio"]
                }
                for _, row in productos_cat.iterrows()
            ]

    # Mostrar JSON en la interfaz
    st.markdown("### 📋 Lista de Compra en JSON:")
    carrito_json = json.dumps(carrito_organizado, indent=4, ensure_ascii=False)
    st.text_area("📜 JSON generado:", carrito_json, height=300)

    # Botón para descargar JSON
    st.download_button(
        label="📥 Descargar Lista de Compra (JSON)",
        data=carrito_json,
        file_name="lista_compra.json",
        mime="application/json"
    )

    # Botón para vaciar el carrito
    if st.button("🗑️ Vaciar Carrito"):
        st.session_state.carrito = []
        st.rerun()
