import streamlit as st
import pandas as pd
import json
import glob
import os

# Título de la aplicación
st.title('🛒 Comparador de Precios de Supermercados')

# 1. Buscar todos los archivos JSON con extensión ".json"
json_files = glob.glob("*.json")
if not json_files:
    st.error("No se encontraron archivos JSON con extensión '.json' en la carpeta actual.")
    st.stop()

# 2. Leer y combinar los archivos JSON, extrayendo el nombre de la empresa a partir del nombre del archivo
data_list = []
for file in json_files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Extraer la empresa: se espera que el nombre del archivo tenga un guion bajo, por ejemplo "dia_2025-03-15.json"
            brand = os.path.basename(file).split("_")[0]
            for item in data:
                item["empresa"] = brand
            data_list.extend(data)
    except Exception as e:
        st.error(f"Error leyendo {file}: {e}")

# 3. Convertir la lista de datos en DataFrame
df = pd.DataFrame(data_list)

# Verificar que contenga las columnas esperadas (ajusta según tu formato)
expected_columns = {"titulo", "precios", "categoria", "imagen", "link", "empresa"}
missing_cols = expected_columns - set(df.columns)
if missing_cols:
    st.warning(f"Faltan columnas en el DataFrame: {missing_cols}. Ajusta tus archivos JSON o el código.")

# 4. Función para extraer el precio principal (se espera que 'precios' sea una lista)
def extraer_precio(precio):
    if isinstance(precio, list) and len(precio) > 0:
        try:
            return float(precio[0])
        except (ValueError, TypeError):
            return None
    return None

df["precio"] = df["precios"].apply(extraer_precio)
df.dropna(subset=["precio"], inplace=True)
df = df.sort_values("titulo")

# DEBUG: Mostrar cantidad de productos por empresa
st.write("**Cantidad de productos por empresa:**")
st.write(df["empresa"].value_counts())

# 5. Inicializar el carrito de compra en session_state
if "cart" not in st.session_state:
    st.session_state.cart = []

# 6. Barra lateral para el carrito de compra
st.sidebar.title("Carrito de Compra")
if st.sidebar.button("Ver carrito"):
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.sidebar.write(cart_df)
        total = cart_df["precio"].sum()
        st.sidebar.write(f"**Total: ${total:.2f}**")
    else:
        st.sidebar.write("El carrito está vacío.")

# 7. Filtros: recuadros para seleccionar Categoría y Marca
st.subheader("Filtrar productos")
col1, col2 = st.columns(2)
with col1:
    categorias_disponibles = sorted(df["categoria"].dropna().unique().tolist())
    categorias_seleccionadas = st.multiselect("Filtrar por Categoría", options=categorias_disponibles, default=categorias_disponibles)
with col2:
    marcas_disponibles = sorted(df["empresa"].dropna().unique().tolist())
    marcas_seleccionadas = st.multiselect("Filtrar por Marca", options=marcas_disponibles, default=marcas_disponibles)

# Aplicar filtros
df_filtrado = df[df["categoria"].isin(categorias_seleccionadas) & df["empresa"].isin(marcas_seleccionadas)]
if df_filtrado.empty:
    st.error("No hay productos que cumplan los filtros seleccionados.")
    st.stop()

# 8. Selección de producto mediante selectbox (los títulos se extraen del df filtrado)
titulos_unicos = sorted(df_filtrado["titulo"].unique().tolist())
producto_seleccionado = st.selectbox("Selecciona un producto", titulos_unicos)

# Filtrado por producto (puedes usar contains o coincidencia exacta)
# Aquí usamos coincidencia exacta para evitar ambigüedades:
df_producto = df_filtrado[df_filtrado["titulo"] == producto_seleccionado]
if df_producto.empty:
    st.info("No se encontraron productos con ese criterio.")
else:
    st.write("### Productos encontrados")
    df_producto = df_producto.sort_values("precio")

    for index, row in df_producto.iterrows():
        col1, col2 = st.columns([1, 3])
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


