# obtener_urls.py
from datetime import datetime
from lxml import html
import requests
import os
import csv
import pandas as pd
from tqdm import tqdm

urlsArticulos = {}
errores = 0
snapError = []

if not os.path.exists('articulos_x_procesar/ELPAIS_ESP'):
    os.makedirs('articulos_x_procesar/ELPAIS_ESP')

if not os.path.exists('log_ejecuciones/ELPAIS_ESP'):
    os.makedirs('log_ejecuciones/ELPAIS_ESP')

origen = "ElPais"
url = "https://web.archive.org/cdx/search/cdx"
parametros = {'url': 'www.elpais.com', 'from': '20200214', 'to': '20250405'}
headers = {'Accept': '*/*'}

try:
    respuesta = requests.get(url, params=parametros, timeout=100)
    if respuesta.status_code == 200:
        rtaWebArchive = respuesta.text
    else:
        raise Exception(f"Error: Código de estado {respuesta.status_code}")
except requests.exceptions.RequestException as e:
    raise Exception(f"Error en la solicitud: {e}")

lstSnapWebArchive = rtaWebArchive.strip().split('\n')
snapShotsWebArchive = {}

for snap in lstSnapWebArchive:
    snapFecha = snap.split(' ')[1]
    fecha = datetime.strptime(snapFecha, "%Y%m%d%H%M%S")
    snapShotsWebArchive[fecha.date()] = snapFecha

def obtener_palabras_clave():
    with open('datos_base/Terminos.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        terms_list = []
        for rows in reader:
            terms_list.extend(rows[0].split(","))
        return [term.strip().lower() for term in terms_list]

palabras_clave = obtener_palabras_clave()

for fecha, item in tqdm(snapShotsWebArchive.items(), desc="Obteniendo URLs", unit="fecha"):
    linkArticulo = f'https://web.archive.org/web/{item}/https://elpais.com/noticias/violencia-machista/'

    try:
        respuesta = requests.get(linkArticulo, timeout=100)
        if respuesta.status_code != 200:
            errores += 1
            snapError.append(f"{item}")
            continue
        rtaHtml = html.fromstring(respuesta.text)
    except Exception:
        errores += 1
        snapError.append(f"{item}")
        continue

    enlacesEncontrados = rtaHtml.xpath('//a')

    linksInteres = [
        element.get('href')
        for element in enlacesEncontrados
        if element.get('href') and any(p in element.text_content().lower() for p in palabras_clave)
    ]

    for link in linksInteres:
        link = link[20:]
        link = link[link.find('http'):]
        urlsArticulos[link.replace("http:", "https:")] = item

# Guardar logs
df = pd.DataFrame({'': [f"Fecha: {snap}, Artículo: {art}" for art, snap in urlsArticulos.items()]})
df.to_csv('log_ejecuciones/ELPAIS_ESP/archivoControl2020_2025_ESP.csv', index=False)

df2 = pd.DataFrame({'': snapError})
df2.to_csv('log_ejecuciones/ELPAIS_ESP/errores2020_2025_ESP.csv', index=False)

# Guardar enlaces a archivo
with open('log_ejecuciones/ELPAIS_ESP/urlsExtraidas.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['url', 'snapshot'])
    for art, snap in urlsArticulos.items():
        writer.writerow([art, snap])

print("Extracción completada.")
