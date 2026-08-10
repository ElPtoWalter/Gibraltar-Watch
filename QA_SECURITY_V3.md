# QA · Professional Security v3

Pruebas realizadas antes de empaquetar:

- 11/11 pruebas unitarias de Observatory vNext: OK.
- Compilación Python de los scripts nuevos y modificados: OK.
- YAML de workflows: válido.
- Build sintético con `fetch('foo.json')`: el front-end conserva el dato, `foo.json` no se publica y los metadatos de implementación se eliminan: OK.
- Build del paquete: 0 archivos `.json` publicados: OK.
- Auditoría del artefacto: sin backend, workflows, source maps ni referencias de implementación: OK.
- Auditoría de secretos: OK.

Limitación deliberada: el HTML/CSS/JavaScript que un navegador necesita para representar una web siempre puede inspeccionarse. La protección se centra en no publicar el repositorio fuente, backend, workflows, tests, JSON brutos ni metadatos internos.
