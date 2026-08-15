# Diario del Estrecho v3 · Hotfix visual y de rutas

El fallo no era únicamente “falta de CSS”: coexistían dos arquitecturas de URL. La web pública usa `/diario/` y `/diario/AAAA-MM-DD.html`, mientras la versión anterior preparada en el parche generaba `diario.html` y `diario-AAAA-MM-DD.html` en la raíz.

Esta versión consolida una sola arquitectura:

- `/diario/` — hemeroteca canónica.
- `/diario/AAAA-MM-DD.html` — ediciones.
- `/diario.css` — hoja editorial cargada mediante ruta absoluta.
- `/diario.html` — compatibilidad mediante redirección a `/diario/`.

También normaliza navegación, canonical, RSS, sitemap y enlaces de portada para que una página dentro de `/diario/` nunca intente buscar `styles.css`, `trafico.html` o `fuentes.html` dentro de esa subcarpeta.
