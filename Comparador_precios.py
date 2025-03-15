import streamlit as st
import pandas as pd
import json
import glob
import os

# Título de la aplicación
st.title('🛒 Comparador de Precios de Supermercados')

# 1. Buscar todos los archivos JSON
json_files = glob.glob("*.json")
if not json_files:
    st.error("No se encontraron archivos JSON en la carpeta actual.")
    st.stop()

# 2. Leer y combinar los archivos JSON, asignando la empresa desde el nombre del archivo
data_list = []
for file in json_files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Extraer la parte antes del primer "_" para identificar la empresa
            brand = os.path.basename(file).split("_")[0]
            for item in data:
                item["empresa"] = brand
            data_list.extend(data)
    except Exception as e:
        st.error(f"Error leyendo {file}: {e}")

df = pd.DataFrame(data_list)

# Verificar que contenga las columnas esperadas (ajusta según tu formato)
expected_columns = {"titulo", "precios", "categoria", "imagen", "link", "empresa"}
missing_cols = expected_columns - set(df.columns)
if missing_cols:
    st.warning(f"Faltan columnas en el DataFrame: {missing_cols}. Ajusta tus archivos JSON o el código.")

# Función para extraer el precio principal
def extraer_precio(precio):
    """
    Se asume que 'precios' es una lista con al menos un elemento.
    Ej: ["2.50", "2.45"] -> devolvemos 2.50 como float.
    """
    if isinstance(precio, list) and len(precio) > 0:
        try:
            return float(precio[0])
        except (ValueError, TypeError):
            return None
    return None

# Crear columna 'precio' y eliminar productos sin precio
df["precio"] = df["precios"].apply(extraer_precio)
df.dropna(subset=["precio"], inplace=True)

# Ordenar el DataFrame por título
df = df.sort_values("titulo")

# Muestra un conteo de productos por empresa (para confirmar que se cargaron)
st.write("**Cantidad de productos por empresa:**")
st.write(df["empresa"].value_counts())

# 3. Inicializar el carrito de compra en session_state
if "cart" not in st.session_state:
    st.session_state.cart = []

# 4. Barra lateral: Carrito de Compra
st.sidebar.title("Carrito de Compra")
if st.sidebar.button("Ver carrito"):
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.sidebar.write(cart_df)
        total = cart_df["precio"].sum()
        st.sidebar.write(f"**Total: ${total:.2f}**")
    else:
        st.sidebar.write("El carrito está vacío.")

# 5. Filtro por categoría (selectbox)
st.subheader("Filtrar por Categoría")
categorias_unicas = sorted(df["categoria"].dropna().unique().tolist())
categoria_seleccionada = st.selectbox("Selecciona una categoría", categorias_unicas)

# Filtrar DataFrame según la categoría elegida
df_filtrado = df[df["categoria"] == categoria_seleccionada]
if df_filtrado.empty:
    st.error("No hay productos en la categoría seleccionada.")
    st.stop()

# 6. Desplegable de productos (según la categoría seleccionada)
st.subheader("Selecciona un producto")
productos_unicos = sorted(df_filtrado["titulo"].unique().tolist())
producto_seleccionado = st.selectbox("Selecciona un producto", productos_unicos)

# Filtrar por el producto elegido
df_producto = df_filtrado[df_filtrado["titulo"] == producto_seleccionado]
if df_producto.empty:
    st.info("No se encontraron productos con ese criterio.")
else:
    st.write("### Productos encontrados")
    df_producto = df_producto.sort_values("precio")

    # Mostrar cada producto con su imagen, empresa, precio, etc.
    for index, row in df_producto.iterrows():
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
            # Botón para añadir al carrito
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

   
