import streamlit as st
import pandas as pd
from TableExtractor import parse_pdf_schedule
from datetime import datetime
import requests           
import io
import datetime

# Título de la aplicación
st.title("Progra Matcher with love")

# Instrucciones para el usuario
st.write("Sube tu programación para ver si coincides con Pedro en algún momento :)")

url = f"https://drive.google.com/uc?id=1emmB5HefzZNNVSynAxJVIEsBq61C9pRp"

# Descargar el archivo y leerlo en un DataFrame
@st.cache_resource
def cargar_mi_progra():
    response = requests.get(url)
    df = pd.read_csv(io.StringIO(response.text), header=None)
    df = df.drop(columns=[0,6,7])
    df = df.rename(columns={1: "Departure", 2: "Origin", 3: "Arrival", 4: "Destination", 5: "Flight number"})

    df['Departure'] = pd.to_datetime(df['Departure'], format='%d/%m/%Y %H:%M')  # Ajusta el formato de fecha y hora
    df['Arrival'] = pd.to_datetime(df['Arrival'], format='%d/%m/%Y %H:%M')  

    return df

su_progra_file = st.file_uploader("Tu progra", type="pdf")


# Función para encontrar coincidencias con indicación del caso
def encontrar_coincidencias(df_su_progra, df_mi_progra):
    import datetime
    import pandas as pd

    resultados = []
    delta = datetime.timedelta(days=0, hours=2)

    for _, row_a in df_su_progra.iterrows():
        for _, row_b in df_mi_progra.iterrows():
            if ((abs(row_a['Departure'] - row_b['Departure']) <= delta) and 
                (row_a['Origin'] == row_b['Origin'])):
                # Combinar columnas de A y B junto con el caso
                resultado = {**row_a.to_dict(), **row_b.to_dict(), "match_case": "El día " + str(row_a['Departure'].strftime("%d/%m")) + " coincidiremos al salir de " + row_a['Origin']}
                resultados.append(resultado)
            if ((abs(row_a['Departure'] - row_b['Arrival']) <= delta) and 
                (row_a['Origin'] == row_b['Destination'])):
                resultado = {**row_a.to_dict(), **row_b.to_dict(), "match_case": "El día " + str(row_a['Departure'].strftime("%d/%m")) + " coincidiremos saliendo tu de/llegando yo a " + row_a['Origin']}
                resultados.append(resultado)
            if ((abs(row_a['Arrival'] - row_b['Departure']) <= delta) and 
                (row_a['Destination'] == row_b['Origin'])):
                resultado = {**row_a.to_dict(), **row_b.to_dict(), "match_case": "El día " + str(row_a['Departure'].strftime("%d/%m")) + " coincidiremos llegando tu a/saliendo yo de " + row_a['Origin']}
                resultados.append(resultado)
            if ((abs(row_a['Arrival'] - row_b['Arrival']) <= delta) and 
                (row_a['Destination'] == row_b['Destination'])):
                resultado = {**row_a.to_dict(), **row_b.to_dict(), "match_case": "El día " + str(row_a['Departure'].strftime("%d/%m")) + " coincidiremos al llegar a " + row_a['Origin']}
                resultados.append(resultado)

    df_matches = pd.DataFrame(resultados).drop_duplicates()

    return df_matches

# Procesar archivos y mostrar coincidencias
if su_progra_file:
    
    mi_progra = cargar_mi_progra()
    su_progra = parse_pdf_schedule(su_progra_file)

    st.write(encontrar_coincidencias(su_progra,mi_progra))


    # Encontrar coincidencias
    # coincidencias = encontrar_coincidencias(df_mi_programacion, df_programacion_amiga)
    
    # # Mostrar resultados
    # if not coincidencias.empty:
    #     st.success("¡Se encontraron coincidencias!")
    #     st.write("Aquí están los vuelos en los que coinciden:")
    #     st.table(coincidencias)
    # else:
    #     st.warning("No se encontraron coincidencias.")
