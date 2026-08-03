# Gibraltar Watch · consolidación final

## Arquitectura
- Portada reducida de 14 bloques a una secuencia editorial de 9 secciones.
- Eliminación de duplicaciones entre la narrativa geológica antigua y el observatorio estratégico.
- Menú agrupado: Geopolítica y Territorio y futuro.
- Pie común para todo el sitio.

## Portada
- Hero: tráfico, economía y poder.
- Panel con tráfico, frontera, relación bilateral y seguridad.
- Actualidad con hechos verificados y lectura prudente.
- Economía: Algeciras, Tánger Med, comercio UE–Marruecos y OPE.
- Ceuta/Melilla y España–Marruecos como pilares propios.
- Mapa conceptual de control distribuido.
- Análisis, escenarios y territorio/futuro.

## Diseño
- Sin alturas fijas en los bloques críticos.
- `min-width: 0`, `overflow-wrap` y tipografía fluida para evitar solapamientos.
- Rejillas adaptadas a 4, 2 y 1 columna.
- Menú móvil probado y accesible.
- Soporte para `prefers-reduced-motion`.

## Ingeniería
- Instalador idempotente ejecutado al final del workflow.
- Carga dinámica desde geopolitics.json, ope-2026.json y seismicity.json.
- Sitemap XML reconstruido de forma válida.
- Pruebas de idempotencia, IDs únicos, enlaces locales y sintaxis JavaScript.
