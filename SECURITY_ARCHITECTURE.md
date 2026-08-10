# Gibraltar Watch · publicación profesional y endurecida

## Qué consigue esta versión

- Elimina de la web pública referencias a IA, OpenAI, modelos, motores y GitHub Actions.
- La firma pública pasa a ser **Redacción de Gibraltar Watch** / **criterios editoriales de Gibraltar Watch**.
- No inventa periodistas, revisiones humanas ni cargos que no existan.
- El artefacto publicado excluye Python, tests, workflows, documentación técnica, source maps, ZIP y JSON independientes.
- Los datos que necesitan las páginas se encapsulan en memoria durante el build para mantener compatibilidad con el front-end sin publicar endpoints `.json`.
- Incluye una auditoría que bloquea el despliegue si reaparecen archivos o textos sensibles.
- Incluye un Worker de Cloudflare opcional/recomendado para bloquear rutas técnicas y añadir cabeceras de seguridad.

## Limitación técnica importante

Ninguna web puede impedir que el navegador reciba el HTML/CSS/JavaScript necesario para mostrarla. El objetivo real es **ocultar el repositorio fuente y el backend**, no prometer que el código ejecutado por el navegador sea invisible.

Para ocultar el código fuente del repositorio, el repositorio debe ser **privado**. La web pública se despliega desde un artefacto construido por GitHub Actions.
