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

    # ---- WISHLIST CON CHECKBOX ----
    st.markdown("### 📋 Mi Lista de la Compra:")
    productos_comprados = st.session_state.get("productos_comprados", {})

    for supermercado, categorias in carrito_organizado.items():
        st.subheader(f"🏪 {supermercado}")

        for categoria, productos in categorias.items():
            st.markdown(f"**📂 {categoria}**")
            for producto in productos:
                producto_id = f"{supermercado}_{categoria}_{producto['producto']}"
                if producto_id not in productos_comprados:
                    productos_comprados[producto_id] = False
                
                # Checkbox para cada producto
                productos_comprados[producto_id] = st.checkbox(
                    f"✅ {producto['producto']} - {producto['precio']:.2f}€",
                    value=productos_comprados[producto_id],
                    key=producto_id
                )

    # Guardar el estado de los checkboxes
    st.session_state.productos_comprados = productos_comprados

    # Botón para eliminar productos marcados como comprados
    if st.button("🗑️ Eliminar productos comprados"):
        st.session_state.carrito = [
            item for item in st.session_state.carrito
            if not productos_comprados[f"{item['supermercado']}_{item['categoria']}_{item['titulo']}"]
        ]
        st.session_state.productos_comprados = {}
        st.rerun()

    # 📥 Botón para descargar la lista en JSON
    carrito_json = json.dumps(carrito_organizado, indent=4, ensure_ascii=False)
    st.download_button(
        label="📥 Descargar Lista de Compra (JSON)",
        data=carrito_json,
        file_name="lista_compra.json",
        mime="application/json"
    )

    # Botón para vaciar todo el carrito
    if st.button("🛒 Vaciar Todo el Carrito"):
        st.session_state.carrito = []
        st.session_state.productos_comprados = {}
        st.rerun()
