"""Construir el Word editable usando las evidencias resultantes del experimento."""
import csv,json,statistics as st
from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.enum.text import WD_ALIGN_PARAGRAPH
rows=list(csv.DictReader(Path("resultados/comparacion.csv").open(encoding="utf8")))
stages=["antes","despues"]
def pick(stage,phase,op):
    return [x for x in rows if x["version"]==stage and x["fase"]==phase and x["op"]==op]
def med(stage,op,key):
    return st.median(float(x[key]) for x in pick(stage,"carga",op))
def fmt(x):return f"{x:.2f}".replace(".",",")
a,b=[med(s,"listado","p95") for s in stages]
repo="https://github.com/mchiroyl/construir-medir-y-mejorar-una-API"
video=repo+"/releases/download/entrega/Video-S15.mp4"
d=Document()
sec=d.sections[0];sec.top_margin=Inches(.66);sec.bottom_margin=Inches(.62)
sec.left_margin=sec.right_margin=Inches(.85)
ss=d.styles
for name,size,col in [("Normal",11,"263B43"),("Title",29,"142D37"),("Heading 1",23,"142D37"),("Heading 2",15,"135B5A")]:
    s=ss[name];s.font.name="Calibri";s.font.size=Pt(size);s.font.color.rgb=RGBColor.from_string(col)
    s.paragraph_format.space_after=Pt(5)
for e in ss["Title"].element.xpath(".//w:pBdr"):e.getparent().remove(e)
d.core_properties.author="Marvin Chiroy Lopreto"
d.core_properties.title="Evaluación de una API de reservas con k6"
p=d.add_paragraph
def link(label,url):
    para=p(); h=OxmlElement("w:hyperlink");h.set(qn("r:id"),para.part.relate_to(url,RT.HYPERLINK,is_external=True))
    r=OxmlElement("w:r"); prop=OxmlElement("w:rPr");color=OxmlElement("w:color");color.set(qn("w:val"),"086A71");prop.append(color);u=OxmlElement("w:u");u.set(qn("w:val"),"single");prop.append(u);r.append(prop);t=OxmlElement("w:t");t.text=label;r.append(t);h.append(r);para._p.append(h)
def h(text):d.add_heading(text,2)
def page(title):d.add_page_break(); d.add_heading(title,1)
def tbl(data):
    t=d.add_table(rows=0,cols=len(data[0]));t.style="Light Shading Accent 1"
    for line in data:
        cells=t.add_row().cells
        for c,v in zip(cells,line):
            c.text=str(v)
            for par in c.paragraphs:
                par.paragraph_format.space_after=Pt(2)
                for r in par.runs:r.font.size=Pt(10)
def pic(name,caption,width=6.5):
    d.add_picture("evidencias/"+name+".png",width=Inches(width))
    para=p(caption);para.runs[0].italic=True;para.runs[0].font.size=Pt(10)
foot=sec.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.RIGHT;foot.add_run("Marvin Chiroy Lopreto   ·   S15     /     ")
fld=OxmlElement("w:fldSimple");fld.set(qn("w:instr"),"PAGE");foot._p.append(fld)
p("Evaluación de una API de reservas con k6","Title")
p("Marvin Chiroy Lopreto   ·   Carné 2890-22-20336   ·   9 de noviembre de 2026")
h("Qué cambió")
p(f"Al consultar las reservas más recientes, PostgreSQL recorría la tabla para devolver apenas diez filas. Después de añadir un índice en el orden de la página, el p95 del listado pasó de {fmt(a)} a {fmt(b)} ms bajo una demanda de cinco operaciones por segundo. Son las medianas de tres corridas por versión.")
p("La regla principal se mantuvo: si dos personas piden la misma sala y el mismo horario, solo una puede reservarlo. La API permite consultar disponibilidad, crear una reserva y recorrer el listado por páginas.")
link("Abrir repositorio, código y resultados originales",repo)
link("Abrir video de la demostración",video)
pic("01-api","Figura 1. La sala estaba libre. Después del alta, la misma consulta devolvió false y el segundo intento recibió 409. Captura del registro HTTP de evidencias/demo-api.json.")
page("Diseño de las pruebas")
p("La demanda es una hipótesis de trabajo para una sede pequeña. Por cada 20 operaciones se programaron 12 consultas de disponibilidad, 5 listados y 3 altas. Cada iteración hizo una solicitud. Los horarios de altas fueron únicos; los conflictos intencionales se verificaron aparte.")
tbl([["Prueba","Oferta y duración","Decisión que permite tomar"],["Humo","1/s durante 20 s","Comprobar las tres rutas y sus respuestas."],["Sostenida","5/s durante 60 s; tres corridas por versión","Comparar el p95 con repeticiones y observar variación."],["Estrés","2, 5, 10, 15 y 2/s; 20 s por fase","Observar la degradación y el regreso a la tasa inicial."]])
h("Criterios fijados antes de medir")
p("El p95 debía quedar por debajo de 300 ms en lecturas y de 500 ms en altas, que además confirman una transacción. Se exigió menos de 1 % de errores HTTP inesperados, al menos 99 % de checks válidos y cero iteraciones descartadas. En recuperación, p95 global inferior a 300 ms. El p99 se registró para examinar la cola.")
p("Los checks verifican los estados libre y ocupado, el tamaño y orden del listado, y los datos devueltos al crear. El script usa tasas de llegada independientes del tiempo de respuesta. Se fijó un timeout de 2 s. En estrés hay 2 VUs precargados y hasta 4 por escalón; en carga y humo, 4 iniciales y hasta 16.")
h("Cuándo detenerse")
p("El monitor termina k6 si la RAM libre cae por debajo de 2 GiB o la CPU del equipo supera 90 % durante 10 s. k6 evalúa también un aborto si los errores HTTP acumulados superan 5 % después de 10 s. El procedimiento tras un aborto es esperar margen, consultar salud y repetir humo. El alcance termina en 15 operaciones/s.")
link("Consultar el plan previo en la versión inicial",repo+"/blob/antes/PLAN.md")
page("Carga sostenida y variación")
p("Cada fila agrupa tres corridas de un minuto con la misma mezcla y el mismo calentamiento. Se calculó cada percentil dentro de su corrida y después se tomó la mediana de las tres mediciones. Todos los tiempos están en milisegundos.")
data=[["Operación","p50 antes / después","p95 antes / después","p99 antes / después"]]
for op in ("disponibilidad","listado","crear","todas"):
    data.append([op.capitalize()]+[" / ".join(fmt(med(s,op,k)) for s in stages) for k in ("p50","p95","p99")])
tbl(data)
h("El listado en cada repetición")
vals=lambda s:[float(x["p95"]) for x in pick(s,"carga","listado")]
tbl([["Versión","Corrida 1","Corrida 2","Corrida 3"],["Inicial",*map(fmt,vals("antes"))],["Con índice",*map(fmt,vals("despues"))]])
p(f"La reducción mediana fue de {fmt(a-b)} ms ({fmt((a-b)*100/a)} %). Los rangos observados fueron {fmt(min(vals('antes')))}–{fmt(max(vals('antes')))} ms antes y {fmt(min(vals('despues')))}–{fmt(max(vals('despues')))} ms después. El p99 de creación tiene pocas observaciones por corrida; puede moverse por una sola petición lenta.")
p("En creación, el p95 mediano pasó de "+fmt(med("antes","crear","p95"))+" a "+fmt(med("despues","crear","p95"))+" ms. En disponibilidad pasó de "+fmt(med("antes","disponibilidad","p95"))+" a "+fmt(med("despues","disponibilidad","p95"))+" ms. Estas diferencias incluyen variación del equipo entre corridas.")
pic("02-carga","Figura 2. Extractos de carga-2/k6.txt de ambas versiones. La serie completa permite verificar los conteos y recalcular los percentiles.")
counts=[sum(int(x["n"]) for x in pick(s,"carga","todas")) for s in stages]
p(f"Las tres corridas completaron {counts[0]} solicitudes antes y {counts[1]} después, a {fmt(counts[0]/180)} y {fmt(counts[1]/180)} solicitudes/s. Aquí las iteraciones/s coinciden con las solicitudes/s. Las pequeñas diferencias frente a 5/s se deben al conteo en los extremos de la ventana.")
page("Diagnóstico y regresión funcional")
p("El listado fue la lectura más lenta de la versión inicial. Aunque cumplía el umbral, resultaba costoso ordenar las reservas para entregar solo diez. La hipótesis fue que el motor podría detenerse al completar la página si encontraba las filas ya ordenadas.")
pic("03-sql","Figura 3. Extractos de resultados/plan-antes.txt y plan-despues.txt. Se ejecutó la misma consulta de la segunda página sobre la semilla restablecida.")
p("Se creó un índice B-tree por inicio descendente e id descendente. El segundo campo resuelve los empates. La consulta, su paginación y la exclusión de traslapes se conservaron. Los tiempos de EXPLAIN pertenecen al motor SQL; los tiempos HTTP incluyen el resto de la solicitud.")
pic("04-regresion","Figura 4. La regresión verificó el conflicto concurrente y consultó PostgreSQL para contar las filas persistidas. Originales en resultados/regresion-antes.txt y regresion-despues.txt.")
page("Estrés y recuperación")
pic("05-estres","Figura 5. Tabla derivada de las series originales de estres-1. Los dos escalones a 2/s permiten comparar el inicio con el período posterior al pico.")
for s in stages:
    base=pick(s,"base","todas")[0];recovery=pick(s,"recuperacion","todas")[0]; peak=pick(s,"pico","todas")[0]
    p(f"{'Versión inicial' if s=='antes' else 'Versión corregida'}: el p95 global fue {fmt(float(base['p95']))} ms al inicio, {fmt(float(peak['p95']))} ms en el pico y {fmt(float(recovery['p95']))} ms al regresar a 2/s. El pico completó {peak['n']} solicitudes en 20 s.")
total=[x for x in rows if x["op"]=="todas"]
n=sum(int(x["n"]) for x in total); err=sum(float(x["errores"]) for x in total); drops=sum(float(x["descartadas"]) for x in total); checks=sum(float(x["checks_ok"]) for x in total)
p(f"En las pruebas de ambas versiones se completaron {n} solicitudes, con {int(err)} errores HTTP inesperados y {int(checks)} checks correctos. k6 registró {int(drops)} iteraciones descartadas. Los dos humos, las seis cargas y los dos escenarios de estrés terminaron con código cero.")
p("En un modelo de llegadas, una iteración descartada indica que k6 no pudo iniciarla a tiempo. Para atribuirla habría que contrastar VUs, duración de las iteraciones y recursos del generador y del sistema. El pico probado no mostró saturación. Veinte segundos de recuperación permiten observar el retorno inmediato, pero no establecen estabilidad prolongada.")
base_i,base_f=[pick(s,"base","todas")[0] for s in stages]
media_i,media_f=[pick(s,"media","todas")[0] for s in stages]
p("También hubo dos retrocesos en estrés: el p95 global del primer escalón pasó de "+fmt(float(base_i["p95"]))+" a "+fmt(float(base_f["p95"]))+" ms y el escalón de 10/s pasó de "+fmt(float(media_i["p95"]))+" a "+fmt(float(media_f["p95"]))+" ms. Hubo una sola corrida de estrés por versión. Esos valores describen la variación observada; no identifican su causa.")
h("Límites de la comparación")
p("Las versiones se ejecutaron en dos bloques sucesivos, en un equipo compartido por el generador y la API. La caché del SO permaneció caliente y los procesos de fondo siguieron activos. El índice también ocupa espacio y se actualiza con cada alta. No se midieron retención prolongada, acceso remoto ni páginas profundas.")
page("Entorno y trazabilidad")
p("Windows 11 Pro 10.0.26300, Intel Core i5-13420H, 12 procesadores lógicos y 15,71 GiB de RAM. PostgreSQL 18.6 en Ubuntu 26.04 LTS bajo WSL2, con 7 792 MiB visibles. API en Python 3.12.10, Flask 3.1.3, Waitress 3.0.2 y psycopg 3.3.6. k6 2.3.0 se ejecutó en Windows. No se usaron contenedores ni cuotas de contenedor.")
p("Se mantuvieron 80 salas y 80 000 reservas iniciales. Antes de cada medición se eliminaron las altas de prueba, se restableció la identidad, se ejecutó VACUUM ANALYZE y se hicieron cinco listados de calentamiento. El pool admitía 2–8 conexiones y la API, ocho hilos. El commit exacto se guardó en cada ejecucion.json.")
h("Recursos durante carga sostenida")
p("Máximos muestreados para las tres cargas de cada versión, salvo la RAM disponible, que muestra el mínimo. La CPU de proceso usa un núcleo como referencia. Las muestras se tomaron aproximadamente cada dos segundos.")
info={}
for s in stages:
    samples=[]
    for f in Path("resultados",s).glob("carga-*/recursos.csv"):
        samples+=list(csv.DictReader(f.open()))
    def value(k,op=max,div=1):
        return op(float(r[k])/div for r in samples if r.get(k))
    info[s]=[value("cpu_host_pct"),value("ram_disponible_gib",min),value("rss_api_mib"),value("rss_k6_mib"),value("pg_rss_suma_kib",max,1024),value("cpu_api_pct_un_nucleo"),value("cpu_k6_pct_un_nucleo")]
tbl([["Indicador","Antes","Después"]]+[[label,fmt(info["antes"][j]),fmt(info["despues"][j])] for j,label in enumerate(["CPU del host (%)","RAM libre mínima (GiB)","RSS de la API (MiB)","RSS de k6 (MiB)","RSS sumado de PostgreSQL (MiB)","CPU de la API (% de un núcleo)","CPU de k6 (% de un núcleo)"])])
p("La suma RSS de PostgreSQL incluye memoria compartida repetida. Sus contadores faltan en el humo inicial y en la primera carga inicial por un problema de lectura desde Windows. La sonda se corrigió sin cambiar k6, la API, los límites ni la demanda. No se atribuye el cambio de latencia a diferencias de RAM.")
p("En resultados/antes y resultados/despues, cada corrida conserva k6.txt, serie.json.gz, recursos.csv y ejecucion.json. Las etiquetas antes y despues identifican el esquema probado. El README explica cómo instalar, configurar, iniciar y restablecer el laboratorio.")
link("Ver los archivos originales de las corridas",repo+"/tree/main/resultados")
d.save("Informe S15.docx")



