"""
@author: Ingrid Rodriguez
"""
import pandas as pd
#import nltk
import os
import re
#from nltk.probability import FreqDist
#from nltk.corpus import stopwords
import json
import spacy 
#from spacy.tokens import Span
from datetime import datetime
import pycountry

###############################################################
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
###############################################################
# Diccionario para convertir meses en español a números
meses = {
    'enero': 1, 'ene': 1, 'febrero': 2, 'feb': 2,
    'marzo': 3, 'mar': 3, 'abril': 4, 'abr': 4,
    'mayo': 5, 'may': 5, 'junio': 6, 'jun': 6, 
    'julio': 7, 'jul': 7, 'agosto': 8, 'ago': 8,
    'septiembre': 9, 'sep': 9, 'octubre': 10, 'oct': 10, 
    'noviembre': 11, 'nov': 11, 'diciembre': 12, 'dic': 12
}
###############################################################
###### Funcion convertir_a_fecha
def convertir_a_fecha(fecha_str):
    # Probar con cada expresión regular
    for expresion in regex_fechas:
        coincidencia = re.search(expresion, fecha_str)
        
        if coincidencia:
            if expresion == regex_fechas[0]:  # Caso: "5 de diciembre de 2016"
                dia = int(re.search(r'\d{1,2}', coincidencia.group()).group())
                mes_texto = re.search(r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)', coincidencia.group()).group().lower()
                anio = int(re.search(r'\d{4}', coincidencia.group()).group())
                mes = meses[mes_texto]  # Convertir el mes en texto a número
            elif expresion == regex_fechas[1]:  # Caso: "diciembre 5, 2016" o "dic 5, 2016"
                mes_texto = re.search(r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)', coincidencia.group()).group().lower()
                dia = int(re.search(r'\d{1,2}', coincidencia.group()).group())
                anio = int(re.search(r'\d{4}', coincidencia.group()).group())
                mes = meses[mes_texto]
            elif expresion == regex_fechas[2]:  # Caso: "05/12/16", "12/05/2016", "05-12-16"
                partes = re.split('[-/]', coincidencia.group())
                dia = int(partes[0])
                mes = int(partes[1])
                anio = int(partes[2])
            elif expresion == regex_fechas[3]:  # Caso: "16/05/12", "2016/12/05", "16-05-12"
                partes = re.split('[-/]', coincidencia.group())
                anio = int(partes[2])
                mes = int(partes[1])
                dia = int(partes[0])
                
            # Manejar años con 2 dígitos (asumir 2000 si es menor a 100)
            if anio < 100:
                anio += 2000
            
            # Si día es mayor a 31 se asume error y se cambia a 01
            if dia > 31:
                dia = 1
            
            # Crear el objeto datetime
            fecha = datetime(anio, mes, dia)
            
            # Convertir al formato yyyymmdd
            # return fecha.strftime('%Y%m%d')
            return fecha.date().isoformat()
    
    return "No se encontró una fecha en un formato válido."
###############################################################
###############################################################
# Expresiones regulares para detectar delitos y variaciones
patrones_delitos = {
    "secuestro": r"secuest\w+",
    "violación": r"viola\w+",
    "feminicidio": r"feminicid\w+",
    "robo": r"rob\w+",
    "asalto": r"asalt\w+",
    "hurto": r"hurt\w+",
    "terrorismo": r"terroris\w+",
    "narcotráfico": r"narcotr\w+",
    "masacre": r"masacr\w+"
}
###### Funcion para normalizar delitos a un solo nombre donde la py --version base de las expresiones regulares se mantengan
# Función para normalizar delitos a una forma estándar
def normalizar_delito(texto_delito):
    if re.match(r"secuest\w+", texto_delito.lower()):
        return "secuestro"
    if re.match(r"viola\w+", texto_delito.lower()):
        return "violación"
    if re.match(r"feminici\w+", texto_delito.lower()): 
        return "feminicidio"
    if re.match(r"rob\w+", texto_delito.lower()):
        return "robo"
    if re.match(r"asalt\w+", texto_delito.lower()):
        return "robo"
    if re.match(r"hurt\w+", texto_delito.lower()):
        return "robo"
    if re.match(r"terroris\w+", texto_delito.lower()):
        return "terrorismo"
    if re.match(r"narcotr\w+", texto_delito.lower()):
        return "narcotráfico"
    if re.match(r"masacr\w+", texto_delito.lower()):
        return "masacre"
    
    return texto_delito
###############################################################
# Cargar la lista de municipios y departamentos desde un archivo CSV
df_depmun = pd.read_csv("datos_base/Departamentos_y_municipios_de_Colombia.csv")

# Crear conjuntos para buscar más rápido
municipios = set(df_depmun['MUNICIPIO'].str.lower())
departamentos = set(df_depmun['DEPARTAMENTO'].str.lower())

# Crear listado de paises
paises = {country.name for country in pycountry.countries}
###############################################################
###############################################################
###### Funcion para normalizar delitos a un solo nombre donde la base de las expresiones regulares se mantengan
# Función para verificar si una localización es un municipio o un departamento
def verificar_localizacion(localizacion):
    localizacion_lower = localizacion.lower()
    if localizacion_lower in municipios:
        return "Municipio"
    elif localizacion_lower in departamentos:
        return "Departamento"
    else:
        return "No encontrado"
###############################################################
###############################################################    
# Función para retornar el departamento de un municipio
def obtener_departamento(municipio):
    # Filtrar la fila correspondiente al municipio
    resultado = df_depmun[df_depmun['MUNICIPIO'].str.lower() == municipio.lower()]
    
    # Verificar si se encontró el municipio
    if not resultado.empty:
        # Retornar el departamento asociado al municipio
        return resultado.iloc[0]['DEPARTAMENTO']
    else:
        # Si no se encuentra el municipio, retornar un mensaje
        return f"Sin especificar"
###############################################################

indice = []
# Directorio de trabajo
os.chdir('articulos_x_procesar/')
files_csv = os.listdir()
nlp = spacy.load("es_core_news_lg")  # Modelo para español
palabrasExcluir = nlp.Defaults.stop_words #listado de stopwords de spacy usado para filtros posteriores
palabrasExcluir.add("el tiempo")

lstEventos = []
df = pd.DataFrame()
for i in files_csv:
    print(i)
    #Se inicializa el diccionario
    evento = {}
    # Formación del data frame a través de la lectura del archivo
    df = pd.read_csv(i)
    # Contenido del campo texto del data frame
    df_text = df.to_string()
    
    ###############################################################
    # Agregar el titulo del articulo
    tituloarticulo = df_text.split('\n')[1][1:].strip()
    evento["tituloarticulo"] = tituloarticulo
    
    #Tokenizacion de titulos
    doc_titulo = nlp(tituloarticulo)
    evento["tokenizaciontitulo"] = [token.text for token in doc_titulo if not token.is_stop and not token.is_punct]   
    
    ###############################################################
    # Agregar fecha del articulo
    fechaarticulo = datetime.strptime(i.split('_')[1], '%Y%m%d%H%M%S').date().isoformat()
    evento["fechaarticulo"] = fechaarticulo
    
    ###############################################################
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
        
    if fecha_menor :
        evento["fechaevento"] = fecha_menor
        evento["fechaestimada"] = fecha_menor
    else:
        evento["fechaestimada"] = fechaarticulo 
    
    ###############################################################
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
            # span = Span(doc, doc.char_span(start, end).start, doc.char_span(start, end).end, label="DELITO")
            # ents_filtradas.append(span)
    
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
    departamento = ""
    paisEncontrado = ""
    delitos_relacionados = []
    personas_involucradas = []
    for ent in doc.ents:
        if ent.label_ == "DELITO":
            delito_normalizado = normalizar_delito(ent.text)
            delitos_relacionados.append(delito_normalizado)
        elif ent.label_ == "LOC": # Verificar cada localización detectada
            tipo = verificar_localizacion(ent.text)
            if tipo == "Municipio" and municipio == "": #Tomar como ubicacion del evento el primer municipio o departamento mencionado en el texto
                municipio = ent.text
                departamento = obtener_departamento(municipio)
            elif tipo == "Departamento" and departamento == "":
                municipio = "Sin especificar"
                departamento = ent.text
            elif ent.text in paises :
                paisEncontrado = ent.text
        elif ent.label_ == "PER": # Verificar cada persona detectada
            persona_detectada = ent.text
            if persona_detectada not in personas_involucradas and persona_detectada.lower() not in palabrasExcluir and persona_detectada.find("http") == -1:
                personas_involucradas.append(persona_detectada)
    
    # Adicionar al diccionario de eventos de asesinatos los delitos relacionados si existen
    delitos_sinduplicados = list(set(delitos_relacionados))
    if len(delitos_sinduplicados) > 0:
        evento["delitos_relacionados"] = delitos_sinduplicados
    
    # Adicionar al diccionario de eventos la ubicacion del evento si existe
    if paisEncontrado != "":
        evento["pais"] = "Colombia" if paisEncontrado == "Colombia" or departamento != "" else "Otros Paises"

    if departamento != "":
        evento["pais"] = "Colombia"
        evento["departamento"] = departamento
        evento["municipio"] = municipio

    # Adicionar al diccionario de eventos de asesinatos las personas relacionadas si existen
    personas_involucradas_sinduplicados = list(set(personas_involucradas))
    personas_involucradas_sinduplicados.sort(key=len, reverse=True)
    personas_involucradas_procesado = []

    # Iteramos sobre cada persona en la lista ordenada
    for persona in personas_involucradas_sinduplicados:
        # Comprobamos si 'persona' no está contenida en ninguna de las ya añadidas a resultados_finales
        if not any(persona in personaB for personaB in personas_involucradas_procesado):
            personas_involucradas_procesado.append(persona)
    
    if len(personas_involucradas_procesado) > 0:
        evento["personas_involucradas"] = personas_involucradas_procesado
    ##################################################################################################
    lstEventos.append(evento)
    #print(evento)

#################################################################################################
# Escribir los datos al archivo JSON
with open("C:/Projects/TFM/noticias_estandarizadas.json", "w", encoding="utf-8") as archivo:
    json.dump(lstEventos, archivo, ensure_ascii=False, indent=4)