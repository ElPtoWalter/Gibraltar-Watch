# Diario del Estrecho v2

- Motor híbrido **artículo completo / parte breve** según una puntuación de relevancia auditable.
- Umbral editorial calculado antes de cualquier redacción con modelo.
- Selección de hasta 9 señales recientes, con deduplicado, máximo por categoría y máximo por dominio.
- Solo URLs HTTP/HTTPS trazables.
- Redacción opcional mediante OpenAI con salida estructurada y paquete factual cerrado.
- Fallback local automático: el diario no depende de una API de pago.
- Partes sin señales nuevas: `noindex` y fuera del sitemap para evitar páginas SEO vacías.
- Portada estática: retirada de la dependencia de `diario-latest.json` + `diario.js`.
- Hemeroteca, RSS, sitemap y navegación anterior/archivo/siguiente actualizados automáticamente.
- Migración de la hemeroteca v1 a `.github/diario-state.json`.
- Transparencia editorial pública sin exponer prompts, modelos ni detalles internos.
- 13 pruebas unitarias superadas antes del empaquetado.
