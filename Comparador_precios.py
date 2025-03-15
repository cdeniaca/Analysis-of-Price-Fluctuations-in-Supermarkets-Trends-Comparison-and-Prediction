import streamlit as st
import pandas as pd
import json
import glob
import os

# Configurar el título de la aplicación
st.title('🛒 Comparador de Precios de Supermercados')

# Buscar archivos JSON en la carpeta correcta
folder_path = "C:/Users/crist/OneDrive/Escritorio/Proyecto final/"
archivos_json = glob.glob(os.path.join(folder_path, "*merged.json"))

if not archivos_json:
    st.error("No se encontraron archivos JSON con la fecha 2025-03-15. Verifica la ubicación de los archivos.")
    st.stop()

# Lista para almacenar los datos combinados
dataframes = []

# Cargar y combinar los archivos JSON
for archivo in archivos_json:
    try:
        with open(archivo, "r", encoding="utf-8") as file:
            data = json.load(file)
            df_temp = pd.DataFrame(data)

            # Detectar columnas de precios según el supermercado
            if "precios" in df_temp.columns:
                df_temp["precio"] = df_temp["precios"].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)
            elif "precio" in df_temp.columns:
                df_temp["precio"] = df_temp["precio"]
            else:
                st.warning(f"⚠️ El archivo {archivo} no contiene una columna de precios válida.")
                continue

            # Extraer el nombre del supermercado (antes del primer "_")
            nombre_archivo = os.path.basename(archivo)
            supermercado_nombre = nombre_archivo.split("_")[0]
            df_temp["supermercado"] = supermercado_nombre

            dataframes.append(df_temp)

    except (FileNotFoundError, json.JSONDecodeError):
        st.error(f"⚠️ Error al leer el archivo {archivo}. Verifica que tenga un formato válido.")
        st.stop()

# Concatenar los datos en un solo DataFrame
df = pd.concat(dataframes, ignore_index=True)

# Verificar columnas esperadas
expected_columns = {"titulo", "precio", "categoria", "imagen"}
if not expected_columns.issubset(df.columns):
    st.error(f"⚠️ El archivo debe contener las columnas: {expected_columns}")
    st.stop()

# Función para extraer el precio
def extraer_precio(precio):
    if isinstance(precio, str):  # Para casos donde el precio es un string con caracteres
        try:
            return float(precio.replace("€", "").replace(",", ".").split(" ")[0])
        except ValueError:
            return None
    elif isinstance(precio, (int, float)):
        return float(precio)
    return None

# Convertir precios a formato numérico
df["precio"] = df["precio"].apply(extraer_precio)

# Eliminar filas con precios inválidos
df = df.dropna(subset=["precio"])

# Buscar productos por palabra clave
palabra_clave = st.text_input("🔍 Busca un producto por nombre", "")

if palabra_clave:
    df_filtrado = df[df["titulo"].str.contains(palabra_clave, case=False, na=False)]
    
    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron productos con esa palabra clave.")
    else:
        # Mostrar productos en una tabla si hay más de 10 resultados
        if len(df_filtrado) > 10:
            st.write("### 📋 Comparación de precios en tabla")
            st.dataframe(df_filtrado[["titulo", "supermercado", "categoria", "precio"]].sort_values(by="precio"))
        else:
            # Mostrar productos con imágenes si hay pocos resultados
            st.write("### 🏷️ Comparación de precios con imágenes")
            df_filtrado = df_filtrado.sort_values(by="precio")
            
            cols = st.columns(3)  # Crear 3 columnas por fila
            for i, (_, row) in enumerate(df_filtrado.iterrows()):
                with cols[i % 3]:
                    st.image(row["imagen"], caption=row["titulo"], width=150)
                    st.write(f"**Categoría:** {row['categoria']}")
                    st.write(f"**Supermercado:** {row['supermercado']}")
                    st.write(f"**Precio:** {row['precio']:.2f}€")
                    st.write("---")
else:
    st.info("💡 Escribe una palabra clave para buscar productos.")
