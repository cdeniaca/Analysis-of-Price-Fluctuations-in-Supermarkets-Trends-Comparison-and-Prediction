import streamlit as st
import pandas as pd
import json
import glob
import os

# Configurar la página
st.set_page_config(page_title="Comparador de Precios", layout="wide")

# ---- TÍTULO ----
st.markdown("<h1 style='text-align: center;'> 🛒 Comparador de Precios de Supermercados </h1>", unsafe_allow_html=True)

# ---- CARGA DE DATOS ----
archivos_json = glob.glob(os.path.join("./", "*_merged.json"))

if not archivos_json:
    st.error("❌ No se encontraron archivos JSON.")
    st.stop()

dataframes = []
for archivo in archivos_json:
    with open(archivo, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
            df_temp = pd.DataFrame(data)

            # ✅ Asegurar que la columna "supermercado" existe y no se pierde
            if "supermercado" in df_temp.columns:
                df_temp["supermercado"] = df_temp["supermercado"].fillna("Desconocido")
            else:
                df_temp["supermercado"] = "Desconocido"

            # ✅ Extraer correctamente el precio numérico
            def extraer_precio(precio):
                if isinstance(precio, str):
                    precio = precio.split("€")[0]  # Quitar "€" y posibles unidades
                    precio = precio.replace(",", ".")  # Cambiar coma por punto
                    try:
                        return float(precio.strip())  # Convertir a número
                    except ValueError:
                        return None
                return precio

            df_temp["precio"] = df_temp["precio"].apply(extraer_precio)

            # ✅ Corregir imágenes no disponibles
            df_temp["imagen"] = df_temp["imagen"].apply(
                lambda x: x if x and "no disponible" not in x.lower() else "https://via.placeholder.com/100"
            )

            dataframes.append(df_temp)

        except json.JSONDecodeError:
            st.warning(f"⚠️ Error al leer el archivo {archivo}. Verifica su formato.")

# ✅ Unir todos los datos sin filtrarlos
if dataframes:
    df = pd.concat(dataframes, ignore_index=True)
else:
    st.error("❌ No se pudo cargar ningún archivo JSON válido.")
    st.stop()

# ✅ Mostrar la cantidad de productos cargados antes de filtros
st.write(f"📊 **Productos totales disponibles:** {df.shape[0]}")

# ---- FILTROS ----
st.markdown("### 🎯 Filtrar productos:")

if "categoria_seleccionada" not in st.session_state:
    st.session_state.categoria_seleccionada = "Todas"
if "titulo_seleccionado" not in st.session_state:
    st.session_state.titulo_seleccionado = "Todos"
if "palabra_clave" not in st.session_state:
    st.session_state.palabra_clave = ""

col1, col2, col3 = st.columns(3)

with col1:
    categorias_unicas = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
    st.session_state.categoria_seleccionada = st.selectbox(
        "📂 Selecciona una categoría:", categorias_unicas, 
        index=categorias_unicas.index(st.session_state.categoria_seleccionada),
    )

if st.session_state.categoria_seleccionada != "Todas":
    df = df[df["categoria"] == st.session_state.categoria_seleccionada]

with col2:
    titulos_unicos = ["Todos"] + sorted(df["titulo"].dropna().unique().tolist())
    st.session_state.titulo_seleccionado = st.selectbox(
        "🏷️ Selecciona un producto:", titulos_unicos, 
        index=titulos_unicos.index(st.session_state.titulo_seleccionado),
    )

if st.session_state.titulo_seleccionado != "Todos":
    df = df[df["titulo"] == st.session_state.titulo_seleccionado]

with col3:
    st.session_state.palabra_clave = st.text_input("🔎 Escribe el nombre:", st.session_state.palabra_clave)

if st.session_state.palabra_clave:
    df = df[df["titulo"].str.contains(st.session_state.palabra_clave, case=False, na=False)]

# ✅ Mostrar la cantidad de productos después de aplicar filtros
st.write(f"📊 **Productos después de filtros:** {df.shape[0]}")

st.markdown("####")
if st.button("🧹 Borrar Filtros"):
    st.session_state.categoria_seleccionada = "Todas"
    st.session_state.titulo_seleccionado = "Todos"
    st.session_state.palabra_clave = ""
    st.rerun()

# ---- SECCIÓN DEL CARRITO ----
if "carrito" not in st.session_state:
    st.session_state.carrito = []

def agregar_al_carrito(producto):
    st.session_state.carrito.append(producto)
    st.success(f"✅ {producto['titulo']} agregado al carrito.")

if not df.empty:
    st.markdown("### 🏷️ Productos encontrados:")
    df = df.sort_values(by="precio")
    cols = st.columns(4)

    for i, (_, row) in enumerate(df.iterrows()):
        with cols[i % 4]:
            with st.container():
                st.image(row["imagen"], width=100)
                st.write(f"**{row['titulo']}**")
                st.write(f"🏪 {row['supermercado']} | 📂 {row['categoria']}")
                st.write(f"💰 **{row['precio']:.2f}€**")
                if st.button(f"🛒 Agregar", key=f"add_{i}"):
                    agregar_al_carrito(row.to_dict())

else:
    st.warning("⚠️ No se encontraron productos con los filtros seleccionados.")

# ---- LISTA DE COMPRA ----
st.header("🛍️ Lista de Compra para Imprimir")

if not st.session_state.carrito:
    st.info("Tu carrito está vacío. Agrega productos para empezar.")
else:
    carrito_df = pd.DataFrame(st.session_state.carrito)
    total_compra = carrito_df["precio"].sum()
    st.write(f"💰 **Total de la compra:** {total_compra:.2f}€")

    lista_compra_txt = "🛒 **Lista de Compra**\n\n"
    for supermercado in carrito_df["supermercado"].unique():
        lista_compra_txt += f"🏪 {supermercado}\n" + "-" * len(supermercado) + "\n"
        productos_super = carrito_df[carrito_df["supermercado"] == supermercado]
        for _, row in productos_super.iterrows():
            lista_compra_txt += f"  [ ] {row['titulo']} - {row['precio']:.2f}€\n"
        lista_compra_txt += "\n"

    st.text_area("📜 Copia esta lista:", lista_compra_txt, height=300)
    st.download_button("📥 Descargar TXT", data=lista_compra_txt, file_name="lista_compra.txt", mime="text/plain")

    if st.button("🛒 Vaciar Todo el Carrito"):
        st.session_state.carrito = []
        st.rerun()
