# 14MBID-Trabajo de Fin de Master

Explicación de los elementos almacenados en el repositorio:
articulos_x_procesar: contiene 1025 artículos producto de la extracción con el proceso de web scraping (webScraping.py).
datos_base: contiene un archivo CSV usado en el Procesamiento de Lenguaje Natural (estructurar_data.py) para determinar si las localizaciones detectadas con Spacy son un municipio o departamento.
Georreferenciación: es un reporte en Power BI usando los datos estandarizados de los artículos (noticias_estandarizadas.json).
chromedriver.exe: es el controlador de versión 129.0.6668.58 usado en el proceso de web scraping (webScraping.py) con Selenium para la versión de Google Chrome 128.0.6668.59.
estadisticas.ipynb: cuaderno en el que se realizó el análisis exploratorio de la información extraída de los artículos (noticias_estandarizadas.json).
estructurar_data.py: código Python desarrollado para hacer extracción de información de los artículos (articulos_x_procesar) a través de Procesamiento de Lenguaje Natural.
noticias_estandarizadas.json: archivo en formato JSON con los datos extraídos producto del Procesamiento de Lenguaje Natural (estructurar_data.py).
webScraping.py: código Python para hacer la extracción de los artículos de la biblioteca web Internet Archive (Wayback Machine).
