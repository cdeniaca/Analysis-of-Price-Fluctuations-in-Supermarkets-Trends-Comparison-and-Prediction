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
        data = json.load(file)
        df_temp = pd.DataFrame(data)

        # 🔹 Verificar si la columna "supermercado" existe en el JSON
        if "supermercado" in df_temp.columns:
            df_temp["supermercado"] = df_temp["supermercado"].fillna("Desconocido")  # Rellenar vacíos si hay
        else:
            df_temp["supermercado"] = "Desconocido"  # Asignar por defecto si falta la columna

        dataframes.append(df_temp)

# Unir todos los archivos en un solo DataFrame
df = pd.concat(dataframes, ignore_index=True)

# 🔹 Verificar si la columna tiene valores vacíos
if df["supermercado"].isnull().sum() > 0 or df["supermercado"].eq("").sum() > 0:
    st.warning("⚠️ Hay productos sin un supermercado asignado. Verifica los archivos JSON.")

df["imagen"] = df["imagen"].fillna("https://via.placeholder.com/100")
df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
df = df.dropna(subset=["precio"])

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
                st.markdown(
                    f"""
                    <div style="
                        border: 2px solid #32C3FF;
                        border-radius: 10px;
                        padding: 8px;
                        text-align: center;
                        background-color: #D0F1FF;
                        min-height: 380px;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <img src="{row['imagen']}" width="100" style="border-radius: 6px; max-width: 100%; margin-top: 3px;">
                        <h3 style="font-size: 12px; color: black; margin: 4px 0;">{row['titulo']}</h3>
                        <p style="color: black; font-size: 11px; text-align: center;">
                            🏪 <b>Supermercado:</b> {row['supermercado']}<br>
                            📂 <b>Categoría:</b> {row['categoria']}<br>
                            💰 <b>Precio:</b> {row['precio']:.2f}€
                        </p>
                        <div style="width: 100%; margin-top: auto;">
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(f"🛒 Agregar al Carrito", key=f"add_{i}"):
                    agregar_al_carrito(row.to_dict())

                st.markdown("</div></div>", unsafe_allow_html=True)
else:
    st.warning("⚠️ No se encontraron productos con los filtros seleccionados.")

# ---- LISTA DE COMPRA PARA IMPRIMIR ----
st.header("🛍️ Lista de Compra para Imprimir")

if not st.session_state.carrito:
    st.info("Tu carrito está vacío. Agrega productos para empezar.")
else:
    carrito_df = pd.DataFrame(st.session_state.carrito)
    total_compra = carrito_df["precio"].sum()

    st.write(f"💰 **Total de la compra:** {total_compra:.2f}€")

    lista_compra_txt = "🛒 **Lista de Compra**\n\n"

    for supermercado in carrito_df["supermercado"].unique():
        lista_compra_txt += f"🏪 {supermercado}\n"
        lista_compra_txt += "-" * len(supermercado) + "\n"

        productos_super = carrito_df[carrito_df["supermercado"] == supermercado]
        for categoria in productos_super["categoria"].unique():
            lista_compra_txt += f"  📂 {categoria}\n"
            lista_compra_txt += "  " + "-" * len(categoria) + "\n"

            for _, row in productos_super[productos_super["categoria"] == categoria].iterrows():
                lista_compra_txt += f"    [ ] {row['titulo']} - {row['precio']:.2f}€\n"

    st.text_area("📜 Copia esta lista:", lista_compra_txt, height=300)
    st.download_button("📥 Descargar TXT", data=lista_compra_txt, file_name="lista_compra.txt", mime="text/plain")
    
    if st.button("🛒 Vaciar Todo el Carrito"):
        st.session_state.carrito = []
        st.rerun()
