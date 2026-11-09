"""Crear una demostración narrada a partir de las capturas del ensayo."""
import csv, statistics, subprocess, tempfile, wave
from pathlib import Path
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageOps

rows=list(csv.DictReader(Path("resultados/comparacion.csv").open(encoding="utf8")))
def metric(version):
    return statistics.median(float(x["p95"]) for x in rows if x["version"]==version and x["fase"]=="carga" and x["op"]=="listado")
a,b=map(metric,["antes","despues"])
say=lambda n: str(round(n,1)).replace(".", " coma ")
scenes=[
("demo-paso-1","Consultar una sala","La sala está libre para el intervalo solicitado.",
 "Esta es una API local de reservas de salas. En pantalla aparece una consulta real. Para el primero de mayo de dos mil cuarenta y cinco, la sala ochenta está disponible entre las dos y las tres de la tarde, en horario universal."),
("demo-paso-2","Crear la reserva","La API devuelve 201 y el identificador de la reserva.",
 "Al pulsar Reservar, la API guarda el horario en PostgreSQL y devuelve el identificador de la nueva reserva."),
("01-api","Comprobar el mismo horario","La segunda alta recibe 409 porque el horario ya está ocupado.",
 "Si consultamos otra vez, el horario ya aparece ocupado. Al repetir el alta, recibimos un conflicto. La base de datos protege la misma regla aunque lleguen dos solicitudes al mismo tiempo."),
("02-carga","Leer una prueba de carga","Tres corridas de 60 s por versión a 5 operaciones/s.",
 "Para medir la API se programaron cinco operaciones por segundo. De cada veinte, doce preguntaban por disponibilidad, cinco pedían una página y tres creaban una reserva. Un check del listado exigió diez filas en el orden correcto. El umbral para las lecturas era de trescientos milisegundos en el percentil noventa y cinco."),
("03-sql","Explicar la corrección","La segunda página necesita diez filas de salida y diez de desplazamiento.",
 "El listado ya cumplía el objetivo, pero PostgreSQL leía las ochenta mil reservas y las ordenaba para devolver diez. Al añadir un índice con el mismo orden que la consulta, el motor pudo detenerse después de leer veinte filas. La consulta siguió devolviendo la misma página."),
("02-carga","Comparar el p95 del listado",f"Mediana de tres p95: {a:.2f} ms antes y {b:.2f} ms después.".replace(".",","),
 f"Se repitieron las tres corridas con los mismos datos y la misma demanda. La mediana de los tres percentiles noventa y cinco del listado pasó de {say(a)} a {say(b)} milisegundos. Eso mide la solicitud completa, desde el cliente."),
("04-regresion","Verificar la regla de reserva","Dos altas simultáneas dejaron una sola fila persistida.",
 "Después del cambio volvimos a intentar dos altas simultáneas. Una se guardó y la otra recibió un conflicto. Al contar directamente en PostgreSQL, solo había una reserva para ese horario."),
("05-estres","Volver a carga baja","El último escalón vuelve a 2 operaciones/s.",
 "Por último, el estrés llegó a quince operaciones por segundo y regresó a dos. No se descartaron iteraciones. La tabla muestra el tiempo al principio y al final, y permite comprobar la recuperación. Esta prueba describe el rango medido en la computadora; no determina la capacidad máxima del servicio.")
]
tmp=Path(tempfile.mkdtemp(prefix="s15-video-"))
tts=tmp/"voz.ps1"
tts.write_text("""param([string]$Texto,[string]$Audio)
Add-Type -AssemblyName System.Speech
$v=New-Object System.Speech.Synthesis.SpeechSynthesizer
$v.SelectVoice('Microsoft Helena Desktop')
$v.Rate=0
$v.SetOutputToWaveFile($Audio)
$v.Speak([System.IO.File]::ReadAllText($Texto))
$v.Dispose()
""",encoding="utf-8-sig")
ff=imageio_ffmpeg.get_ffmpeg_exe()
parts=[]
font=lambda size,bold=False: ImageFont.truetype("C:/Windows/Fonts/"+("segoeuib.ttf" if bold else "segoeui.ttf"),size)
for i,(pic,title,caption,narration) in enumerate(scenes):
    wav=tmp/f"{i}.wav"; txt=tmp/f"{i}.txt";txt.write_text(narration,encoding="utf-8-sig")
    subprocess.run(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(tts),str(txt),str(wav)],check=True)
    with wave.open(str(wav)) as f: duration=f.getnframes()/f.getframerate()+.55
    canvas=Image.new("RGB",(1440,810),"#f5f8f7")
    draw=ImageDraw.Draw(canvas)
    draw.text((58,20),"Marvin Chiroy Lopreto   /   API de reservas con k6",font=font(22),fill="#38666b")
    draw.text((55,61),title,font=font(44,True),fill="#18353c")
    source=Image.open(Path("evidencias")/(pic+".png")).convert("RGB")
    scaled=ImageOps.contain(source,(1330,545))
    canvas.paste(scaled,(int((1440-scaled.width)/2),int(137+(545-scaled.height)/2)))
    draw.rectangle((0,705,1440,810),fill="#173e45")
    draw.text((55,735),caption,font=font(27),fill="white")
    png=tmp/f"{i}.png";canvas.save(png)
    part=tmp/f"v{i}.mp4"
    subprocess.run([ff,"-loglevel","error","-y","-loop","1","-framerate","10","-i",str(png),"-i",str(wav),"-t",str(duration),"-af","apad","-c:v","libx264","-threads","2","-preset","fast","-tune","stillimage","-pix_fmt","yuv420p","-c:a","aac","-ar","44100",str(part)],check=True)
    parts.append(part)
lst=tmp/"lista.txt";lst.write_text("\n".join("file '"+p.name+"'" for p in parts),encoding="utf8")
subprocess.run([ff,"-loglevel","error","-y","-f","concat","-safe","0","-i",str(lst),"-c","copy","-movflags","+faststart","Video-S15.mp4"],check=True)
