# Reservas de salas con PostgreSQL y k6

Proyecto individual de Marvin Chiroy Lopreto, carné 2890-22-20336. El informe editable y el video se entregan en este repositorio. El protocolo previo está en PLAN.md. Los archivos originales se encuentran en resultados/ y las capturas en evidencias/.

## Preparar el laboratorio
Se probó con Python 3.12 para Windows, PostgreSQL 18.6 en Ubuntu bajo WSL2 y k6 2.3.0 para Windows. Flask despacha las rutas, Waitress sirve HTTP local con ocho hilos y psycopg usa un pool de dos a ocho conexiones. PostgreSQL aplica la regla de exclusión de horarios incluso ante escrituras concurrentes. La separación permite observar los procesos de API, generador y base. Sin contenedores. Solo la API escucha en 127.0.0.1:8765.

### 1. Ubicar el proyecto en Windows

En la PC de la entrega, abre **PowerShell** y ejecuta desde cualquier carpeta:

~~~powershell
Set-Location -LiteralPath 'D:\UMG\QA\[S15] k6 construir, medir y mejorar una API'
Get-Item -LiteralPath .\app.py, .\requirements.txt
~~~

Esa es la **raíz del proyecto**. Usa `-LiteralPath` porque el nombre incluye corchetes. Si estás en otro equipo, puedes clonar desde **PowerShell**, empezando en tu carpeta de usuario:

~~~powershell
Set-Location -LiteralPath $HOME
git clone https://github.com/mchiroyl/construir-medir-y-mejorar-una-API.git reservas-s15
Set-Location -LiteralPath .\reservas-s15
~~~

En ese caso, usa la carpeta `reservas-s15` que acabas de crear en cada bloque que indique «raíz». Las rutas `scripts\`, `k6\`, `db\` y `resultados\` parten de esa raíz. El ejecutor busca allí el script k6 y guarda allí los resultados.

### 2. Iniciar PostgreSQL — terminal 1, Ubuntu en WSL2

Abre **Ubuntu**. Puedes empezar en cualquier carpeta de Linux. La instalación de paquetes se hace una vez. En los siguientes arranques basta con iniciar PostgreSQL y comprobar que acepta conexiones:

~~~bash
cd ~
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
pg_isready -h 127.0.0.1 -p 5432
~~~

Solo la primera vez, si el rol y la base aún no existen, ejecuta en **la misma terminal Ubuntu**, desde `~`:

~~~bash
sudo -u postgres createuser --pwprompt s15
sudo -u postgres createdb --owner=s15 s15_reservas
~~~

Deja Ubuntu abierto durante la práctica.

### 3. Preparar Python y los datos — terminal 2, PowerShell

Abre otra terminal en Windows. En la **raíz del proyecto**, crea el entorno e instala las dependencias una vez. Se requiere Python 3.12 en Windows:

~~~powershell
Set-Location -LiteralPath 'D:\UMG\QA\[S15] k6 construir, medir y mejorar una API'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
~~~

En esta misma raíz, la aplicación y los scripts leen la conexión desde el archivo local `.dsn`, excluido de Git. Si ya está configurado, continúa al siguiente bloque. Para crearlo por primera vez en **PowerShell**, introduce la contraseña del rol `s15` cuando se solicite:

~~~powershell
$credencial = Get-Credential -UserName s15 -Message 'Contraseña del rol s15 de PostgreSQL'
$claveUri = [Uri]::EscapeDataString($credencial.GetNetworkCredential().Password)
Set-Content -LiteralPath .\.dsn -Encoding ascii -Value "postgresql://s15:$claveUri@127.0.0.1:5432/s15_reservas"
~~~

Si prefieres configurar `DATABASE_URL`, esa variable tiene prioridad sobre `.dsn` y debe estar disponible en **ambas** terminales PowerShell. Solo para una **base vacía**, carga las 80 salas y las 80 000 reservas desde **PowerShell, raíz del proyecto**:

~~~powershell
.\.venv\Scripts\python.exe .\scripts\preparar.py instalar
~~~

### 4. Arrancar la API — terminal 2, PowerShell

En cada arranque, con PostgreSQL activo, ejecuta desde la **raíz del proyecto** y deja abierta esta terminal. Para detener la API al terminar usa Ctrl+C aquí.

~~~powershell
Set-Location -LiteralPath 'D:\UMG\QA\[S15] k6 construir, medir y mejorar una API'
.\.venv\Scripts\python.exe .\app.py
~~~

### 5. Verificar la API — terminal 3, PowerShell

Abre **otra ventana PowerShell**. Esta será la terminal para todas las pruebas. Sitúate en la **misma raíz**:

~~~powershell
Set-Location -LiteralPath 'D:\UMG\QA\[S15] k6 construir, medir y mejorar una API'
Invoke-RestMethod http://127.0.0.1:8765/salud
~~~

La respuesta esperada contiene `estado` con valor `ok`. Instala k6 para Windows desde las [publicaciones oficiales](https://github.com/grafana/k6/releases). Si está en el PATH, comprueba la instalación con `k6 version` en esta terminal. Si descargaste el ZIP, ejecuta aquí las dos líneas siguientes sustituyendo la ruta de ejemplo por la de tu ejecutable:

~~~powershell
$env:K6_BIN = 'C:\herramientas\k6\k6.exe'
& $env:K6_BIN version
~~~

## Contrato
- GET /disponibilidad acepta recurso, inicio y fin con zona horaria. Devuelve disponible. El inicio es inclusivo y el fin exclusivo.
- POST /reservas recibe el mismo objeto JSON. Devuelve 201 y la fila creada; 409 si se traslapa; 400 si el intervalo es inválido; 404 si la sala no existe.
- GET /reservas?pagina=1&limite=10 permite 1–100 filas por página. Orden descendente por inicio y luego por id. Los datos reflejan la base al momento de cada consulta. Si hay escrituras entre dos páginas, su contenido puede moverse.
- Los datos se generan con una fórmula determinista, sin azar ni datos personales: 80 salas × 1 000 intervalos consecutivos de una hora, ocupados durante los primeros 30 minutos.

## Repetir el experimento
Ejecuta los bloques en orden. Mantén PostgreSQL en la terminal 1 y la API en la terminal 2. Usa **PowerShell en la terminal 3, desde la raíz del proyecto**, para las pruebas. Los identificadores 101–103 dejan libres las evidencias originales. Si ya existen carpetas con esos números, elige números nuevos para esa repetición.

**Preparar la línea base.** Si instalaste la semilla en una base vacía, continúa directamente con la regresión. Si la base ya tiene la corrección, antes de volver a medir «antes» ejecuta este bloque en **Ubuntu, terminal 1**, desde cualquier carpeta. Asegúrate de que ninguna prueba esté en curso:

~~~bash
cd ~
sudo -u postgres psql -d s15_reservas -c 'DROP INDEX IF EXISTS reservas_orden_inicio_id;'
~~~

**Medir la versión inicial.** En **PowerShell, terminal 3**, desde la raíz:

~~~powershell
Set-Location -LiteralPath 'D:\UMG\QA\[S15] k6 construir, medir y mejorar una API'
.\.venv\Scripts\python.exe .\scripts\regresion.py
.\.venv\Scripts\python.exe .\scripts\medir.py antes humo 101
101..103 | ForEach-Object { .\.venv\Scripts\python.exe .\scripts\medir.py antes carga $_; if ($LASTEXITCODE -ne 0) { throw "Revisar corrida $_" } }
.\.venv\Scripts\python.exe .\scripts\medir.py antes estres 101
~~~

**Aplicar la corrección.** En **la misma PowerShell, terminal 3**, desde la raíz y con los clientes de carga detenidos:

~~~powershell
.\.venv\Scripts\python.exe .\scripts\preparar.py restablecer
.\.venv\Scripts\python.exe .\scripts\preparar.py diagnosticar
.\.venv\Scripts\python.exe .\scripts\preparar.py corregir
.\.venv\Scripts\python.exe .\scripts\preparar.py diagnosticar
.\.venv\Scripts\python.exe .\scripts\regresion.py
~~~

`restablecer` elimina las altas del experimento, conserva las 80 000 reservas originales y reinicia el próximo ID en 80001. También puedes ejecutarlo por separado desde esta misma carpeta.

**Medir la versión corregida.** En **PowerShell, terminal 3**, desde la raíz:

~~~powershell
.\.venv\Scripts\python.exe .\scripts\medir.py despues humo 101
101..103 | ForEach-Object { .\.venv\Scripts\python.exe .\scripts\medir.py despues carga $_; if ($LASTEXITCODE -ne 0) { throw "Revisar corrida $_" } }
.\.venv\Scripts\python.exe .\scripts\medir.py despues estres 101
.\.venv\Scripts\python.exe .\scripts\resumir.py
~~~

Cada medición guarda sus archivos en `resultados\<versión>\<escenario>-<número>\` dentro de la raíz. Por ejemplo, el resumen del nuevo humo inicial queda en `resultados\antes\humo-101\k6.txt`. El último comando regenera `resultados\comparacion.csv` con todas las corridas disponibles, incluidas las originales. El campo `corrida` permite identificar las nuevas.

### Leer una corrida en Windows PowerShell 5.1

Cada nueva medición crea un `resumen.txt` en español que PowerShell 5.1 reconoce automáticamente. Para cualquier corrida anterior, también puedes mostrar esa vista directamente. Desde la raíz del proyecto:

~~~powershell
python .\scripts\leer_corrida.py .\resultados\despues\carga-1
~~~

Si quieres inspeccionar el registro original, usa `Get-Content -Encoding UTF8` con la ruta absoluta a `k6.txt`. Para leer el motivo de una interrupción en `ejecucion.json`, pasa el contenido a `ConvertFrom-Json` antes de mostrar el campo `aborto`.

El script k6/reservas.js contiene los tres escenarios. El ejecutor aplica el límite de recursos del host, conserva el log, el código de salida, la serie JSON comprimida y las muestras de recursos aproximadamente cada dos segundos. Tras un aborto por seguridad esperar hasta recuperar el margen de CPU/RAM, revisar /salud y ejecutar humo con un nuevo número. En k6.txt se encuentra la evaluación de thresholds; comparacion.csv se reconstruye a partir de las series. En CPU de proceso, 100 % equivale a un procesador lógico; las cifras de RSS de PostgreSQL pueden contar páginas compartidas más de una vez. Las tasas por fase en el CSV se calculan con su duración nominal. k6 puede iniciar una iteración junto al límite de una etapa.

Documentación del ejecutor y criterios: https://grafana.com/docs/k6/latest/ y https://grafana.com/docs/k6/latest/using-k6/thresholds/

## Evidencias para revisión
- Informe editable: [Informe S15.docx](./Informe%20S15.docx). Video narrado: [descargar MP4](https://github.com/mchiroyl/construir-medir-y-mejorar-una-API/releases/download/entrega/Video-S15.mp4).
- Resultados completos: [antes](./resultados/antes), [después](./resultados/despues) y [comparación por corrida y fase](./resultados/comparacion.csv).
- Diagnóstico y regresión: resultados/plan-antes.txt, resultados/plan-despues.txt y resultados/regresion-*.txt.
- En la primera preparación se corrigió la identificación del socket de Windows antes de arrancar k6. El humo inicial válido es humo-2. En ese humo y en carga-1 inicial faltan los contadores de PostgreSQL; CPU del host, API, generador y memoria sí se recogieron. Los demás muestreos incluyen los contadores de la base.
- Las capturas del cliente de demostración provienen de peticiones HTTP reales. Las demás capturas presentan extractos de los originales o la tabla reconstruida de las series. Para rehacerlas, instalar Pillow y playwright para Python, disponer de Edge, restablecer la semilla y ejecutar scripts/capturas.py desde la raíz.
