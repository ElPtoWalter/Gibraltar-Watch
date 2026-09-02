"""Reproducible audit of stored OPE extraction; not a new official traffic report."""
import csv
import html
import json
from datetime import date, datetime, timezone


def audit(data):
    result = []
    for phase in ("departure", "return"):
        block = data.get(phase) or {}
        for unit in ("rotations", "passengers", "vehicles"):
            total = (block.get("day") or {}).get(unit)
            rows = block.get("routes") or []
            if not isinstance(total, (int, float)) or not rows or not all(isinstance(row.get(unit), (int, float)) for row in rows):
                result.append((phase, unit, total, None, None))
                continue
            subtotal = sum(row[unit] for row in rows)
            result.append((phase, unit, total, subtotal, total - subtotal))
    return result


def build_report(root):
    path = root / "ope-2026.json"
    if not path.exists():
        return
    data = json.loads(path.read_text())
    rows = audit(data)
    report_date = str(data.get("report_date") or "")
    try:
        age = (datetime.now(timezone.utc).date() - date.fromisoformat(report_date)).days
        age_text = f"{age} días" if age >= 0 else "fecha futura: revisar"
    except ValueError:
        age_text = "fecha no disponible"
    export = root / "ope-audit.csv"
    with export.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("report_date", "phase", "unit", "recorded_day_total", "stored_routes_sum", "difference"))
        writer.writerows((report_date, *row) for row in rows)
    phase_names = {"departure": "Salida", "return": "Retorno"}
    units = {"rotations": "Rotaciones", "passengers": "Pasajeros", "vehicles": "Vehículos"}
    fmt = lambda value: "Sin dato" if value is None else f"{value:,}".replace(",", ".")
    table = "".join(f"<tr><td>{phase_names[phase]}</td><td>{units[unit]}</td><td>{fmt(total)}</td><td>{fmt(subtotal)}</td><td>{fmt(diff)}</td></tr>" for phase, unit, total, subtotal, diff in rows)
    gaps = [row for row in rows if row[-1] not in (0, None)]
    missing = sum(row[-1] is None for row in rows)
    es = html.escape
    source_url = str(data.get("source_url") or "")
    if not source_url.startswith("https://www.proteccioncivil.es/"):
        source_url = "https://www.proteccioncivil.es/"
    example = next((row for row in rows if row[0] == "departure" and row[1] == "passengers"), None)
    calculation = (f"{fmt(example[2])} − {fmt(example[3])} = {fmt(example[4])}" if example and example[4] is not None else "No hay datos suficientes para la resta.")
    page = f'''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Auditoría de datos OPE: fecha, totales y rutas | Gibraltar Watch</title><meta name="description" content="Análisis propio del dato OPE almacenado: diferencias entre totales y rutas, antigüedad del informe y cálculos reproducibles."><link rel="canonical" href="https://estrechogibraltar.com/auditoria-datos-ope.html"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/diario.css?v=20260831-4"></head><body class="gd-page"><div class="site-shell"><header class="gd-top"><a class="gd-brand" href="/">GIBRALTAR WATCH</a><nav><a href="/diario/">Diario</a><a href="/operacion-paso-estrecho-2026.html">OPE</a><a href="/metodologia.html">Metodología</a><a href="/contacto.html">Correcciones</a></nav></header><main class="gd-shell"><article><header class="gd-hero"><p class="gd-kicker">ANÁLISIS PROPIO · AUDITORÍA REPRODUCIBLE</p><h1>OPE: por qué sumar las rutas no siempre reproduce el total</h1><p class="gd-deck">Comprobamos la fecha y la consistencia del extracto que utiliza Gibraltar Watch. Esta auditoría describe nuestra copia de datos, no certifica el contenido íntegro del PDF oficial.</p></header>
<section class="gd-prose"><h2>Una consulta reciente puede mostrar un informe antiguo</h2><p>La copia del monitor conserva un informe fechado <strong>{es(report_date or "sin fecha")}</strong>. Antigüedad al generar esta página: {age_text}. La última consulta técnica registrada es {es(str(data.get("checked_at") or "sin fecha"))}. Son dos relojes distintos: consultar hoy una página no convierte sus cifras en datos de hoy.</p><p>Por tanto, estos números no permiten responder cuántos pasajeros están cruzando ahora, cuál es la cola de embarque ni cuántas plazas quedan. Tampoco se extrapola un día antiguo al resto de la campaña.</p></section>
<section class="gd-prose"><h2>La comprobación que hacemos</h2><p>Para cada fase sumamos las rutas presentes en nuestra copia y restamos ese subtotal del total diario almacenado. Lo repetimos por separado para rotaciones, pasajeros y vehículos. No mezclamos salidas con retornos ni totales del día con acumulados de campaña.</p><p>Resultado: <strong>{len(gaps)} de {len(rows)} comprobaciones presentan una diferencia distinta de cero</strong>; {missing} no disponen de todos los campos necesarios. Una diferencia advierte de un desglose incompleto o de un posible problema de extracción. No demuestra un error de Protección Civil ni identifica por sí sola la ruta que falta.</p><div style="overflow-x:auto"><table style="width:100%;text-align:left;border-spacing:0.6rem"><caption>Cifras tal como están almacenadas en el monitor</caption><thead><tr><th>Fase</th><th>Unidad</th><th>Total diario</th><th>Suma de rutas</th><th>Diferencia</th></tr></thead><tbody>{table}</tbody></table></div></section>
<section class="gd-prose"><h2>Un ejemplo, paso a paso</h2><p>Para pasajeros en la fase de salida, la resta es: <strong>{calculation}</strong>. El primer número es el total diario del extracto; el segundo es la suma de las rutas que conservamos. La diferencia no se asigna a una ruta imaginada ni se reparte proporcionalmente.</p><p>Si se calcula la cuota de una ruta usando solo la suma parcial como denominador, su peso puede quedar inflado. Si se utiliza el total diario, hay que mostrar la parte no desglosada. Una clasificación de puertos sin explicar esta diferencia daría una precisión que el conjunto no tiene.</p></section>
<section class="gd-prose"><h2>Qué se puede comparar y qué no</h2><p>Una rotación es una unidad distinta de un pasajero o un vehículo. Dividir pasajeros entre rotaciones arroja un promedio por operación registrada, no una tasa de ocupación: para esta última haría falta la capacidad ofertada. Un promedio puede ocultar diferencias grandes entre rutas.</p><p>Salida y retorno son fases distintas de la campaña. Sus totales no deben tratarse como entradas y salidas de una población cerrada: el dato no identifica personas únicas ni asegura que cada pasajero tenga su viaje de vuelta dentro del mismo periodo.</p><p>Los acumulados sirven para describir lo registrado desde el comienzo del periodo, mientras que la tabla anterior compara únicamente el día del informe. Mezclarlos produciría una diferencia artificial incluso si la extracción fuera perfecta.</p></section>
<section class="gd-prose"><h2>Fuentes, descarga y límites</h2><p><a href="{es(source_url, quote=True)}" target="_blank" rel="noopener noreferrer">Documento de Protección Civil enlazado por el monitor</a> · <a href="/ope-audit.csv" download>Descargar los seis cálculos (CSV)</a> · <a href="/operacion-paso-estrecho-2026.html">Panel OPE y desglose almacenado</a>.</p><p>La referencia al documento procede del registro del proyecto; esta auditoría no afirma haber vuelto a contrastar cada cifra con el PDF. Si la descarga oficial ha cambiado o la extracción es parcial, la corrección debe hacerse en la fuente de datos antes de presentar el desglose como completo.</p><p>Para reproducir la tabla, toma las rutas del panel, suma cada unidad dentro de su fase y réstala del total del día. El CSV publica ambos operandos y la diferencia. Los cálculos se actualizan automáticamente con la copia disponible en cada publicación; si faltan campos se muestran como «Sin dato», nunca como cero.</p></section></article></main></div></body></html>'''
    (root / "auditoria-datos-ope.html").write_text(page, encoding="utf-8")
