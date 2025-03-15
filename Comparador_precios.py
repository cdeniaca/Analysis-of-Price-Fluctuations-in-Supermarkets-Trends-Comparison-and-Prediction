import streamlit as st
import pandas as pd
import json
import glob
import os

# Configurar el diseño de la página para ocupar más espacio
st.set_page_config(page_title="Comparador de Precios", layout="wide")

# Configurar el título de la aplicación con emojis y estilo
st.markdown("<h1 style='text-align: center;'> 🛒 Comparador de Precios de Supermercados </h1>", unsafe_allow_html=True)

# Buscar archivos JSON en la carpeta del repositorio
archivos_json = glob.glob(os.path.join("./", "*_merged.json"))

if not archivos_json:
    st.error("❌ No se encontraron archivos JSON con la fecha 2025-03-15.")
    st.stop()

# Lista para almacenar los datos combinados
dataframes = []

# Cargar y combinar los archivos JSON
for archivo in archivos_json:
    try:
        with open(archivo, "r", encoding="utf-8") as file:
            data = json.load(file)
            df_temp = pd.DataFrame(data)

            # Detectar columnas de precios
            if "precios" in df_temp.columns:
                df_temp["precio"] = df_temp["precios"].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)
            elif "precio" in df_temp.columns:
                df_temp["precio"] = df_temp["precio"]
            else:
                continue  # Ignorar archivos sin precios

            # Extraer el nombre del supermercado desde el archivo
            supermercado_nombre = os.path.basename(archivo).split("_")[0]
            df_temp["supermercado"] = supermercado_nombre

            dataframes.append(df_temp)

    except (FileNotFoundError, json.JSONDecodeError):
        st.stop()

# Concatenar los datos en un solo DataFrame
df = pd.concat(dataframes, ignore_index=True)

# Verificar columnas esperadas
expected_columns = {"titulo", "precio", "categoria", "imagen", "supermercado"}
if not expected_columns.issubset(df.columns):
    st.stop()

# Reemplazar valores vacíos en la columna "imagen"
placeholder_img = "https://via.placeholder.com/150"
df["imagen"] = df["imagen"].fillna(placeholder_img)

# Asegurar que la columna "supermercado" no esté vacía
df["supermercado"] = df["supermercado"].fillna("Desconocido")

# Función para extraer el precio
def extraer_precio(precio):
    if isinstance(precio, str):
        try:
            return float(precio.replace("€", "").replace(",", ".").split(" ")[0])
        except ValueError:
            return None
    elif isinstance(precio, (int, float)):
        return float(precio)
    return None

# Convertir precios a formato numérico y eliminar valores inválidos
df["precio"] = df["precio"].apply(extraer_precio)
df = df.dropna(subset=["precio"])

# ---- SECCIÓN DEL CARRITO ----

# Inicializar el carrito de compras en la sesión de Streamlit
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# Función para agregar productos al carrito
def agregar_al_carrito(producto):
    st.session_state.carrito.append(producto)
    st.success(f"✅ {producto['titulo']} agregado al carrito.")

# Buscar productos por palabra clave
st.markdown("### 🔎 Busca un producto por nombre:")
palabra_clave = st.text_input("", "")

if palabra_clave:
    df_filtrado = df[df["titulo"].str.contains(palabra_clave, case=False, na=False)]
    
    if not df_filtrado.empty:
        st.markdown("### 🏷️ Productos encontrados:")

        df_filtrado = df_filtrado.sort_values(by="precio")
        cols = st.columns(4)  # Expandimos la cuadrícula a 4 columnas

        for i, (_, row) in enumerate(df_filtrado.iterrows()):
            with cols[i % 4]:  # Asegurar estructura homogénea en 4 columnas
                with st.container():
                    st.image(row["imagen"], caption=row["titulo"], width=180)

                    # Asegurar alineación de textos
                    st.markdown(f"### {row['titulo']}", unsafe_allow_html=True)
                    st.markdown(f"🏪 **Supermercado:** {row['supermercado']}", unsafe_allow_html=True)
                    st.markdown(f"📂 **Categoría:** {row['categoria']}", unsafe_allow_html=True)
                    st.markdown(f"💰 **Precio:** {row['precio']:.2f}€", unsafe_allow_html=True)

                    # Botón uniforme para agregar al carrito
                    st.button(f"🛒 Agregar {row['titulo']}", key=f"add_{i}", on_click=agregar_al_carrito, args=(row.to_dict(),))
    else:
        st.warning("⚠️ No se encontraron productos con esa palabra clave.")
else:
    st.info("💡 Escribe una palabra clave para buscar productos.")

# ---- SECCIÓN DEL CARRITO ----

st.header("🛍️ Tu Carrito de Compras")

if not st.session_state.carrito:
    st.info("Tu carrito está vacío. Agrega productos para empezar.")
else:
    carrito_df = pd.DataFrame(st.session_state.carrito)
    total_compra = carrito_df["precio"].sum()
    
    # Mostrar los productos organizados por supermercado
    for supermercado in carrito_df["supermercado"].unique():
        st.subheader(f"🏪 {supermercado}")
        carrito_super = carrito_df[carrito_df["supermercado"] == supermercado]
        cols = st.columns(4)  # Expandimos la cuadrícula a 4 columnas

        for i, (_, row) in enumerate(carrito_super.iterrows()):
            with cols[i % 4]:
                with st.container():
                    st.image(row["imagen"], caption=row["titulo"], width=140)
                    st.markdown(f"💰 **Precio:** {row['precio']:.2f}€")

    st.write(f"💰 **Total de la compra:** {total_compra:.2f}€")
    
    # Botón para imprimir la lista de compra
    if st.button("🖨️ Imprimir Lista de Compra"):
        lista_compra = "\n".join(
            [
                f"{row['titulo']} - {row['precio']:.2f}€ ({row['supermercado']})"
                for _, row in carrito_df.iterrows()
            ]
        )
        st.text_area("📋 Copia tu lista de compra:", lista_compra, height=200)

    # Botón para vaciar el carrito
    if st.button("🗑️ Vaciar Carrito"):
        st.session_state.carrito = []
        st.experimental_rerun()
