import streamlit as st
import pandas as pd
import json
import os

# 📂 Ruta del archivo JSON
file_path = "/mnt/data/_2025-03-15_merged.json"

# 🔍 Verificar si el archivo JSON existe antes de leerlo
if not os.path.exists(file_path):
    st.error(f"❌ Archivo JSON no encontrado en la ruta: {file_path}")
    st.stop()

# ---- CARGA DE DATOS ----
st.write("📂 Cargando datos...")

# 📦 Leer el JSON
data = []
try:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    # Convertir a DataFrame
    df = pd.DataFrame(data)
    st.success(f"✅ {df.shape[0]} productos cargados correctamente.")
    
    # 📊 Mostrar las primeras filas para verificar
    st.write(df.head())

except json.JSONDecodeError:
    st.error("❌ Error al cargar el archivo JSON. Verifica el formato del archivo.")
    st.stop()

# ---- VERIFICACIONES ----
# 🔍 Verificar nombres de columnas
expected_columns = {"titulo", "categoria", "precio", "supermercado"}
missing_columns = expected_columns - set(df.columns)

if missing_columns:
    st.error(f"❌ Faltan estas columnas en el JSON: {missing_columns}")
    st.stop()

# 🏪 Asegurar que la columna "supermercado" no esté vacía
df["supermercado"] = df["supermercado"].fillna("Desconocido")

# 💰 Convertir precios a números
df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
df = df.dropna(subset=["precio"])

# 🖼️ Imágenes
df["imagen"] = df["imagen"].fillna("https://via.placeholder.com/100")

# ---- FILTROS ----
st.markdown("### 🎯 Filtrar productos:")

col1, col2, col3 = st.columns(3)

# Categoría
categorias_unicas = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
categoria_seleccionada = col1.selectbox("📂 Selecciona una categoría:", categorias_unicas)

# Producto
titulos_unicos = ["Todos"] + sorted(df["titulo"].dropna().unique().tolist())
titulo_seleccionado = col2.selectbox("🏷️ Selecciona un producto:", titulos_unicos)

# Buscar por nombre
palabra_clave = col3.text_input("🔎 Escribe el nombre:")

# Aplicar filtros
df_filtrado = df.copy()
if categoria_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["categoria"] == categoria_seleccionada]
if titulo_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["titulo"] == titulo_seleccionado]
if palabra_clave:
    df_filtrado = df_filtrado[df_filtrado["titulo"].str.contains(palabra_clave, case=False, na=False)]

st.write(f"📊 **Productos después de filtros:** {df_filtrado.shape[0]}")

# ---- SECCIÓN DEL CARRITO ----
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# Función para agregar al carrito
def agregar_al_carrito(producto):
    st.session_state.carrito.append(producto)
    st.success(f"✅ {producto['titulo']} agregado al carrito.")

# Mostrar productos
if not df_filtrado.empty:
    st.markdown("### 🏷️ Productos encontrados:")
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
    carrito_df = pd.DataFrame(st.session_state.carrito)
    total_compra = carrito_df["precio"].sum()
    st.write(f"💰 **Total de la compra:** {total_compra:.2f}€")

    lista_compra_txt = "🛒 **Lista de Compra**\n\n"
    for supermercado in carrito_df["supermercado"].unique():
        lista_compra_txt += f"🏪 {supermercado}\n"
        lista_compra_txt += "-" * len(supermercado) + "\n"
        productos_super = carrito_df[carrito_df["supermercado"] == supermercado]
        for categoria in productos_super["categoria"].unique():
            lista_compra_txt += f"  📂 {categoria}\n"
            lista_compra_txt += "  " + "-" * len(categoria) + "\n"
            for _, row in productos_super[productos_super["categoria"] == categoria].iterrows():
                lista_compra_txt += f"    [ ] {row['titulo']} - {row['precio']:.2f}€\n"

    st.text_area("📜 Copia esta lista:", lista_compra_txt, height=300)
    st.download_button("📥 Descargar TXT", data=lista_compra_txt, file_name="lista_compra.txt", mime="text/plain")

    if st.button("🛒 Vaciar Todo el Carrito"):
        st.session_state.carrito = []
        st.rerun()
