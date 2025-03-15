import streamlit as st
import pandas as pd
import json
import glob
import os

# Configurar el título de la aplicación
st.title('🛒 Comparador de Precios de Supermercados')

# Buscar todos los archivos JSON que terminen con "merged.json"
json_files = glob.glob("*merged.json")
if not json_files:
    st.error("No se encontraron archivos JSON que terminen en 'merged.json' en la carpeta actual.")
    st.stop()

# Leer y combinar los archivos JSON
data_list = []
for file in json_files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            data_list.extend(data)
    except Exception as e:
        st.error(f"Error leyendo {file}: {e}")

df = pd.DataFrame(data_list)

# Verificar columnas esperadas
expected_columns = {"titulo", "precios", "categoria", "imagen", "link"}
if not expected_columns.issubset(df.columns):
    st.error(f"El archivo debe contener las columnas: {expected_columns}")
    st.stop()

# Función para extraer el precio (se asume que 'precios' es una lista)
def extraer_precio(precio):
    if isinstance(precio, list) and len(precio) > 0:
        try:
            return float(precio[0])
        except ValueError:
            return None
    return None

# Convertir precios a formato numérico y eliminar productos sin precio
df["precio"] = df["precios"].apply(extraer_precio)
df = df.dropna(subset=["precio"])

# Ordenar por título (para el selectbox) y por precio en el DataFrame filtrado
df = df.sort_values("titulo")

# Inicializar el carrito de compra en session_state
if "cart" not in st.session_state:
    st.session_state.cart = []

# Sidebar: Carrito de Compra
st.sidebar.title("Carrito de Compra")
if st.sidebar.button("Ver carrito"):
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.sidebar.write(cart_df)
        total = cart_df["precio"].sum()
        st.sidebar.write(f"**Total: ${total:.2f}**")
    else:
        st.sidebar.write("El carrito está vacío.")

# Desplegable para seleccionar un producto (filtrado por título)
titulos_unicos = sorted(df["titulo"].unique())
producto_seleccionado = st.selectbox("Selecciona un producto", titulos_unicos)

# Filtrar los productos que contengan el título seleccionado (en caso de tener variantes de cada supermercado)
df_filtrado = df[df["titulo"].str.contains(producto_seleccionado, case=False, na=False)]
if df_filtrado.empty:
    st.info("No se encontraron productos con ese criterio.")
else:
    st.write("### Productos encontrados")
    # Ordenar por precio (ascendente) para ver el más barato primero
    df_filtrado = df_filtrado.sort_values("precio")
    
    # Mostrar cada producto con imagen, datos y botón para añadir al carrito
    for index, row in df_filtrado.iterrows():
        col1, col2 = st.columns([1,3])
        with col1:
            st.image(row["imagen"], width=100)
        with col2:
            st.markdown(f"**{row['titulo']}**")
            st.markdown(f"Categoría: {row['categoria']}")
            st.markdown(f"Precio: ${row['precio']:.2f}")
            st.markdown(f"[Ver producto]({row['link']})")
            if st.button("Añadir al carrito", key=f"cart_{index}"):
                st.session_state.cart.append({
                    "titulo": row["titulo"],
                    "precio": row["precio"],
                    "categoria": row["categoria"],
                    "link": row["link"],
                    "imagen": row["imagen"]
                })
                st.success("Producto añadido al carrito")
    

