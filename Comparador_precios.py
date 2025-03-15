import streamlit as st
import pandas as pd
import json
import glob
import os

# Configurar el título de la aplicación
st.title('🛒 Comparador de Precios de Supermercados')

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
expected_columns = {"titulo", "precio", "categoria", "imagen"}
if not expected_columns.issubset(df.columns):
    st.stop()

# Reemplazar valores vacíos en la columna "imagen"
placeholder_img = "https://via.placeholder.com/150"
df["imagen"] = df["imagen"].fillna(placeholder_img)

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
palabra_clave = st.text_input("🔍 Busca un producto por nombre", "")

if palabra_clave:
    df_filtrado = df[df["titulo"].str.contains(palabra_clave, case=False, na=False)]
    
    if not df_filtrado.empty:
        # Mostrar productos en tabla si hay más de 10 resultados
        if len(df_filtrado) > 10:
            st.dataframe(df_filtrado[["titulo", "supermercado", "categoria", "precio"]].sort_values(by="precio"))
        else:
            # Mostrar productos con imágenes si hay pocos resultados
            df_filtrado = df_filtrado.sort_values(by="precio")
            cols = st.columns(3)
            for i, (_, row) in enumerate(df_filtrado.iterrows()):
                with cols[i % 3]:
                    st.image(row["imagen"], caption=row["titulo"], width=150)
                    st.write(f"**Categoría:** {row['categoria']}")
                    st.write(f"**Supermercado:** {row['supermercado']}")
                    st.write(f"**Precio:** {row['precio']:.2f}€")
                    if st.button(f"🛒 Agregar {row['titulo']}", key=f"add_{i}"):
                        agregar_al_carrito(row.to_dict())
else:
    st.info("💡 Escribe una palabra clave para buscar productos.")

# ---- SECCIÓN DEL CARRITO ----

st.header("🛍️ Tu Carrito de Compras")

if not st.session_state.carrito:
    st.info("Tu carrito está vacío. Agrega productos para empezar.")
else:
    # Organizar los productos en el carrito por supermercado
    carrito_df = pd.DataFrame(st.session_state.carrito)
    total_compra = carrito_df["precio"].sum()
    
    # Mostrar los productos organizados por supermercado
    for supermercado in carrito_df["supermercado"].unique():
        st.subheader(f"🏪 {supermercado}")
        carrito_super = carrito_df[carrito_df["supermercado"] == supermercado]
        for _, row in carrito_super.iterrows():
            st.write(f"🛒 **{row['titulo']}** - {row['precio']:.2f}€")
    
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
