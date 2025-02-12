

import datetime
from datetime import datetime
from lxml import html
from time import time
from urllib.parse import urljoin

import requests

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

'''
    Invoca el servicio web de WebArchive para obtener los historicos
'''
def webservice():
    url="https://web.archive.org/cdx/search/cdx"
    parametros = {'url': 'www.elpais.com', 'from': '20200228', 'to': '20200325' }
    headers = {'Accept': '*/*'}

    rtaWebArchive = ''
    try:
        respuesta = requests.get(url, params=parametros, timeout=100)

        if respuesta.status_code == 200:
            rtaWebArchive = respuesta.text
            return rtaWebArchive
        else:
            raise Exception(f"Error: Código de estado {respuesta.status_code}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"Error en la solicitud: {e}")

def procesar_texto(aux):
    lstSnapWebArchive = aux.strip().split('\n')
    return lstSnapWebArchive

def procesar_fechas(lstSnapWebArchive):
    snapShotsWebArchive = {}

    for snap in lstSnapWebArchive:
        snapFecha = snap.split(' ')[1]
        fecha = datetime.strptime(snapFecha, "%Y%m%d%H%M%S")
        snapShotsWebArchive[fecha.date()] = snapFecha
    
    return snapShotsWebArchive

def extraerdatos(snapShotsWebArchive):
    errores = 0    
    snapError = []
    urlsArticulos = {}

    keywords = ['violencia-machista', 'violencia-de-genero', 'feminicidio', 'feminis', 'machis', 'patriarca']

    for fecha,item in snapShotsWebArchive.items():
        
        print(f"Fecha: {fecha}, Último item: {item}")    
        rtaHtmlSeccionJusticia = ''

        linkArticulo = f'https://web.archive.org/web/{item}/https://elpais.com/noticias/violencia-machista'
        
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
            snapError.append(f"item: {item} - Error: {str(e)}")
            print(f"Error en el item: {item} - {str(e)}")
            time.sleep(5)  # Tiempo de espera en caso de error    
            continue
        

    # Extraer los enlaces que contienen palabras clave en su texto
        enlacesEncontrados = rtaHtmlSeccionJusticia.xpath('//a')
            
        linksInteres = filtrar_enlaces(enlacesEncontrados,keywords)

    # Añadir los enlaces encontrados al diccionario
        for link in linksInteres:
            link = link[20:]
            link = link[link.find('http'):]
            if link.find('www') > 0 :
                urlsArticulos[link.replace("http:", "https:")] = item

    return urlsArticulos, errores, snapError

def filtrar_enlaces(enlaces, keywords):
  linksInteres = [
        element.get('href') 
        for element in enlaces 
        if any(palabra in element.text_content().lower() for palabra in keywords)
    ]
  return linksInteres



def main():
    origin = "ELPAIS"
    snapShotsWebArchive = {}
    urlsArticulos = {}
    errores = 0    
    snapError = []
    archivoControl = []

    rtaWebArchive = webservice()
    lstSnapWebArchive = procesar_texto(rtaWebArchive)
    snapShotsWebArchive = procesar_fechas(lstSnapWebArchive)
    start_time = datetime.now()
    urlsArticulos, errores, snapError = extraerdatos(snapShotsWebArchive)
    
    
    for articulo, snap in urlsArticulos.items():
        archivoControl.append(f"Fecha: {snap}, Articulo: {articulo}")

    print("📊 Contenido archivoControl:", archivoControl)



    
   
   

if __name__ == "__main__":
    main()