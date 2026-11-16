"""Vista en español de los registros originales de una corrida de k6."""
import json
import re
from pathlib import Path


def resumen(carpeta):
    datos = json.loads((carpeta / "ejecucion.json").read_text(encoding="utf-8-sig"))
    lineas = [f"Prueba {carpeta.name} ({carpeta.parent.name})"]
    if datos.get("aborto"):
        lineas.append(f"Prueba interrumpida por seguridad. Motivo: {datos['aborto']}.")
    elif datos["salida"] == 0:
        lineas.append("La prueba terminó y cumplió todos los umbrales.")
    else:
        lineas.append(f"La prueba terminó con código {datos['salida']}. Consulta el registro de k6.")

    log = (carpeta / "k6.txt").read_text(encoding="utf-8-sig")
    etiquetas = {
        "checks_succeeded": "Verificaciones correctas",
        "http_req_failed": "Solicitudes HTTP fallidas",
        "dropped_iterations": "Iteraciones descartadas",
    }
    for clave, etiqueta in etiquetas.items():
        valor = re.search(rf"^\s*{clave}\.+:\s*(.+)$", log, re.MULTILINE)
        if valor:
            texto = valor[1].strip().replace(" out of ", " de ")
            lineas.append(f"{etiqueta}: {texto}")
    latencia = re.search(r"^\s*http_req_duration\.+:[^\n]*?p\(95\)=(\S+)", log, re.MULTILINE)
    if latencia:
        lineas.append(f"Tiempo de respuesta HTTP (p95): {latencia[1]}")
    if not log.strip():
        lineas.append("k6 no llegó a escribir su resumen final.")
    return "\n".join(lineas)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carpeta", type=Path)
    print(resumen(parser.parse_args().carpeta))
