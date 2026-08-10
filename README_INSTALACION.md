# Gibraltar Watch · Observatory vNext

Paquete aditivo para dar un salto de calidad sin borrar el trabajo actual.

## Cómo instalarlo

1. Descarga y descomprime el ZIP.
2. Copia **todo el contenido** de la carpeta sobre la raíz actual del repositorio `Gibraltar-Watch`.
3. Cuando se pregunte, acepta **reemplazar** `.github/workflows/update-gibraltar.yml`.
4. No borres los scripts antiguos: vNext está diseñado para ejecutarse **después** de ellos y conservar sus mejoras.
5. Haz un commit de todos los archivos.
6. En GitHub: **Actions → Actualizar Gibraltar Watch → Run workflow → main**.
7. La ejecución correcta termina con `Validar publicación completa antes del commit`, guarda los cambios y ejecuta IndexNow.

El primer ciclo crea automáticamente `observatory.json`, `health.json`, `timeline.json`, `observatory-history.json`, `observatory-feed.xml`, `publication-manifest.json` y `newsletter/latest.*`.

## Qué no debes hacer

- No vuelvas a añadir `continue-on-error: true` al paso de IndexNow.
- No cambies `submit_gibraltar_indexnow.py` por un nombre abreviado.
- No edites manualmente los bloques marcados `GWO_*`: el instalador los mantiene de forma idempotente.
- No publiques una señal del detector de anomalías como prueba de crisis. Son indicadores estadísticos para revisión.

## Comprobación posterior

Tras el primer workflow, comprueba estas rutas:

- `/situacion-actual.html`
- `/datos.html`
- `/mapa-estrategico.html`
- `/transparencia.html`
- `/correcciones.html`
- `/boletin.html`
- `/observatory.json`
- `/health.json`

También aparecerá una acción independiente **Auditar Gibraltar Watch** que comprueba diariamente la web publicada y abre/cierra un Issue si detecta un fallo.
