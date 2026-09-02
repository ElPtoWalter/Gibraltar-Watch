"""Free, local evidence rules for the Gibraltar diary."""
import hashlib
from urllib.parse import urlsplit, urlunsplit


def source_key(item):
    host = (urlsplit(str(item.get("url", ""))).hostname or "").lower()
    # Google News delivers links; it is not the reporting source.
    return str(item.get("source") or host).casefold() if host == "news.google.com" else host


def item_key(item):
    url = urlsplit(str(item.get("url", "")))
    canonical = urlunsplit((url.scheme, url.netloc.lower(), url.path, "", ""))
    return hashlib.sha256((canonical or str(item.get("title", ""))).encode()).hexdigest()[:20]


def reading(section):
    if section == "Ceuta y Melilla":
        return "Una declaración sobre Ceuta o Melilla no mide la presión actual en la frontera. Para pasar del debate político a un dato operativo hacen falta lugar, fecha del hecho y una medida comprobable —por ejemplo, un cierre o un cambio de horario—. No se deducen colas, llegadas ni intenciones de una cita."
    if section == "España–Marruecos":
        return "Una declaración, una visita propuesta y una decisión vigente tienen alcances distintos. Antes de atribuir consecuencias al corredor hay que comprobar quién decide, desde cuándo se aplica la medida y a qué paso o servicio afecta. La agenda diplomática no demuestra una interrupción marítima."
    if section in {"Tráfico marítimo", "Puertos y logística", "Economía y comercio", "Energía y logística"}:
        return "Un dato portuario necesita unidad y periodo: toneladas, contenedores, pasajeros y escalas no son intercambiables. Una noticia sobre un puerto tampoco representa todo el Estrecho. Para comparar orillas hay que usar el mismo indicador, el mismo intervalo y explicar qué rutas quedan fuera."
    if section == "Seguridad y defensa":
        return "La presencia de medios militares o policiales no prueba una suspensión del tráfico. La comprobación útil es un aviso con ubicación, periodo de validez y restricciones concretas. Sin esos datos, la noticia se conserva como contexto de seguridad."
    return "La relación con el Estrecho se valora por el hecho descrito, no solo por el nombre de un lugar. El titular no permite completar cifras, causas ni consecuencias ausentes de la fuente."


def archive_decision(status, selected, previous):
    fields = ("maritime_status", "border_pressure", "bilateral_tension", "security_status")
    snapshot = {key: status.get(key) for key in fields}
    sources = {source_key(item) for item in selected}
    new = {item_key(item) for item in selected} - set(previous.get("source_keys") or [])
    old = previous.get("status_snapshot")
    material = bool(old and snapshot != old and new and len(sources) >= 2)
    return material, snapshot, sorted({item_key(item) for item in selected})
