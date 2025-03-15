import streamlit as st
import pandas as pd
import json
import glob
import os
import re

# Configurar la página
st.set_page_config(page_title="Comparador de Precios", layout="wide")

# ---- TÍTULO ----
st.markdown("<h1 style='text-align: center;'> 🛒 Comparador de Precios de Supermercados </h1>", unsafe_allow_html=True)

# ---- CARGA DE DATOS ----
archivos_json = glob.glob("*_merged.json")  # Busca en el directorio actual

# Verificar si se encontró el archivo JSON
st.write("🔍 Archivos JSON encontrados:", archivos_json)

if not archivos_json:
    st.error("❌ No se encontraron archivos JSON.")
    st.stop()

dataframes = []
for archivo in archivos_json:
    file_path = os.path.abspath(archivo)  # Ruta absoluta para depuración
    st.write(f"📂 Intentando cargar: {file_path}")

    with open(archivo, "r", encoding="utf-8") as file:
        try:
            json_content = file.read()
            json_cleaned = re.sub(r",\s*([\]}])", r"\1", json_content)
            data = json.loads(json_cleaned)
            df_temp = pd.DataFrame(data)

            # 🏪 Asegurar que la columna "supermercado" no esté vacía
            df_temp["supermercado"] = df_temp.get("supermercado", "Desconocido").fillna("Desconocido")

            # 💰 Extraer correctamente el precio
            def extraer_precio(precio):
                if isinstance(precio, str):
                    precio = re.sub(r"[^\d,\.]", "", precio)  # Eliminar caracteres no numéricos
                    precio = precio.replace(",", ".")  # Convertir comas en puntos
                    try:
                        return float(precio)  # Convertir a número
                    except ValueError:
                        return None
                return precio

            df_temp["precio"] = df_temp["precio"].apply(extraer_precio)

            # 🖼️ Manejo de imágenes
            df_temp["imagen"] = df_temp["imagen"].apply(
                lambda x: x if isinstance(x, str) and "http" in x else "https://via.placeholder.com/100"
            )

            dataframes.append(df_temp)

        except json.JSONDecodeError:
            st.warning(f"⚠️ Error al leer el archivo {archivo}. Verifica su formato.")

# 📦 Unir los datos
df_original = pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()

if df_original.empty:
    st.error("❌ No se pudo cargar ningún archivo JSON válido.")
    st.stop()

# ---- FILTROS ----
st.markdown("### 🎯 Filtrar productos:")

st.write(f"📊 **Productos totales disponibles:** {df_original.shape[0]}")

# Variables de estado
if "categoria_seleccionada" not in st.session_state:
    st.session_state.categoria_seleccionada = "Todas"
if "titulo_seleccionado" not in st.session_state:
    st.session_state.titulo_seleccionado = "Todos"
if "palabra_clave" not in st.session_state:
    st.session_state.palabra_clave = ""

# Aplicar filtros en una copia para no modificar df_original
df = df_original.copy()

col1, col2, col3 = st.columns(3)

with col1:
    categorias_unicas = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
    st.session_state.categoria_seleccionada = st.selectbox("📂 Selecciona una categoría:", categorias_unicas)

if st.session_state.categoria_seleccionada != "Todas":
    df = df[df["categoria"] == st.session_state.categoria_seleccionada]

with col2:
    titulos_unicos = ["Todos"] + sorted(df["titulo"].dropna().unique().tolist())
    st.session_state.titulo_seleccionado = st.selectbox("🏷️ Selecciona un producto:", titulos_unicos)

if st.session_state.titulo_seleccionado != "Todos":
    df = df[df["titulo"] == st.session_state.titulo_seleccionado]

with col3:
    st.session_state.palabra_clave = st.text_input("🔎 Escribe el nombre:", st.session_state.palabra_clave)

if st.session_state.palabra_clave:
    df = df[df["titulo"].str.contains(st.session_state.palabra_clave, case=False, na=False)]

st.write(f"📊 **Productos después de filtros:** {df.shape[0]}")

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

if not df.empty:
    st.markdown("### 🏷️ Productos encontrados:")
    df = df.sort_values(by="precio")
    cols = st.columns(4)

    for i, (_, row) in enumerate(df.iterrows()):
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
