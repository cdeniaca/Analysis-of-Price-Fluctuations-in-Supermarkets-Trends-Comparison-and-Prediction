import streamlit as st
import pandas as pd
import json
import glob
import os

# Configurar la página para ocupar más espacio
st.set_page_config(page_title="Comparador de Precios", layout="wide")

# Configurar el título de la aplicación
st.markdown("<h1 style='text-align: center;'> 🛒 Comparador de Precios de Supermercados </h1>", unsafe_allow_html=True)

# Buscar archivos JSON
archivos_json = glob.glob(os.path.join("./", "*_merged.json"))

if not archivos_json:
    st.error("❌ No se encontraron archivos JSON.")
    st.stop()

# Cargar los datos JSON en un DataFrame
dataframes = []
for archivo in archivos_json:
    with open(archivo, "r", encoding="utf-8") as file:
        data = json.load(file)
        df_temp = pd.DataFrame(data)

        # Extraer el nombre del supermercado desde el archivo
        supermercado_nombre = os.path.basename(archivo).split("_")[0]
        df_temp["supermercado"] = supermercado_nombre
        dataframes.append(df_temp)

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

# Convertir precios a numérico
df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
df = df.dropna(subset=["precio"])

# ---- SECCIÓN DEL CARRITO ----

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
        cols = st.columns(4)

        for i, (_, row) in enumerate(df_filtrado.iterrows()):
            with cols[i % 4]:
                with st.container():
                    # Crear un rectángulo con fondo personalizado y botón dentro
                    st.markdown(
                        f"""
                        <div style="
                            border: 2px solid #32C3FF;
                            border-radius: 12px;
                            padding: 15px;
                            text-align: center;
                            background-color: #D0F1FF;
                            min-height: 520px;
                            display: flex;
                            flex-direction: column;
                            justify-content: space-between;
                            align-items: center;
                        ">
                        """,
                        unsafe_allow_html=True,
                    )

                    # Imagen del producto
                    st.image(row["imagen"], width=140)

                    # Información del producto
                    st.markdown(f"### {row['titulo']}", unsafe_allow_html=True)
                    st.markdown(f"🏪 **Supermercado:** {row['supermercado']}")
                    st.markdown(f"📂 **Categoría:** {row['categoria']}")
                    st.markdown(f"💰 **Precio:** {row['precio']:.2f}€")

                    # Botón funcional de Streamlit dentro del recuadro
                    if st.button(f"🛒 Agregar al Carrito", key=f"add_{i}"):
                        agregar_al_carrito(row.to_dict())

                    # Cerrar div
                    st.markdown("</div>", unsafe_allow_html=True)
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

    # Mostrar productos organizados por supermercado
    for supermercado in carrito_df["supermercado"].unique():
        st.subheader(f"🏪 {supermercado}")
        carrito_super = carrito_df[carrito_df["supermercado"] == supermercado]
        cols = st.columns(4)

        for i, (_, row) in enumerate(carrito_super.iterrows()):
            with cols[i % 4]:
                with st.container():
                    st.image(row["imagen"], caption=row["titulo"], width=140)
                    st.markdown(f"💰 **Precio:** {row['precio']:.2f}€")

    st.write(f"💰 **Total de la compra:** {total_compra:.2f}€")
    
    # Botón para imprimir la lista de compra
    if st.button("🖨️ Imprimir Lista de Compra"):
        lista_compra = "\n".join(
            [f"{row['titulo']} - {row['precio']:.2f}€ ({row['supermercado']})" for _, row in carrito_df.iterrows()]
        )
        st.text_area("📋 Copia tu lista de compra:", lista_compra, height=200)

    # Botón para vaciar el carrito
    if st.button("🗑️ Vaciar Carrito"):
        st.session_state.carrito = []
        st.experimental_rerun()
