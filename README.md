# Gibraltar Watch

Observatorio bilingüe y estático del Estrecho de Gibraltar.

## Qué incluye

- Respuesta rigurosa a “¿se está cerrando el Estrecho?”.
- Panel sísmico automático mediante la API oficial del USGS.
- Mapa Leaflet de terremotos y serie histórica diaria.
- Radar AIS de MarineTraffic cargado bajo demanda.
- Explicación tectónica, oceanográfica y geológica.
- Estado documental del proyecto de túnel España–Marruecos.
- Páginas en español e inglés, sitemap, RSS, datos estructurados e IndexNow.

## Repositorio recomendado

Crea un repositorio público con el nombre exacto:

`estrecho-de-gibraltar`

La URL prevista es:

`https://elptowalter.github.io/estrecho-de-gibraltar/`

## Instalación

1. Sube todo el contenido a la raíz del repositorio, incluida `.github`.
2. En Settings → Pages selecciona `Deploy from a branch`, rama `main`, carpeta `/(root)`.
3. En Actions ejecuta `Actualizar Gibraltar Watch` una vez.
4. Espera al despliegue y recarga la web.

## Fuentes automáticas

El script `update_gibraltar.py` consulta el servicio FDSN del USGS en el área 34–38° N y 8–1,5° O, con magnitud mínima 1,0. Si la consulta falla, conserva el último resultado válido y registra el intento.

## Avisos

- La convergencia de 4,5 ± 1 mm/año es regional; no es una tasa de estrechamiento directo.
- El radar AIS es visual y no alimenta automáticamente ninguna inferencia de cierre.
- Los datos sísmicos no predicen terremotos.
- El proyecto de túnel está en fase de estudios, no de construcción.
