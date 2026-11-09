"""Capturas de navegador de extractos originales. Ejecutar después de las pruebas."""
import html,json,subprocess,tempfile,time
from pathlib import Path
import requests
from PIL import Image

root=Path.cwd()
out=root/"evidencias"
out.mkdir(exist_ok=True)
edge=Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
def shot(name,title,subtitle,body,height=530):
    style="""*{box-sizing:border-box}body{background:#fff;font:22px 'Segoe UI',sans-serif;color:#152d36;margin:32px}h1{font-size:34px;font-weight:650;margin:0 0 8px}p{font-size:19px;color:#45636c;margin:0 0 20px}pre{background:#eff5f5;color:#102e37;padding:16px 22px;font:21px/1.45 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;margin:0}"""
    folder=Path(tempfile.gettempdir())/"s15-evidence"
    folder.mkdir(exist_ok=True)
    file=folder/(name+".html")
    file.write_text('<meta charset="utf-8"><style>'+style+'</style><h1>'+html.escape(title)+'</h1><p>'+html.escape(subtitle)+'</p><pre>'+html.escape(body)+'</pre>',encoding="utf8")
    target=out/(name+".png")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel="msedge")
        page=browser.new_page(viewport={"width":1280,"height":height})
        page.goto(file.as_uri())
        page.screenshot(path=str(target),full_page=True)
        browser.close()
    # Crop only bottom whitespace to keep the captured text readable in the report.
    im=Image.open(target).convert("RGB")
    from PIL import ImageChops
    bbox=ImageChops.difference(im,Image.new("RGB",im.size,"white")).getbbox()
    im.crop((0,0,im.width,min(im.height,bbox[3]+22))).save(target)

def main():
    from demo import capture
    capture()
    pieces=[]
    for label in ("antes","despues"):
        f=Path("resultados")/label/"carga-2"/"k6.txt"
        lines=f.read_text(encoding="utf8").splitlines()
        pieces.append(label.upper()+" · carga-2\n"+"\n".join(x.strip() for x in lines if ("{ op:listado }" in x and "avg=" in x) or "http_req_failed.........." in x or "http_reqs........" in x))
    shot("02-carga","El mismo listado bajo carga","Extractos de k6.txt · carga-2 de cada versión · tiempos HTTP", "\n\n".join(pieces),500)
    sql=[]
    for stage in ("antes","despues"):
        content=Path(f"resultados/plan-{stage}.txt").read_text(encoding="utf8")
        sql.append(stage.upper()+"\n"+"\n".join(s.strip() for s in content.splitlines() if any(x in s for x in ("Scan","Sort Method","Execution Time","Sort Key"))))
    shot("03-sql","Cómo obtuvo PostgreSQL la segunda página","EXPLAIN ANALYZE con búferes · misma consulta, 10 filas", "\n\n".join(sql),530)
    reg=Path("resultados/regresion-despues.txt").read_text(encoding="utf8")
    shot("04-regresion","Regresión después de crear el índice","Dos solicitudes simultáneas para un mismo horario · prueba automatizada",reg.strip(),550)
    import csv
    rows=list(csv.DictReader(Path("resultados/comparacion.csv").open(encoding="utf8")))
    seq=["base","normal","media","pico","recuperacion"]
    lines=["Fase          Oferta/s   HTTP antes/después   p95 antes/después (ms)"]
    for phase,rate in zip(seq,[2,5,10,15,2]):
        a,b=[next(x for x in rows if x["version"]==stage and x["fase"]==phase and x["op"]=="todas") for stage in ("antes","despues")]
        lines.append(f'{phase:14}{rate:>6}        {a["n"]:>3} / {b["n"]:<3}            {float(a["p95"]):>5.2f} / {float(b["p95"]):5.2f}')
    shot("05-estres","Estrés y regreso a carga baja","Tabla calculada de los puntos originales de estres-1 · cada fase dura 20 s","\n".join(lines),390)
if __name__=="__main__": main()


