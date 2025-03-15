import streamlit as st
import pandas as pd
import json
import glob
import os

# Configurar el título de la aplicación
st.title('🛒 Comparador de Precios de Supermercados')

# Buscar archivos JSON con la fecha específica
archivos_json = glob.glob("*2025-03-15.json")

if not archivos_json:
    st.error("No se encontraron archivos JSON con la fecha 2025-03-15. Verifica que los archivos estén en la carpeta correcta.")
    st.stop()

# Lista para almacenar los datos combinados
dataframes = []

# Cargar y combinar los archivos JSON
for archivo in archivos_json:
    try:
        with open(archivo, "r", encoding="utf-8") as file:
            data = json.load(file)
            df_temp = pd.DataFrame(data)
            df_temp["supermercado"] = os.path.basename(archivo).split("_")[0]  # Extraer correctamente el nombre del supermercado
            dataframes.append(df_temp)
    except (FileNotFoundError, json.JSONDecodeError):
        st.error(f"Error al leer el archivo {archivo}. Verifica que tenga un formato válido.")
        st.stop()

# Concatenar los datos en un solo DataFrame
df = pd.concat(dataframes, ignore_index=True)

# Verificar columnas esperadas
expected_columns = {"titulo", "precios", "categoria", "imagen"}
if not expected_columns.issubset(df.columns):
    st.error(f"El archivo debe contener las columnas: {expected_columns}")
    st.stop()

# Función para extraer el precio
def extraer_precio(precio):
    if isinstance(precio, list) and len(precio) > 0:
        try:
            return float(precio[0])
        except ValueError:
            return None
    elif isinstance(precio, str):  # Para casos donde el precio es un string con caracteres
        try:
            return float(precio.replace("€", "").replace(",", ".").split(" ")[0])
        except ValueError:
            return None
    return None

# Convertir precios a formato numérico
df["precios"] = df["precios"].apply(extraer_precio)

# Verificar valores nulos
df = df.dropna(subset=["precios"])

# Buscar productos por palabra clave
palabra_clave = st.text_input("Busca un producto por nombre", "")

if palabra_clave:
    df_filtrado = df[df["titulo"].str.contains(palabra_clave, case=False, na=False)]
    
    if df_filtrado.empty:
        st.warning("No se encontraron productos con esa palabra clave.")
    else:
        # Mostrar productos en una cuadrícula de 3 en 3
        st.write("### Comparación de precios")
        df_filtrado = df_filtrado.sort_values(by="precios")
        
        cols = st.columns(3)  # Crear 3 columnas por fila
        for i, (_, row) in enumerate(df_filtrado.iterrows()):
            with cols[i % 3]:
                st.image(row["imagen"], caption=row["titulo"], width=150)
                st.write(f"**Categoría:** {row['categoria']}")
                st.write(f"**Supermercado:** {row['supermercado']}")
                st.write(f"**Precio:** {row['precios']:.2f}€")
                st.write("---")
else:
    st.info("Escribe una palabra clave para buscar productos.")
