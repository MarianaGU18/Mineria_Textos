import pandas as pd
import sys
import os
import re
import json
import tldextract
import spacy 
from datetime import datetime
import pycountry
from datetime import datetime

from datetime import datetime
import re
# Variables de ruta
ruta_DATA_ESP = "datos_base/DATA_ESP/data_ESP.csv"
directorio_trabajo = "articulos_x_procesar/ELPAIS_ESP/"
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

###### Funcion convertir_a_fecha
'''
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
            return fecha.date().isoformat()
    
    return "No se encontró una fecha en un formato válido."
'''



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
                        return posibles_fechas[0]
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

                fecha = datetime(anio, mes, dia)
                return fecha.date().isoformat()

            except Exception as e:
                print(f"[ERROR] Problema al convertir '{fecha_str}': {e}")
                return None

    return None

# Expresiones regulares para detectar delitos y variaciones
patrones_delitos = {
    "secuestro": r"secuest\w+",
    "violación": r"viola\w+",
    "feminicidio": r"feminicid\w+",
    "robo": r"rob\w+",
    "asalto": r"asalt\w+",
    "hurto": r"hurt\w+",
    "descuartizar": r"descuarti\w+",
    "asesinato": r"asesin\w+",
    "matar": r"matar\w+",
    "agredir": r"agre\w+",
    "abandonar": r"abando\w+"
}

# Función para normalizar delitos a una forma estándar
def normalizar_delito(texto_delito):
    texto_delito_lower = texto_delito.lower()  # Convertir el texto a minúsculas

    # Iterar sobre el diccionario de patrones
    for delito, patron in patrones_delitos.items():
        if re.match(patron, texto_delito_lower):
            return delito

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
departamentos = set(df_depmun['COMUNIDAD'].str.lower())

# Crear listado de paises
paises = {country.name.lower() for country in pycountry.countries}

paises.add("españa")  # Agregar "España" a la lista de países
paises.add("España")  # Agregar "España" a la lista de países
paises.add("espana")  # Agregar "España" a la lista de países
paises.add("Espana")  # Agregar "España" a la lista de países
paises.add("spain")  # Agregar "Spain" a la lista de países 

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

    #print(f"{url} → País no encontrado")
    return "País no encontrado"

def obtener_una_url(archivo,carpeta_csv):
        
    if archivo.endswith(".csv"):
        ruta_archivo = os.path.join(carpeta_csv, archivo)
        df = pd.read_csv(ruta_archivo, header=None)
        if not df.empty:
            url = df.iloc[0, 0]
            return url  # Sale al encontrar la primera URL
    return None  # Si no se encuentra ninguna

#Funcion para normalizar delitos a un solo nombre donde la base de las expresiones regulares se mantengan
#Función para verificar si una localización es un municipio o un departamento

def verificar_localizacion(localizacion):
    localizacion_lower = localizacion.lower()
    if localizacion_lower in municipios:
        return "MUNICIPIO"
    elif localizacion_lower in departamentos:
        return "COMUNIDAD"
    else:
        return "No encontrado"

# Función para retornar el departamento de un municipio
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



nlp = spacy.load("es_core_news_lg")  # Modelo para español
palabrasExcluir = nlp.Defaults.stop_words #listado de stopwords de spacy usado para filtros posteriores
palabrasExcluir.add("el pais")

lstEventos = []
df = pd.DataFrame()
'''
for archivo in os.listdir(directorio_trabajo):

    url= obtener_una_url(archivo,directorio_trabajo)
    pais= detectar_pais(url)

    evento = {}
    ####### ID del evento
    evento["id"] = "ESP"+ archivo.split('_')[1] 
    evento["diario"] = origen
    fechaarticulo = datetime.strptime(archivo.split('_')[1], '%d%m%Y%H%M%S').date().isoformat()
    evento["fechaarticulo"] = fechaarticulo 
    evento["pais"] = pais
    #evento["ubicación_noticia"] = 

    lstEventos.append(evento)

    print(lstEventos)

    municipio = ""
    comunidad = ""
    paisEncontrado = ""
    delitos_relacionados = []
    personas_involucradas = []

    doc.ents = ents_filtradas


    for ent in doc.ents:
        if ent.label_ == "DELITO":
            delito_normalizado = normalizar_delito(ent.text)
            delitos_relacionados.append(delito_normalizado)
        elif ent.label_ == "LOC": # Verificar cada localización detectada
            tipo = verificar_localizacion(ent.text)
            if tipo == "Municipio" and municipio == "": #Tomar como ubicacion del evento el primer municipio o departamento mencionado en el texto
                municipio = ent.text
                departamento = obtener_comunidad(municipio)
            elif tipo == "Comunidad" and departamento == "":
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
        evento["pais"] = "España" if paisEncontrado == "España" or comunidad != "" else "Otros Paises"
    else:
        evento["pais"] = "Pais no especificado"


    if comunidad != "":
        evento["pais"] = "España"
        evento["comunidad"] = comunidad
        evento["municipio"] = municipio
    else:
        evento["pais"] = "Pais no especificado"
        evento["comunidad"] = "comunidad no especificado"
        evento["municipio"] = "municipio no especificado"
'''

# Directorio de trabajo
os.chdir(directorio_trabajo)
files_csv = os.listdir()
nlp = spacy.load("es_core_news_lg")  # Modelo para español
palabrasExcluir = nlp.Defaults.stop_words #listado de stopwords de spacy usado para filtros posteriores
palabrasExcluir.add("el pais")


lstEventos = []
df = pd.DataFrame()
coun = 0


for idx, i in enumerate(files_csv, 1): 
    print(i)
    #Se inicializa el diccionario
    evento = {}
    # Formación del data frame a través de la lectura del archivo
    df = pd.read_csv(i)
    # Contenido del campo texto del data frame
    df_text = df.to_string()
    

    ####### ID del evento
    evento["ID_noticia"] = f"ESP{idx:03}"

    ###############################################################
    # Agregar el titulo del articulo
    tituloarticulo = df_text.split('\n')[1][1:].strip()
    evento["tituloarticulo"] = tituloarticulo
    
    #Tokenizacion de titulos
    doc_titulo = nlp(tituloarticulo)
    #evento["tokenizaciontitulo"] = [token.text for token in doc_titulo if not token.is_stop and not token.is_punct]   
    
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
        #evento["fechaestimada"] = fecha_menor
    else:
        evento["fechaestimada"] = fechaarticulo 
    
    ############
    evento["diario"] = origen    

    ###############################################################
    #Buscar otros delitos expuestos usando expresiones regulares y adicionando los resultados a las entidades de Spacy
    # Procesar el texto con SpaCy
    doc = nlp(df_text)
    # Filtrar las entidades para mantener solo 'LOC' y 'PER'
    '''ents_filtradas = [ent for ent in doc.ents if ent.label_ in ["LOC", "PER"]]
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
     '''
    municipio = ""
    comunidad = ""
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
                departamento = obtener_comunidad(municipio)
            elif tipo == "Comunidad" and departamento == "":
                municipio = "Sin especificar"
                departamento = ent.text
            elif ent.text in paises :
                #paisEncontrado = ent.text
                
                paisEncontrado = detectar_pais(ent.text)
        elif ent.label_ == "PER": # Verificar cada persona detectada
            persona_detectada = ent.text
            if persona_detectada not in personas_involucradas and persona_detectada.lower() not in palabrasExcluir and persona_detectada.find("http") == -1:
                personas_involucradas.append(persona_detectada)
        '''
        # Adicionar al diccionario de eventos de asesinatos los delitos relacionados si existen
        delitos_sinduplicados = list(set(delitos_relacionados))
        if len(delitos_sinduplicados) > 0:
            evento["delitos_relacionados"] = delitos_sinduplicados
        '''


    # Adicionar al diccionario de eventos la ubicacion del evento si existe

    if comunidad != "":
        evento["pais"] = "España"
        evento["comunidad"] = comunidad
        evento["municipio"] = municipio
    else:
        evento["pais"] = "Pais no especificado"
        evento["comunidad"] = "comunidad no especificado"
        evento["municipio"] = "municipio no especificado"
    
    # Adicionar al diccionario de eventos de asesinatos las personas relacionadas si existen
    
    lstEventos.append(evento)

'''
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
    
    lstEventos.append(evento)

'''
    ##################################################################################################

#################################################################################################
# Escribir los datos al archivo JSON

directorio = "./TFM"

if not os.path.exists(directorio):
    os.makedirs(directorio)

with open(f"{directorio}/noticias_estandarizadas_ESP.json", "w", encoding="utf-8") as archivo:
    json.dump(lstEventos, archivo, ensure_ascii=False, indent=4)
