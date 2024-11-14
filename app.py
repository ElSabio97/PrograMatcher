import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# Título de la aplicación
st.title("Comparador de Programación de Vuelos")

# Instrucciones para el usuario
st.write("Sube tu programación en formato CSV y la programación de tu amiga en formato HTML para ver si coinciden en algún vuelo.")

# Subir archivos
csv_file = st.file_uploader("Tu programación (CSV)", type="csv")
html_file = st.file_uploader("Programación de tu amiga (HTML)", type="html")

# Función para cargar y procesar el CSV
def cargar_programacion_csv(file):
    df = pd.read_csv(file)
    df['Hora'] = pd.to_datetime(df['Hora'], format='%H:%M')  # Asegura el formato datetime
    return df[['Origen', 'Destino', 'Hora']]

# Función para cargar y procesar el HTML
def cargar_programacion_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    vuelos = []
    for row in soup.select('table#memo tr'):  # Ajusta el selector según el HTML
        columns = row.find_all('td')
        if columns:
            origen = columns[0].text.strip()
            destino = columns[1].text.strip()
            hora = datetime.strptime(columns[2].text.strip(), '%H:%M')  # Ajusta el formato si es necesario
            vuelos.append({'Origen': origen, 'Destino': destino, 'Hora': hora})
    return pd.DataFrame(vuelos)

# Función para encontrar coincidencias
def encontrar_coincidencias(df1, df2):
    coincidencias = pd.merge(df1, df2, on=['Origen', 'Destino', 'Hora'])
    return coincidencias

# Procesar archivos y mostrar coincidencias
if csv_file and html_file:
    # Cargar programación CSV y HTML
    df_mi_programacion = cargar_programacion_csv(csv_file)
    html_content = html_file.read().decode('utf-8')
    df_programacion_amiga = cargar_programacion_html(html_content)

    # Encontrar coincidencias
    coincidencias = encontrar_coincidencias(df_mi_programacion, df_programacion_amiga)
    
    # Mostrar resultados
    if not coincidencias.empty:
        st.success("¡Se encontraron coincidencias!")
        st.write("Aquí están los vuelos en los que coinciden:")
        st.table(coincidencias)
    else:
        st.warning("No se encontraron coincidencias.")
