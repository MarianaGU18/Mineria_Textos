import pandas as pd
import sys
import os
import re
import json
import csv
import tldextract
import spacy 
from datetime import datetime
import pycountry
from datetime import datetime

from datetime import datetime
import re
# Variables de ruta
ruta_DATA_ESP = "datos_base/DATA_ESP/data_ESP.csv"
directorio_trabajo = "articulos_x_procesar/ELPAIS_ESP"
origen = "ElPais"


###############################################################
#Expresiones regulares de fecha
# Formato 12 de septiembre de|del 2023
regex_formato_textual = r'\b\d{1,2}\sde\s(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s(?:de|del)\s\d{4}\b'
# Formato Septiembre 12, 2023 o Sept 12, 2023
regex_mes_antes = r'\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s\d{1,2},?\s\d{4}\b'
# Formato dd/mm/yyyy o dd-mm-yyyy
regex_formato_numerico = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
# Formato yyyy-mm-dd o yyyy/mm/dd
regex_formato_iso = r'\b\d{2,4}[-/]\d{1,2}[-/]\d{1,2}\b'
# Combinar todas las expresiones regulares en una lista
regex_fechas = [regex_formato_textual, regex_mes_antes, regex_formato_numerico, regex_formato_iso]

# Diccionario para convertir meses en español a números
meses = {
    'enero': 1, 'ene': 1, 'febrero': 2, 'feb': 2,
    'marzo': 3, 'mar': 3, 'abril': 4, 'abr': 4,
    'mayo': 5, 'may': 5, 'junio': 6, 'jun': 6, 
    'julio': 7, 'jul': 7, 'agosto': 8, 'ago': 8,
    'septiembre': 9, 'sep': 9, 'octubre': 10, 'oct': 10, 
    'noviembre': 11, 'nov': 11, 'diciembre': 12, 'dic': 12
}

def convertir_a_fecha(fecha_str):
    for expresion in regex_fechas:
        coincidencia = re.search(expresion, fecha_str)
        
        if coincidencia:
            try:
                if expresion == regex_fechas[0]:  # "5 de diciembre de 2016"
                    dia = int(re.search(r'\d{1,2}', coincidencia.group()).group())
                    mes_texto = re.search(r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)', coincidencia.group(), re.IGNORECASE).group().lower()
                    anio = int(re.search(r'\d{4}', coincidencia.group()).group())
                    mes = meses.get(mes_texto, 0)

                elif expresion == regex_fechas[1]:  # "diciembre 5, 2016"
                    mes_texto = re.search(r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)', coincidencia.group(), re.IGNORECASE).group().lower()
                    dia = int(re.search(r'\d{1,2}', coincidencia.group()).group())
                    anio = int(re.search(r'\d{4}', coincidencia.group()).group())
                    mes = meses.get(mes_texto, 0)

                elif expresion in [regex_fechas[2], regex_fechas[3]]:  # formatos tipo 05/12/16 o 2016/12/05
                    partes = list(map(int, re.split(r'[-/]', coincidencia.group())))
                    
                    posibles_fechas = []
                    # Intentar combinaciones de día-mes-año
                    for orden in [(0, 1, 2), (2, 1, 0), (1, 0, 2)]:
                        try:
                            d, m, y = partes[orden[0]], partes[orden[1]], partes[orden[2]]
                            if y < 100:
                                y += 2000
                            if 1 <= m <= 12 and 1 <= d <= 31:
                                posibles_fechas.append(datetime(y, m, d).date().isoformat())
                        except:
                            continue
                    
                    if posibles_fechas:
                        fecha_obj = datetime.strptime(posibles_fechas[0], "%Y-%m-%d")
                        return fecha_obj.strftime('%d/%m/%Y')

                        #return posibles_fechas[0]
                    else:
                        print(f"[ERROR] Formato ambiguo no reconocido en '{fecha_str}'")
                        return None

                # Validaciones comunes
                if anio < 100:
                    anio += 2000

                if not (1 <= mes <= 12):
                    print(f"[ERROR] Mes fuera de rango: {mes} en '{fecha_str}'")
                    return None
                if not (1 <= dia <= 31):
                    print(f"[ERROR] Día fuera de rango: {dia} en '{fecha_str}'")
                    return None

                #fecha = datetime(anio, mes, dia)
                #return fecha.date().isoformat()

                fecha = datetime(anio, mes, dia)
                return fecha.strftime('%d/%m/%Y')

            except Exception as e:
                print(f"[ERROR] Problema al convertir '{fecha_str}': {e}")
                return None

    return None

# Expresiones regulares para detectar delitos y variaciones
def obtener_palabras_clave():
    with open('datos_base/Terminos.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        terms_list = []
        for rows in reader:
            terms_list.extend(rows[0].split(","))
        # Convertimos a diccionario
        return {term.strip().lower(): re.escape(term.strip().lower()) for term in terms_list}

patrones_delitos = obtener_palabras_clave()

# Función para normalizar delitos a una forma estándar
def normalizar_delito(texto_delito):
    texto_delito_lower = texto_delito.lower()  # Convertir el texto a minúsculas
    delitos_detectados = []

    # Iterar sobre el diccionario de patrones
    for delito, patron in patrones_delitos.items():
        if re.match(patron, texto_delito_lower):
            delitos_detectados.append(delito)  # Agregar el delito normalizado a la lista
            #return delito

    if delitos_detectados:
        return ', '.join(delitos_detectados)  # Retornar los delitos normalizados como una cadena separada por comas
    else:
        # Si no coincide con ninguno, retornar el texto original
        return texto_delito
 
###############################################################################
# Validaciones
if not os.path.isfile(ruta_DATA_ESP):
    print(f"El archivo {ruta_DATA_ESP} no existe.")
    os.makedirs(ruta_DATA_ESP)
    sys.exit(1)

# Cargar la lista de municipios y departamentos desde un archivo CSV

df_depmun = pd.read_csv(ruta_DATA_ESP)

# Validaciones
if not os.path.isdir(directorio_trabajo):
    print(f"El directorio {directorio_trabajo} no existe.")
    sys.exit(1)

# Crear conjuntos para buscar más rápido
municipios = set(df_depmun['MUNICIPIO'].str.lower())
comunidades = set(df_depmun['COMUNIDAD'].str.lower())
provincias = set(df_depmun['PROVINCIA'].str.lower())
# Crear listado de paises
paises = {country.name.lower() for country in pycountry.countries}

paises.add("españa")  
paises.add("espana")  
paises.add("méxico")  
paises.add("turquía")  
paises.add("brasil")  
paises.add("islandia")  
paises.add("EUA")  


def verificar_localizacion(localizacion):

    localizacion_lower = localizacion.lower()
        
    if localizacion_lower in municipios:
        return "MUNICIPIO"
    elif localizacion_lower in comunidad:
        return "COMUNIDAD"
    else:
        return "No encontrado"

def obtener_comunidad(municipio):
    # Filtrar la fila correspondiente al municipio
    resultado = df_depmun[df_depmun['MUNICIPIO'].str.lower() == municipio.lower()]
    
    # Verificar si se encontró el municipio
    if not resultado.empty:
        # Retornar el departamento asociado al municipio
        return resultado.iloc[0]['COMUNIDAD']
    else:
        # Si no se encuentra el municipio, retornar un mensaje
        return f"Sin especificar"


# Función para detectar país desde la URL
def detectar_pais(url):
    ext = tldextract.extract(url)
    dominio = ext.domain.lower()
    subdominio = ext.subdomain.lower()
    path = url.lower()

    for pais in paises:
        if pais in dominio or pais in subdominio or pais in path:
            #print(f"{url} → País detectado: {pais.title()}")
            return pais.title()


def obtener_una_url(archivo,directorio_trabajo):
        
    if archivo.endswith(".csv"):
        ruta_archivo = os.path.join(directorio_trabajo, archivo)
        df = pd.read_csv(ruta_archivo, header=None)
        if not df.empty:
            url = df.iloc[0, 0]
            return url  # Sale al encontrar la primera URL
    return None  # Si no se encuentra ninguna

nlp = spacy.load("es_core_news_lg")  # Modelo para español
palabrasExcluir = nlp.Defaults.stop_words #listado de stopwords de spacy usado para filtros posteriores
palabrasExcluir.add("el pais")

lstEventos = []
df = pd.DataFrame()

# Directorio de trabajo
os.chdir(directorio_trabajo)
files_csv = os.listdir()
nlp = spacy.load("es_core_news_lg")  # Modelo para español
palabrasExcluir = nlp.Defaults.stop_words #listado de stopwords de spacy usado para filtros posteriores
palabrasExcluir.add("el pais")

for idx, i in enumerate(files_csv, 1): 
    
    #Se inicializa el diccionario
    evento = {}
    # Formación del data frame a través de la lectura del archivo
    df = pd.read_csv(i)
    # Contenido del campo texto del data frame
    df_text = df.to_string()
    
    ####### ID del evento
    evento["ID_noticia"] = f"ESP{idx:03}"

    '''    
    # Agregar el titulo del articulo
    #tituloarticulo = df_text.split('\n')[1][1:].strip()
    #evento["tituloarticulo"] = tituloarticulo
    
    #Tokenizacion de titulos
    #doc_titulo = nlp(tituloarticulo)
    #evento["tokenizaciontitulo"] = [token.text for token in doc_titulo if not token.is_stop and not token.is_punct]   
    '''
    # Agregar fecha del articulo
    fechaarticulo = datetime.strptime(i.split('_')[1], '%Y%m%d%H%M%S').strftime('%d/%m/%Y')
    evento["fechaarticulo"] = fechaarticulo

    # Buscar fechas en el texto usando expresiones regulares
    fechas = []
    for regex in regex_fechas:
        fechas.extend(re.findall(regex, df_text.lower()))
    
    #Conversion de fechas de texto a tipo date
    fechas_sinduplicados = list(set(fechas))
    fechas_date = []
    for fecha in fechas_sinduplicados:
        fecha_formato = convertir_a_fecha(fecha)
        fechas_date.append(fecha_formato)

    # Obtener la menor fecha y adicionarla al diccionario de eventos de asesinatos si existen fechas
    fecha_menor = ''
    if len(fechas_date) > 0:
        fecha_menor = min(fechas_date)
        
    evento["diario"] = origen    

    #Buscar otros delitos expuestos usando expresiones regulares y adicionando los resultados a las entidades de Spacy
    # Procesar el texto con SpaCy
    doc = nlp(df_text)
    # Filtrar las entidades para mantener solo 'LOC' y 'PER'
    ents_filtradas = [ent for ent in doc.ents if ent.label_ in ["LOC", "PER"]]
    delitos_encontrados = []

    for delito, patron in patrones_delitos.items():
        # Buscar todas las coincidencias del patrón de delito
        for match in re.finditer(patron, df_text.lower()):
            start, end = match.span()  # Obtener el inicio y fin de la coincidencia
            delitos_encontrados.append((start, end, delito))
 
    # Verificar superposición de entidades antes de agregar las nuevas entidades de tipo DELITO
    for start, end, delito in delitos_encontrados:
        span = doc.char_span(start, end, label="DELITO")
        
        # Asegurarse de que el span no es None y no se solape con otras entidades
        if span is not None:
            overlapping = False
            for ent in doc.ents:
                # Verifica si los spans se solapan
                if ent.start < span.end and span.start < ent.end:
                    overlapping = True
                    break
            if not overlapping:
                ents_filtradas.append(span)

    # Actualizar las entidades del documento con las nuevas entidades detectadas y filtradas
   
    doc.ents = ents_filtradas
   
    municipio = ""
    comunidad = ""
    departamento = ""
    delitos_relacionados = []
    paises_detectados = []

    conteo_delitos  = {}  

    directorio_trabajo = os.getcwd()
    # Obtener la URL del archivo CSV   

    for ent in doc.ents:
        
        url= obtener_una_url(i,directorio_trabajo)
        pais= detectar_pais(url)
        paises_detectados.append(pais)
    
        if ent.label_ == "DELITO":
            delito_normalizado = normalizar_delito(ent.text)

            if delito_normalizado not in conteo_delitos:
                conteo_delitos[delito_normalizado] = 1
            else:
                conteo_delitos[delito_normalizado] += 1


        if ent.label_ == "LOC": # Verificar cada localización detectada

            tipo = verificar_localizacion(ent.text)
   
            if tipo == "MUNICIPIO": 

                municipio = ent.text
                comunidad = obtener_comunidad(municipio)
                
            elif tipo == "COMUNIDAD" :
                municipio = "Sin especificar"
                comunidad = ent.text
       
    evento["pais"] = "España" if pais in ["Espana", "España"] else "Otro Pais"
    evento["delitos_relacionados"] = conteo_delitos if conteo_delitos else "Sin especificar"
    #evento["ubicacion_noticia"] = {comunidad}, {municipio}
    evento["ubicacion_noticia"] = f"{comunidad}, {municipio}" if departamento and municipio else "Sin especificar"

    lstEventos.append(evento)

#print(lstEventos)

#################################################################################################
# Escribir los datos al archivo JSON

directorio = "./TFM"

if not os.path.exists(directorio):
    os.makedirs(directorio)

with open(f"{directorio}/noticias_estandarizadas_ESP.json", "w", encoding="utf-8") as archivo:
    json.dump(lstEventos, archivo, ensure_ascii=False, indent=4)
