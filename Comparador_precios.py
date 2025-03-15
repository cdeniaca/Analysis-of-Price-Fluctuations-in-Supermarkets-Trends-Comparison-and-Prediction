import streamlit as st
import pandas as pd
import json
import os

# 📂 RUTA DEL ARCHIVO JSON (Asegúrate que esté correcto)
file_path = "/mnt/data/mercadona_2025-03-15.json"

# 🔍 Verificar si el archivo JSON existe antes de leerlo
if not os.path.exists(file_path):
    st.error(f"❌ Archivo JSON no encontrado en la ruta: {file_path}")
    st.stop()
else:
    st.success(f"✅ Archivo JSON encontrado en: {file_path}")

# ---- CARGA DE DATOS ----
st.write("📂 Cargando datos...")

# 📦 Leer el JSON en partes para evitar problemas con archivos grandes
data = []
try:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Convertir a DataFrame
    df = pd.DataFrame(data)
    st.success(f"✅ {df.shape[0]} productos cargados correctamente.")

except json.JSONDecodeError:
    st.error("❌ Error al cargar el archivo JSON. Verifica el formato del archivo.")
    st.stop()

# ---- VERIFICACIONES ----
if "supermercado" not in df.columns:
    df["supermercado"] = "Desconocido"

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
    st.session_state.categoria_seleccionada = st.selectbox("📂 Selecciona una categoría:", categorias_unicas)

if st.session_state.categoria_seleccionada != "Todas":
    df = df[df["categoria"] == st.session_state.categoria_seleccionada]

with col2:
    titulos_unicos = ["Todos"] + sorted(df["titulo"].dropna().unique().tolist())
    st.session_state.titulo_seleccionado = st.selectbox("🏷️ Selecciona un producto:", titulos_unicos)

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
                    <div style="border: 2px solid #32C3FF; border-radius: 10px; padding: 8px;
                        text-align: center; background-color: #D0F1FF;">
                        <img src="{row['imagen']}" width="100" style="border-radius: 6px;">
                        <h3 style="font-size: 12px; color: black;">{row['titulo']}</h3>
                        <p style="color: black; font-size: 11px; text-align: center;">
                            🏪 <b>Supermercado:</b> {row['supermercado']}<br>
                            📂 <b>Categoría:</b> {row['categoria']}<br>
                            💰 <b>Precio:</b> {row['precio']:.2f}€
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(f"🛒 Agregar al Carrito", key=f"add_{i}"):
                    agregar_al_carrito(row.to_dict())

else:
    st.warning("⚠️ No se encontraron productos con los filtros seleccionados.")

# ---- LISTA DE COMPRA ----
st.header("🛍️ Lista de Compra")

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
