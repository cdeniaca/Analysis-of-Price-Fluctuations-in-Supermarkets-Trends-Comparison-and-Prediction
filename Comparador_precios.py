import streamlit as st
import pandas as pd
import json
import glob
import os

# Título de la aplicación
st.title('🛒 Comparador de Precios de Supermercados')

# 1. Buscar todos los archivos JSON que terminen en "merged.json"
json_files = glob.glob("*.json")

if not json_files:
    st.error("No se encontraron archivos JSON que terminen en '.json' en la carpeta actual.")
    st.stop()

# 2. Leer y combinar los archivos JSON
data_list = []
for file in json_files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Extraer el nombre de la empresa (hasta el primer "_")
            brand = os.path.basename(file).split("_")[0]
            # Añadir la columna "empresa" a cada producto
            for item in data:
                item["empresa"] = brand
            data_list.extend(data)
    except Exception as e:
        st.error(f"Error leyendo {file}: {e}")

# 3. Convertir la lista de datos en DataFrame
df = pd.DataFrame(data_list)

# Verificar columnas esperadas (ajusta según tus datos)
expected_columns = {"titulo", "precios", "categoria", "imagen", "link", "empresa"}
missing_cols = expected_columns - set(df.columns)
if missing_cols:
    st.warning(f"Faltan columnas en el DataFrame: {missing_cols}. Ajusta tus archivos JSON o el código.")
    # Si son columnas críticas, podrías detener la app:
    # st.stop()

# 4. Función para extraer el precio principal (si 'precios' es una lista)
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

# Crear columna 'precio' con formato numérico y eliminar productos sin precio
df["precio"] = df["precios"].apply(extraer_precio)
df.dropna(subset=["precio"], inplace=True)

# Ordenar el DataFrame por título (para el selectbox)
df = df.sort_values("titulo")

# 5. Inicializar el carrito de compra en session_state
if "cart" not in st.session_state:
    st.session_state.cart = []

# 6. Barra lateral (sidebar) para el carrito
st.sidebar.title("Carrito de Compra")

# Botón para ver el contenido del carrito
if st.sidebar.button("Ver carrito"):
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.sidebar.write(cart_df)
        total = cart_df["precio"].sum()
        st.sidebar.write(f"**Total: ${total:.2f}**")
    else:
        st.sidebar.write("El carrito está vacío.")

# 7. Desplegable para seleccionar un producto (por su título exacto)
titulos_unicos = df["titulo"].unique().tolist()
producto_seleccionado = st.selectbox("Selecciona un producto", titulos_unicos)

# 8. Filtrar DataFrame para mostrar solo el producto seleccionado (match exacto)
df_filtrado = df[df["titulo"] == producto_seleccionado]

if df_filtrado.empty:
    st.info("No se encontraron productos con ese criterio.")
else:
    st.write("### Productos encontrados")

    # Ordenar por precio ascendente para ver primero el más barato
    df_filtrado = df_filtrado.sort_values("precio")

    # Mostrar cada producto con imagen, datos y botón para añadir al carrito
    for index, row in df_filtrado.iterrows():
        col1, col2 = st.columns([1,3])
        with col1:
            st.image(row["imagen"], width=100)
        with col2:
            st.markdown(f"**{row['titulo']}**")
            st.markdown(f"Empresa: {row['empresa']}")  # Muestra la empresa extraída
            st.markdown(f"Categoría: {row['categoria']}")
            st.markdown(f"Precio: ${row['precio']:.2f}")
            # Enlace del producto (si existe)
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

