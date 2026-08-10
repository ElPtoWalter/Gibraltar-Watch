# Observatory vNext · salto de calidad total

Esta versión no sustituye Gibraltar Watch: lo convierte en un observatorio más explicable, histórico, auditable y resistente.

## 20 mejoras abordadas

1. **Health monitor**: `health.json`, diagnóstico de frescura e integridad y auditoría externa diaria.
2. **Estado del Estrecho**: motor conservador con cinco niveles, confianza y cuatro capas separadas.
3. **Cronología automática**: `timeline.json` registra cambios materiales, nuevos partes, Diario, sismicidad y anomalías nuevas.
4. **Diario reforzado**: postprocesado de trazabilidad sin reescribir los hechos del artículo.
5. **Hechos / interpretación / escenarios**: señalización editorial y nueva página de transparencia.
6. **Salud de fuentes**: fecha de consulta, antigüedad, fuente, enlace y nota metodológica.
7. **Semáforo de frescura**: actualizado / revisar frescura / desactualizado / sin datos.
8. **Panel “ahora mismo”**: estado, confianza, noticias 24 h, sismicidad y salud visibles de un vistazo.
9. **Histórico propio**: `observatory-history.json`, hasta 730 instantáneas diarias.
10. **Página de datos**: métricas, series históricas y gráficas SVG sin dependencia de una librería de charts.
11. **Niveles de aviso**: informativo, relevante, importante y urgente; solo los cambios altos generan Issue.
12. **Detector de anomalías**: noticias, sismicidad y OPE, activado únicamente con histórico suficiente y con lenguaje no causal.
13. **Mapa estratégico**: nodos del Estrecho y capa sísmica; el corredor conceptual se identifica como no-AIS.
14. **SEO avanzado**: nuevas páginas con canonical, Open Graph, JSON-LD, sitemap e IndexNow sobre el sitemap actualizado.
15. **RSS**: `observatory-feed.xml` con cambios del observatorio.
16. **Newsletter**: generación automática `newsletter/latest.html`, `.txt` y `.json`, además de `/boletin.html`.
17. **Monetización responsable**: se mantiene intacta la separación ya existente entre publicidad/patrocinio e indicadores editoriales.
18. **Transparencia**: nueva `/transparencia.html` con automatización, IA, fuentes, anomalías y límites explicados.
19. **Correcciones**: `/correcciones.html` + `corrections.json`, preparado como registro público persistente.
20. **Recuperación y backups**: publicación bloqueada si falla QA, checksums SHA-256 en `publication-manifest.json` y rollback basado en historial Git.

## Mejoras extra

- Alertas locales del navegador para cambios de nivel mientras la web está abierta.
- Issues automáticos de GitHub solo para transiciones de prioridad alta, evitando ruido.
- Auditoría independiente diaria contra la web realmente publicada, no solo contra archivos locales.
- Sanitización del texto externo mostrado en popups del mapa.
- Pruebas unitarias específicas de la lógica del observatorio y de la idempotencia de los instaladores.
- El newsletter no inventa un backend ni almacena emails en un repositorio público: queda listo para conectar de forma explícita a un proveedor compatible con consentimiento y bajas.
