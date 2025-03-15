import streamlit as st
import pandas as pd
import json
import glob
import os

st.title('🛒 Comparador de Precios de Supermercados')

# 1. Buscar todos los archivos JSON
json_files = glob.glob("*.json")
if not json_files:
    st.error("No se encontraron archivos JSON con extensión '.json'.")
    st.stop()

data_list = []
for file in json_files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            brand = os.path.basename(file).split("_")[0]
            for item in data:
                item["empresa"] = brand
            data_list.extend(data)
    except Exception as e:
        st.error(f"Error leyendo {file}: {e}")

df = pd.DataFrame(data_list)

# DEBUG: Ver cuántos productos hay de cada empresa
st.write("Archivos JSON cargados:", json_files)
st.write("Total de productos leídos:", len(df))
if "empresa" in df.columns:
    st.write("Cantidad de productos por empresa:")
    st.write(df["empresa"].value_counts())

# Verificar columnas
expected_cols = {"titulo","precios","categoria","imagen","link","empresa"}
missing_cols = expected_cols - set(df.columns)
if missing_cols:
    st.warning(f"Faltan columnas: {missing_cols}")

# Extraer precio principal
def extraer_precio(precio):
    if isinstance(precio, list) and len(precio) > 0:
        try:
            return float(precio[0])
        except:
            return None
    return None

df["precio"] = df["precios"].apply(extraer_precio)
df.dropna(subset=["precio"], inplace=True)

# Ordenar DataFrame
df = df.sort_values("titulo")

# Carrito
if "cart" not in st.session_state:
    st.session_state.cart = []

st.sidebar.title("Carrito de Compra")
if st.sidebar.button("Ver carrito"):
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.sidebar.write(cart_df)
        total = cart_df["precio"].sum()
        st.sidebar.write(f"**Total: ${total:.2f}**")
    else:
        st.sidebar.write("El carrito está vacío.")

# Selección de producto
titulos_unicos = df["titulo"].unique().tolist()
producto_seleccionado = st.selectbox("Selecciona un producto", titulos_unicos)

# FILTRADO PARCIAL (si quieres exacto, usa ==)
df_filtrado = df[df["titulo"].str.contains(producto_seleccionado, case=False, na=False)]

if df_filtrado.empty:
    st.info("No se encontraron productos con ese criterio.")
else:
    st.write("### Productos encontrados")
    df_filtrado = df_filtrado.sort_values("precio")

    for index, row in df_filtrado.iterrows():
        col1, col2 = st.columns([1,3])
        with col1:
            st.image(row["imagen"], width=100)
        with col2:
            st.markdown(f"**{row['titulo']}**")
            st.markdown(f"Empresa: {row['empresa']}")
            st.markdown(f"Categoría: {row['categoria']}")
            st.markdown(f"Precio: ${row['precio']:.2f}")
            if "link" in row and pd.notna(row["link"]):
                st.markdown(f"[Ver producto]({row['link']})")
            
            if st.button("Añadir al carrito", key=f"cart_{index}"):
                st.session_state.cart.append({
                    "titulo": row["titulo"],
                    "empresa": row["empresa"],
                    "precio": row["precio"],
                    "categoria": row["categoria"],
                    "link": row.get("link", ""),
                    "imagen": row["imagen"]
                })
                st.success("Producto añadido al carrito")
