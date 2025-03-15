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
            data_list.extend(data)  # Agregar todos los productos a la lista
    except Exception as e:
        st.error(f"Error leyendo {file}: {e}")

df = pd.DataFrame(data_list)

# 3. Verificar columnas esperadas
expected_columns = {"titulo", "precios", "categoria", "imagen", "link"}
missing_cols = expected_columns - set(df.columns)
if missing_cols:
    st.warning(f"Faltan columnas en el DataFrame: {missing_cols}. Ajusta tu código o tus archivos JSON.")
    # Si faltan columnas críticas, podrías hacer stop:
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

# 5. Crear columna 'precio' con formato numérico y eliminar productos sin precio
df["precio"] = df["precios"].apply(extraer_precio)
df.dropna(subset=["precio"], inplace=True)

# Ordenar el DataFrame por título (para el selectbox)
df = df.sort_values("titulo")

# 6. Inicializar el carrito de compra en session_state
if "cart" not in st.session_state:
    st.session_state.cart = []

# 7. Barra lateral (sidebar) para el carrito
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

# 8. Desplegable para seleccionar un producto (por su título)
titulos_unicos = df["titulo"].unique().tolist()
producto_seleccionado = st.selectbox("Selecciona un producto", titulos_unicos)

# 9. Filtrar DataFrame para mostrar solo el producto seleccionado (y sus variantes)
df_filtrado = df[df["titulo"].str.contains(producto_seleccionado, case=False, na=False)]

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
            st.markdown(f"Categoría: {row['categoria']}")
            st.markdown(f"Precio: ${row['precio']:.2f}")
            # Solo mostrar link si existe en el DataFrame
            if "link" in row and pd.notna(row["link"]):
                st.markdown(f"[Ver producto]({row['link']})")
            
            # Botón para añadir al carrito
            if st.button("Añadir al carrito", key=f"cart_{index}"):
                st.session_state.cart.append({
                    "titulo": row["titulo"],
                    "precio": row["precio"],
                    "categoria": row["categoria"],
                    "link": row["link"] if "link" in row else "",
                    "imagen": row["imagen"]
                })
                st.success("Producto añadido al carrito")

  
