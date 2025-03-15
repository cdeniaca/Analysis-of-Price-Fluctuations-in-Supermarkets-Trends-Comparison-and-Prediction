import streamlit as st
import pandas as pd
import json
import glob
import os

# Configurar la página
st.set_page_config(page_title="Comparador de Precios", layout="wide")

# ---- TÍTULO ----
st.markdown("<h1 style='text-align: center;'> 🛒 Comparador de Precios de Supermercados </h1>", unsafe_allow_html=True)

import os
import streamlit as st
import pandas as pd
import json

# 📂 Ruta del archivo JSON
file_path = "/mnt/data/_2025-03-15_merged.json"  # Asegúrate de que la ruta es correcta

# 🔎 Verificar si el archivo existe
if not os.path.exists(file_path):
    st.error(f"❌ Archivo {file_path} no encontrado.")
    st.stop()

st.write(f"📂 Cargando archivo desde: {file_path}")

# 📌 Cargar JSON en partes para evitar consumir mucha memoria
data = []
with open(file_path, "r", encoding="utf-8") as file:
    for line in file:
        try:
            item = json.loads(line.strip(",\n"))  # Procesar línea por línea
            data.append(item)
        except json.JSONDecodeError:
            continue  # Ignorar errores

# 📦 Convertir a DataFrame
if data:
    df = pd.DataFrame(data)
    st.success(f"✅ Archivo JSON cargado exitosamente. {df.shape[0]} registros encontrados.")
else:
    st.error("❌ No se pudieron cargar datos del JSON.")
    st.stop()

# ---- FILTROS ----
st.markdown("### 🎯 Filtrar productos:")

st.write(f"📊 **Productos totales disponibles:** {df.shape[0]}")

# Variables de estado
if "categoria_seleccionada" not in st.session_state:
    st.session_state.categoria_seleccionada = "Todas"
if "titulo_seleccionado" not in st.session_state:
    st.session_state.titulo_seleccionado = "Todos"
if "palabra_clave" not in st.session_state:
    st.session_state.palabra_clave = ""

# Aplicar filtros en una copia para no modificar df
df_filtrado = df.copy()

col1, col2, col3 = st.columns(3)

with col1:
    categorias_unicas = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
    st.session_state.categoria_seleccionada = st.selectbox("📂 Selecciona una categoría:", categorias_unicas)

if st.session_state.categoria_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["categoria"] == st.session_state.categoria_seleccionada]

with col2:
    titulos_unicos = ["Todos"] + sorted(df["titulo"].dropna().unique().tolist())
    st.session_state.titulo_seleccionado = st.selectbox("🏷️ Selecciona un producto:", titulos_unicos)

if st.session_state.titulo_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["titulo"] == st.session_state.titulo_seleccionado]

with col3:
    st.session_state.palabra_clave = st.text_input("🔎 Escribe el nombre:", st.session_state.palabra_clave)

if st.session_state.palabra_clave:
    df_filtrado = df_filtrado[df_filtrado["titulo"].str.contains(st.session_state.palabra_clave, case=False, na=False)]

st.write(f"📊 **Productos después de filtros:** {df_filtrado.shape[0]}")

if st.button("🧹 Borrar Filtros"):
    st.session_state.categoria_seleccionada = "Todas"
    st.session_state.titulo_seleccionado = "Todos"
    st.session_state.palabra_clave = ""
    st.rerun()

# ---- SECCIÓN DEL CARRITO ----
if "carrito" not in st.session_state:
    st.session_state.carrito = []

def agregar_al_carrito(producto):
    st.session_state.carrito.append(producto)
    st.success(f"✅ {producto['titulo']} agregado al carrito.")

if not df_filtrado.empty:
    st.markdown("### 🏷️ Productos encontrados:")
    df_filtrado = df_filtrado.sort_values(by="precio")
    cols = st.columns(4)

    for i, (_, row) in enumerate(df_filtrado.iterrows()):
        with cols[i % 4]:
            st.image(row['imagen'], width=100)
            st.write(f"**{row['titulo']}**")
            st.write(f"🏪 {row['supermercado']} | 📂 {row['categoria']}")
            st.write(f"💰 {row['precio']:.2f}€")
            if st.button(f"🛒 Agregar", key=f"add_{i}"):
                agregar_al_carrito(row.to_dict())
else:
    st.warning("⚠️ No se encontraron productos con los filtros seleccionados.")

# ---- LISTA DE COMPRA ----
st.header("🛍️ Lista de Compra")

if not st.session_state.carrito:
    st.info("Tu carrito está vacío. Agrega productos para empezar.")
else:
    total_compra = sum(p["precio"] for p in st.session_state.carrito)
    st.write(f"💰 **Total de la compra:** {total_compra:.2f}€")
    st.download_button("📥 Descargar Lista", data=json.dumps(st.session_state.carrito, indent=4), file_name="lista_compra.json", mime="application/json")
    if st.button("🛒 Vaciar Carrito"):
        st.session_state.carrito = []
        st.rerun()
