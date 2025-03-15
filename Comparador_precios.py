import streamlit as st
import pandas as pd
import json
import glob
import os

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
                    st.write("---")
    else:
        st.warning("⚠️ No se encontraron productos con esa palabra clave.")
