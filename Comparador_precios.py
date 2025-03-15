import streamlit as st
import pandas as pd
import json
import glob

# Configurar el título de la aplicación
st.title('🛒 Comparador de Precios de Supermercados')

# Buscar archivo JSON con la fecha específica
archivo_json = glob.glob("*2025-03-15.json")

if not archivo_json:
    st.error("No se encontró un archivo JSON con la fecha 2025-03-15. Verifica que el archivo esté en la carpeta correcta.")
    st.stop()

# Cargar el archivo JSON encontrado
try:
    with open(archivo_json[0], "r", encoding="utf-8") as file:
        data = json.load(file)
except FileNotFoundError:
    st.error("El archivo JSON no se encontró. Verifica que esté en la misma carpeta.")
    st.stop()
except json.JSONDecodeError:
    st.error("Error al leer el archivo JSON. Verifica que tenga un formato válido.")
    st.stop()

# Convertir datos a DataFrame
df = pd.DataFrame(data)

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
    return None

# Convertir precios a formato numérico
df["precios"] = df["precios"].apply(extraer_precio)

# Verificar valores nulos
if df["precios"].isnull().values.any():
    st.warning("El archivo contiene productos sin precio. Se recomienda limpiar los datos antes de continuar.")
    df = df.dropna()

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
                st.write(f"**Precio:** ${row['precios']}")
                st.write("---")
else:
    st.info("Escribe una palabra clave para buscar productos.")
