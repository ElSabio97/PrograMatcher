import streamlit as st
import pandas as pd
from TableExtractor import parse_pdf_schedule
import requests
import io
from datetime import datetime, timedelta

# Título de la aplicación
st.title("Progra Matcher")

st.write("Sube tu programación para ver si coincides conmigo en en algún momento :)")

# Descargar programación personal
url = f"https://drive.google.com/uc?id=1emmB5HefzZNNVSynAxJVIEsBq61C9pRp"

@st.cache_resource
def cargar_mi_progra():
    response = requests.get(url)
    df = pd.read_csv(io.StringIO(response.text), header=None)
    df = df.drop(columns=[0, 6, 7])
    df = df.rename(columns={1: "Departure", 2: "Origin", 3: "Arrival", 4: "Destination", 5: "Flight number"})
    df['Departure'] = pd.to_datetime(df['Departure'], format='%d/%m/%Y %H:%M')
    df['Arrival'] = pd.to_datetime(df['Arrival'], format='%d/%m/%Y %H:%M')
    return df

su_progra_file = st.file_uploader("Tu progra", type="pdf")

# Ajuste del rango temporal
rango_tiempo = st.slider("Ajusta el máximo tiempo que queráis esperaros el uno al otro (en horas):", 0.25, 3.0, 0.5)
delta = timedelta(hours=rango_tiempo)

# Validación del archivo subido
if su_progra_file:
    if su_progra_file.type != "application/pdf":
        st.error("Por favor sube un archivo PDF válido.")
    else:
        try:
            su_progra = parse_pdf_schedule(su_progra_file)
            st.write(su_progra)

            # Cargar mi programación
            mi_progra = cargar_mi_progra()

            # Función para encontrar coincidencias
            def encontrar_coincidencias(df_su_progra, df_mi_progra):
                resultados = []
                for _, row_a in df_su_progra.iterrows():
                    for _, row_b in df_mi_progra.iterrows():

                        # Coincidimos saliendo
                        if ((abs(row_a['Departure'] - row_b['Departure']) <= delta) and 
                            (row_a['Origin'] == row_b['Origin'])):
                            resultado = {"Fecha": f"{row_a['Departure'].strftime('%d/%m')}", 
                                         "Lugar": f"{row_a['Origin']}",
                                         "Espera": f"{str(abs(row_a['Departure'] - row_b['Departure']))[-8:-3]}",
                                         "Detalles": f"Pedro sale a las {row_b['Departure'].strftime('%H:%M')} y Bea a las {row_a['Departure'].strftime('%H:%M')} {'posicionada con ' + row_a['Flight number'] + ' destino a ' +  row_a['Destination'] if row_a['Position'] == '*' else 'trabajando en SWT' + row_a['Flight number']}"}
                            resultados.append(resultado)

                        # Coincidimos yo llegando y ella saliendo
                        if ((abs(row_a['Departure'] - row_b['Arrival']) <= delta) and 
                            (row_a['Origin'] == row_b['Destination'])):
                            resultado = {"Fecha": f"{row_a['Departure'].strftime('%d/%m')}", 
                                         "Lugar": f"{row_a['Origin']}",
                                         "Espera": f"{str(abs(row_a['Departure'] - row_b['Arrival']))[-8:-3]}",
                                         "Detalles": f"Pedro llegará a las {row_b['Arrival'].strftime('%H:%M')} y Bea saldrá a las {row_a['Departure'].strftime('%H:%M')} {'posicionada con ' + row_a['Flight number'] + ' destino a ' +  row_a['Destination'] if row_a['Position'] == '*' else 'trabajando en SWT' + row_a['Flight number']}"}
                            resultados.append(resultado)

                        # Coincidimos yo saliendo y ella llegando
                        if ((abs(row_a['Arrival'] - row_b['Departure']) <= delta) and 
                            (row_a['Destination'] == row_b['Origin'])):
                            resultado = {"Fecha": f"{row_a['Arrival'].strftime('%d/%m')}", 
                                         "Lugar": f"{row_a['Destination']}",
                                         "Espera": f"{str(abs(row_a['Arrival'] - row_b['Departure']))[-8:-3]}",
                                         "Detalles": f"Pedro saldrá a las {row_b['Departure'].strftime('%H:%M')} y Bea llegarás a las {row_a['Arrival'].strftime('%H:%M')} {'posicionada con ' + row_a['Flight number'] + ' desde ' +  row_a['Origin'] if row_a['Position'] == '*' else 'trabajando en SWT' + row_a['Flight number']}"}
                            resultados.append(resultado)

                        # Coincidimos llegando
                        if ((abs(row_a['Arrival'] - row_b['Arrival']) <= delta) and 
                            (row_a['Destination'] == row_b['Destination'])):
                            resultado = {"Fecha": f"{row_a['Departure'].strftime('%d/%m')}", 
                                         "Lugar": f"{row_a['Destination']}",
                                         "Espera": f"{str(abs(row_a['Arrival'] - row_b['Arrival']))[-8:-3]}",
                                         "Detalles": f"Pedro llegará a las {row_b['Arrival'].strftime('%H:%M')} y Bea a las {row_a['Arrival'].strftime('%H:%M')} {'posicionada con ' + row_a['Flight number'] + ' desde ' +  row_a['Origin'] if row_a['Position'] == '*' else 'trabajando en SWT' + row_a['Flight number']}"}
                            resultados.append(resultado)

                df_matches = pd.DataFrame(resultados).drop_duplicates()
                
                return df_matches

            # Encontrar coincidencias
            coincidencias = encontrar_coincidencias(su_progra, mi_progra)
            
            # Mostrar resultados
            if not coincidencias.empty:
                st.success("It's a match! " + '\N{HEAVY BLACK HEART}')
                st.write("Estas son las oportunidades para veros:")
                st.dataframe(hide_index=True, data = coincidencias)
            else:
                st.warning("No se encontraron coincidencias.")
        except Exception as e:
            st.error(f"Hubo un error al procesar el archivo PDF: {e}")
