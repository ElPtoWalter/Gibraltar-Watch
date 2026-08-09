# Diario del Estrecho · v1.0

- Generación automática de una edición diaria, como máximo una por fecha local de Madrid.
- Hora objetivo: primera ejecución del workflow a partir de las 06:00 Europe/Madrid.
- Selección de noticias por relevancia, recencia, diversidad de categorías y fiabilidad de fuente.
- Integración de estado marítimo, presión fronteriza, relación España–Marruecos, seguridad y OPE.
- Crónica larga solo cuando hay señal suficiente y varias fuentes; parte breve con `noindex` en jornadas pobres.
- Hemeroteca automática en `/diario/`.
- RSS propio en `/diario/feed.xml`.
- Actualización automática de portada y sitemap.
- Redacción gratuita mediante reglas editoriales.
- Redacción IA opcional mediante `OPENAI_API_KEY`, con fallback automático si falla.
- Guardrails editoriales: no inventar hechos, no atribuir intenciones, no convertir rumores en hechos y no inferir cierres marítimos sin confirmación.
- Instalador idempotente para menú, portada y pie de página.
