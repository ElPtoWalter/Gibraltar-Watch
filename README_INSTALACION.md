# Instalación · Professional Security v3

1. Copia todo el contenido del paquete en la raíz de `Gibraltar-Watch` y acepta reemplazar archivos.
2. Haz commit en `main`.
3. En GitHub ve a **Settings → Pages → Build and deployment → Source → GitHub Actions**.
4. Ejecuta manualmente **Actions → Desplegar Gibraltar Watch seguro → Run workflow → main**.
5. Cuando el despliegue sea correcto, comprueba que `https://estrechogibraltar.com/observatory.json` devuelve 404, mientras la web sigue funcionando.
6. Si tu plan de GitHub permite Pages desde repositorios privados, cambia después el repositorio a **Private**. No lo hagas antes de confirmar que tu plan lo permite.
7. Si utilizas Cloudflare como proxy, despliega `cloudflare/security-worker.js` sobre la ruta `estrechogibraltar.com/*` para añadir una segunda barrera a rutas técnicas y cabeceras HTTP.

## Resultado esperado

- La web continúa siendo pública.
- El repositorio puede quedar privado.
- El backend, scripts, tests y workflows no forman parte del artefacto público.
- Los `.json` no se publican como URLs directas.
- La web no muestra referencias a IA/OpenAI/modelos/GitHub Actions.
