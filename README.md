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

# Versión 2

Proyecto de minería de textos, centrado en el análisis de artículos sobre violencia machista del diario El País (España). Esta nueva versión está diseñada para ser modular, reutilizable y fácilmente adaptable a otras fuentes de noticias o países.

## 📂 Estructura del Proyecto

- **text_mining_pipeline.py** – Clase que gestiona la extracción de snapshots, filtrado de URLs y scraping de artículos.

- **test_text_mining.py** – Script de prueba para procesar datos de forma controlada por rango de fechas.

- **procesamiento_utils.py** – Utilidades compartidas para parseo de fechas, detección de ubicaciones y países, y coincidencias por palabras clave.

- **estructurar_data.py** – Script completo para procesar los artículos descargados, detectar fechas, delitos, ubicaciones y países, y generar la salida en JSON.

## ⚙️ Funcionalidades Principales

1. **Extracción de Snapshots y URLs** (`text_mining_pipeline.py`)

   - API de Wayback Machine
   - Filtro por palabras clave (`Terminos.csv`)
   - Logs de URLs válidas y fallidas

2. **Scraping de artículos** (`text_mining_pipeline.py`)

   - Selenium en modo `headless`
   - Extracción de: título, subtítulos, etiquetas, localización y cuerpo
   - Manejo robusto de errores

3. **Procesamiento NLP y estructuración** (`main.py`, `estructurar_data.py`)
   - Identificación de entidades con SpaCy (`LOC`, `PER`, `GPE`)
   - Detección de delitos con regex y normalización
   - Clasificación de ubicaciones: municipio, comunidad, provincia
   - Detección del país desde texto o URL
   - Salida JSON estandarizada

## 🧪 Pruebas

Usa test_text_mining.py para probar la tubería con un solo día o rango reducido.

## 🗃️ Dependencias
requests
lxml
pandas
selenium
spacy
pycountry
tldextract
tqdm
Modelo de SpaCy: es_core_news_lg

> [!IMPORTANT]
> Uno de los primeros problemas detectados fue el uso de ChromeDriver, ya que este varía según la versión del Chrome instalada. Esto se resolvió consultando la página oficial de descargas:
>
> 👉 https://developer.chrome.com/docs/chromedriver/downloads?hl=es-419
>
> Desde ahí se puede acceder a los endpoints JSON y ubicar la versión específica requerida según el Chrome instalado.
