#librerias
from datetime import datetime
from lxml import html
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm  # Importar tqdm para la barra de progreso

import os
import pandas as pd
import requests
import time

urlsArticulos = {}
urlsArticulosV1 = {}
errores = 0
snapError = []

# Verificar si el directorio 'articulos_x_procesar' existe, si no, crearlo
if not os.path.exists('articulos_x_procesar'):
    os.makedirs('articulos_x_procesar')

# Verificar si el directorio 'log_ejecuciones' existe, si no, crearlo
if not os.path.exists('log_ejecuciones'):
    os.makedirs('log_ejecuciones')
    
origen = "ElPais"

# Invocar el servicio webArchive para obtener los resultados del historico
url="https://web.archive.org/cdx/search/cdx"
parametros = {'url': 'www.elpais.com', 'from': '20200214', 'to': '20250314' }

headers = {'Accept': '*/*'}

rtaWebArchive = ''
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


start_time = datetime.now()
# Extracción y almacenamiento de datos de cada página

for fecha, item in tqdm(snapShotsWebArchive.items(), desc="Obteniendo URLs", unit="fecha"):
                
        rtaHtmlSeccionJusticia = ''
        linkArticulo = 'https://web.archive.org/web/' + item + '/https://elpais.com/noticias/violencia-machista/'

        try:
            respuesta = requests.get(linkArticulo, timeout=100)

            if respuesta.status_code == 200:
                rtaHtmlSeccionJusticia = html.fromstring(respuesta.text)
            else:
                errores += 1
                snapError.append(f"item: {item}")
                print(f"item Error: {item}")
                continue

        except requests.exceptions.RequestException as e:
            errores += 1
            snapError.append(f"item: {item}")
            print(f"item Error: {item}")
            time.sleep(30)
            continue
        
        # Obtener todos los links de la sección
        enlacesEncontrados = rtaHtmlSeccionJusticia.xpath('//a')

        palabras_clave = ["viol", "machismo", "femini", "matar","descuartizar", "asesin",
                        "abandonar", "agredir","mata"]

        linksInteres = [
            element.get('href') 
            for element in enlacesEncontrados 
            if element.get('href') and any(palabra in element.text_content().lower() for palabra in palabras_clave)
        ]

        # Referencias de las páginas 
        for link in linksInteres:
            link = link[20:]
            link = link[link.find('http'):]

            urlsArticulos[link.replace("http:", "https:")] = item
           
archivoControl = []
for articulo, snap in urlsArticulos.items():
    archivoControl.append(f"Fecha: {snap}, Artículo: {articulo}")

df = pd.DataFrame({'':archivoControl})
df.to_csv('log_ejecuciones/archivoControl2020_2025_v2.csv', index=False)


df2 = pd.DataFrame({'':snapError})
df2.to_csv('log_ejecuciones/errores2020_2025_v2.csv', index=False)

end_time = datetime.now()
print('Duration Extraccion Urls: {}'.format(end_time - start_time))

# Inicializa webDriver Chrome 
options = webdriver.ChromeOptions()
options.add_argument('--disable-extensions')
options.add_argument('--blink-settings=imagesEnabled=false')

s = Service(os.path.dirname(os.path.abspath(__file__)) + '/chromedriver.exe')
driver = webdriver.Chrome(options= options, service = s)
count = 0
articuloError = []

for articulo, snap in urlsArticulos.items():
    linkArticulo = 'https://web.archive.org/web/' + snap +'/'+ articulo
    try:
        # Link de la página
        driver.get(linkArticulo)
        time.sleep(5)
    except TimeoutException:
        pass
    
    # definicion variables de trabajo
    titulo = "NONE"
    subtitulo = "NONE"
    contenido = "NONE"
    articulo = []

    try:
        titulo = (driver.find_element(By.TAG_NAME, "h1")).text
        if titulo == "" :
            el_titulo = driver.find_elements(By.TAG_NAME, "h1")
            if len(el_titulo) > 1 :
                titulo = driver.find_elements(By.TAG_NAME, "h1")[1].text
    except NoSuchElementException:
        subtitulo = (driver.find_element(By.TAG_NAME, "h2")).text

    articuloContenido = (driver.find_elements(By.CLASS_NAME, "articulo-contenido"))
    
    if articuloContenido:
        contenido = articuloContenido[0].find_elements(By.CLASS_NAME, "contenido")
    else :
        contenido = (driver.find_elements(By.CLASS_NAME, "paragraph"))
        
    if  (titulo != '' and titulo != 'NONE') and subtitulo != "Hrm.":
        # construcción listado con los elementos encontrados
        articulo.append(titulo)
        articulo.append(subtitulo)
            
        for itemContenido in contenido:
            textoXlineas = itemContenido.text.strip().split('\n')
            for texto in textoXlineas:
                if texto and not texto.startswith('-') and (not texto.startswith('(') and not texto.endswith(')')):
                    articulo.append(texto)
        
        # exportar datos a .csv
        df = pd.DataFrame({linkArticulo:articulo})
        df.to_csv('articulos_x_procesar/%s_%s_%i.csv' % (origen, snap, count), index=False)
        count += 1
    else :
        articuloError.append(linkArticulo)
    
driver.quit()

if articuloError :
    df3 = pd.DataFrame({'':articuloError})
    df3.to_csv('log_ejecuciones/articulosError_2020_2025.csv', index=False)
