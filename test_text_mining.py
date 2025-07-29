from text_mining_pipeline import TextMiningPipeline

# Crear instancia con fechas de solo 1 día (para limitar la prueba)
pipeline = TextMiningPipeline(
    sitio="elpais.com/noticias/violencia-machista",
    origen="PRUEBA_ELPAIS",
    from_date="20200214",
    to_date="20250717",
    palabras_clave_path="datos_base/Terminos.csv"
)

# Ejecutar la tubería paso a paso (esto tomará unos minutos)
pipeline.obtener_snapshots()
pipeline.filtrar_urls_relevantes()
pipeline.procesar_articulos()
