# Cambios · Professional Security v3

## Identidad editorial
- La atribución pública pasa a **Redacción de Gibraltar Watch** y **criterios editoriales de Gibraltar Watch**.
- Se eliminan de las páginas públicas las referencias a motores, modelos, OpenAI, GitHub Actions y autoría automatizada.
- El Diario se sanea después de cada nueva edición para evitar que el generador vuelva a introducir texto técnico.
- Transparencia y metodología explican fuentes, criterios, frescura, correcciones y controles sin publicar detalles de implementación.

## Separación fuente / publicación
- Nuevo build `_site` con lista de exclusión estricta.
- No se publican `.py`, `.yml`, `.yaml`, `.md`, tests, workflows, ZIP, logs, source maps ni JSON independientes.
- Los datos necesarios para la interfaz se encapsulan en un runtime en memoria para mantener compatibilidad con el JavaScript existente.
- Los endpoints `.json` dejan de existir en el artefacto público.

## Seguridad
- Auditoría de posibles secretos antes del commit y antes del despliegue.
- Auditoría del artefacto público: falla si detecta backend, JSON, source maps, rutas o textos técnicos no permitidos.
- Despliegue por artefacto de GitHub Pages separado del repositorio fuente.
- Worker de Cloudflare incluido para bloquear rutas técnicas y añadir cabeceras de seguridad HTTP.
- `.gitignore` reforzado.
- Auditoría externa adaptada a la nueva arquitectura: verifica que las rutas técnicas ya no respondan con 200.
