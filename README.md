# Reservas de salas con PostgreSQL y k6

Proyecto individual de Marvin Chiroy Lopreto, carné 2890-22-20336. El informe editable y el video se entregan en este repositorio. El protocolo previo está en PLAN.md. Los archivos originales se encuentran en resultados/ y las capturas en evidencias/.

## Reiniciar en la PC de la entrega

Usa tres ventanas. **A** controla PostgreSQL en Ubuntu, **B** mantiene la API abierta y **C** sirve para las pruebas. Los bloques de PowerShell empiezan en Windows, donde el indicador de la consola comienza con `PS`. Copia solo las líneas de los bloques. En una instalación nueva, completa primero el apartado **Instalación inicial** al final.

### 1. Detener el laboratorio anterior

1. **Ventana C, pruebas.** Si k6 está midiendo, espera a que termine y regrese el indicador `PS` para que escriba el resultado.
2. **Ventana B, API.** En la consola que ejecuta `python .\app.py`, pulsa **Ctrl+C** una vez. Si la API ya está apagada, continúa.
3. **Ventana A.** Si ves `Password:`, pulsa **Ctrl+C**. Si ves un indicador de Ubuntu terminado en `$`, escribe `exit` para regresar a PowerShell. Desde **PowerShell**, en cualquier carpeta, detén la instancia de PostgreSQL del laboratorio y comprueba su estado:

~~~powershell
# A | PowerShell | cualquier carpeta de Windows
wsl -d Ubuntu -u root -- pg_ctlcluster 18 main stop
wsl -d Ubuntu -- pg_lsclusters
Get-NetTCPConnection -State Listen -LocalPort 8765 -ErrorAction SilentlyContinue
~~~

El clúster `18 main` debe mostrar `down` y el último comando debe volver al indicador sin listar un proceso. Si el clúster ya estaba detenido, basta con verificar su estado. Este apagado conserva las reservas, el índice y las evidencias. Puedes cerrar las ventanas del laboratorio aquí si ya terminaste.

### 2. Iniciar PostgreSQL

**Ventana A · PowerShell · cualquier carpeta.** En la PC de la entrega, empieza aquí si el laboratorio ya está apagado:

~~~powershell
# A | PowerShell | cualquier carpeta de Windows
wsl -d Ubuntu -u root -- pg_ctlcluster 18 main start
wsl -d Ubuntu -- pg_isready -h 127.0.0.1 -p 5432
~~~

Espera la respuesta `accepting connections`. Ahora deja una sesión de Ubuntu abierta en esta ventana para mantener WSL activo:

~~~powershell
# A | PowerShell | cualquier carpeta de Windows
wsl -d Ubuntu
~~~

### 3. Iniciar la API

**Ventana B · abre otra PowerShell.** Sitúate en la carpeta exacta del proyecto. Las comillas y `-LiteralPath` permiten usar los espacios y los corchetes del nombre.

~~~powershell
# B | PowerShell | destino: D:\UMG\QA\[S15] k6 construir, medir y mejorar una API
$proyecto = 'D:\UMG\QA\[S15] k6 construir, medir y mejorar una API'
Set-Location -LiteralPath $proyecto
python .\app.py
~~~

Deja esta ventana abierta aunque la pantalla quede en silencio. En una consola que indique que el puerto 8765 está ocupado, comprueba el estado con el paso 4 antes de intentar otro arranque.

### 4. Comprobar la API

**Ventana C · abre una tercera PowerShell.** Usa esta ventana y esta carpeta para todos los comandos restantes de la práctica:

~~~powershell
# C | PowerShell | destino: D:\UMG\QA\[S15] k6 construir, medir y mejorar una API
$proyecto = 'D:\UMG\QA\[S15] k6 construir, medir y mejorar una API'
Set-Location -LiteralPath $proyecto
Invoke-RestMethod 'http://127.0.0.1:8765/salud'
(Invoke-RestMethod 'http://127.0.0.1:8765/reservas?pagina=1&limite=2').reservas | Format-Table id,recurso,inicio,fin
~~~

Continúa cuando veas `estado ok` y dos filas. Los identificadores dependen de las reservas que existan en ese momento.

### 5. Ejecutar la regresión y seleccionar k6

**Ventana C · PowerShell · raíz del proyecto.** La regresión crea reservas de prueba y comprueba, entre otras cosas, que dos altas simultáneas dejan una sola fila.

~~~powershell
# C | PowerShell | D:\UMG\QA\[S15] k6 construir, medir y mejorar una API
python .\scripts\regresion.py
~~~

Espera `Reservas persistidas: 1; esperado 1` y `Orden estable entre páginas: OK`. Selecciona el mismo k6 2.3.0 utilizado para el informe:

~~~powershell
# C | PowerShell | D:\UMG\QA\[S15] k6 construir, medir y mejorar una API
$env:K6_BIN = Join-Path $env:TEMP 's15-k6\k6-v2.3.0-windows-amd64\k6.exe'
if (-not (Test-Path -LiteralPath $env:K6_BIN)) { throw 'Localiza k6.exe de la versión 2.3.0 y asigna su ruta a $env:K6_BIN.' }
& $env:K6_BIN version
~~~

Si descargaste k6 en otra carpeta, sustituye la primera línea por la ruta real de tu ejecutable. Comprueba que la salida muestre `v2.3.0`.

### 6. Ejecutar humo y leer el resultado en español

**Ventana C · misma sesión PowerShell · raíz del proyecto.** Este bloque mide la versión corregida instalada en la PC de la entrega. Cada medición restablece los datos a la semilla de 80 000 reservas, elimina las altas de prueba y calienta la API. Se elige un número libre para conservar todas las corridas anteriores.

~~~powershell
# C | PowerShell | D:\UMG\QA\[S15] k6 construir, medir y mejorar una API
$numero = 101
while (Test-Path -LiteralPath (Join-Path $proyecto "resultados\despues\humo-$numero")) { $numero++ }
python .\scripts\medir.py despues humo $numero
$salida = $LASTEXITCODE
$carpeta = Join-Path $proyecto "resultados\despues\humo-$numero"
if (Test-Path -LiteralPath "$carpeta\resumen.txt") { Get-Content -LiteralPath "$carpeta\resumen.txt" -Encoding UTF8 }
~~~

El humo dura 20 segundos. El código `0` indica que terminó y cumplió sus umbrales. Para abrir los archivos originales desde esa misma ventana:

~~~powershell
# C | PowerShell | D:\UMG\QA\[S15] k6 construir, medir y mejorar una API
Get-Content -LiteralPath "$carpeta\k6.txt" -Encoding UTF8
Get-Content -LiteralPath "$carpeta\ejecucion.json" -Raw -Encoding UTF8 | ConvertFrom-Json | Select-Object salida,aborto
~~~

Si aparece un aborto, revisa `recursos.csv`. El monitor interrumpe la corrida cuando la CPU del equipo supera el 90 % o quedan menos de 2 GiB disponibles durante 10 segundos. Espera a que el equipo recupere margen, comprueba `/salud` y repite el bloque completo del paso 6 para usar otro número. El resumen de k6 puede quedar vacío si el monitor interrumpe el proceso. Para apagar el sistema al terminar, vuelve al paso 1.

## Repetir la comparación completa antes y después

Esta sección es opcional para quien solo quiera iniciar el sistema. Mantén las ventanas A y B abiertas. Ejecuta los bloques en **C, PowerShell, raíz del proyecto**, tras configurar k6 en el paso 5. Define primero dos funciones de sesión para escoger identificadores libres y detener la secuencia si un comando falla:

~~~powershell
# C | PowerShell | D:\UMG\QA\[S15] k6 construir, medir y mejorar una API
function Ejecutar-Python {
    python @args
    if ($LASTEXITCODE -ne 0) { throw "El comando terminó con código $LASTEXITCODE. Revisa la salida antes de continuar." }
}
function Medir-Corrida($version, $modo) {
    $n = 101
    while (Test-Path -LiteralPath (Join-Path $proyecto "resultados\$version\$modo-$n")) { $n++ }
    Ejecutar-Python .\scripts\medir.py $version $modo $n
}
~~~

**Primero, medir la versión inicial.** Con los clientes de prueba detenidos, quita el índice de la práctica en la base `s15_reservas`. Ejecuta desde PowerShell:

~~~powershell
# C | PowerShell | D:\UMG\QA\[S15] k6 construir, medir y mejorar una API
wsl -d Ubuntu -u postgres -- psql -v ON_ERROR_STOP=1 -d s15_reservas -c 'DROP INDEX IF EXISTS reservas_orden_inicio_id;'
if ($LASTEXITCODE -ne 0) { throw 'Revisa la conexión a PostgreSQL antes de medir.' }
Ejecutar-Python .\scripts\preparar.py restablecer
Ejecutar-Python .\scripts\preparar.py diagnosticar
Ejecutar-Python .\scripts\regresion.py
Medir-Corrida antes humo
1..3 | ForEach-Object { Medir-Corrida antes carga }
Medir-Corrida antes estres
~~~

**Después, aplicar la corrección y repetir las mediciones.** En C y desde la misma carpeta:

~~~powershell
# C | PowerShell | D:\UMG\QA\[S15] k6 construir, medir y mejorar una API
Ejecutar-Python .\scripts\preparar.py restablecer
Ejecutar-Python .\scripts\preparar.py corregir
Ejecutar-Python .\scripts\preparar.py diagnosticar
Ejecutar-Python .\scripts\regresion.py
Medir-Corrida despues humo
1..3 | ForEach-Object { Medir-Corrida despues carga }
Medir-Corrida despues estres
Ejecutar-Python .\scripts\resumir.py
~~~

El escenario de estrés termina con una etapa de recuperación a 2 operaciones/s. Si se aborta una medición, revisa su motivo antes de continuar y verifica la recuperación con humo de la misma versión. Cada corrida escribe en `resultados\<versión>\<escenario>-<número>\`. Las corridas interrumpidas por seguridad se anuncian en la consola y se excluyen de los percentiles. El último comando regenera el archivo derivado `resultados\comparacion.csv`. Los umbrales, la mezcla y el calentamiento se describen en [el plan de pruebas](PLAN.md).

## Contrato
- GET /disponibilidad acepta recurso, inicio y fin con zona horaria. Devuelve disponible. El inicio es inclusivo y el fin exclusivo.
- POST /reservas recibe el mismo objeto JSON. Devuelve 201 y la fila creada; 409 si se traslapa; 400 si el intervalo es inválido; 404 si la sala no existe.
- GET /reservas?pagina=1&limite=10 permite 1–100 filas por página. Orden descendente por inicio y luego por id. Los datos reflejan la base al momento de cada consulta. Si hay escrituras entre dos páginas, su contenido puede moverse.
- Los datos se generan con una fórmula determinista, sin azar ni datos personales: 80 salas × 1 000 intervalos consecutivos de una hora, ocupados durante los primeros 30 minutos.

## Instalación inicial en otro equipo


Se probó con Python 3.12 para Windows, PostgreSQL 18.6 en Ubuntu bajo WSL2 y k6 2.3.0 para Windows. Flask despacha las rutas, Waitress sirve HTTP local con ocho hilos y psycopg usa un pool de dos a ocho conexiones. PostgreSQL aplica la regla de exclusión de horarios incluso ante escrituras concurrentes. La separación permite observar los procesos de API, generador y base. Sin contenedores. Solo la API escucha en 127.0.0.1:8765.

### 1. Ubicar el proyecto en Windows

En la PC de la entrega, abre **PowerShell** y ejecuta desde cualquier carpeta:

~~~powershell
# PowerShell | destino en la PC de la entrega: D:\UMG\QA\[S15] k6 construir, medir y mejorar una API
$proyecto = 'D:\UMG\QA\[S15] k6 construir, medir y mejorar una API'
Set-Location -LiteralPath $proyecto
Get-Item -LiteralPath "$proyecto\app.py", "$proyecto\requirements.txt" | Select-Object Name
~~~

Esa es la **raíz del proyecto**. Usa `-LiteralPath` porque el nombre incluye corchetes. Si estás en otro equipo, puedes clonar desde **PowerShell**, empezando en tu carpeta de usuario:

~~~powershell
# PowerShell | clonar desde $HOME y entrar en $HOME\reservas-s15
Set-Location -LiteralPath $HOME
git clone https://github.com/mchiroyl/construir-medir-y-mejorar-una-API.git reservas-s15
$proyecto = Join-Path $HOME 'reservas-s15'
Set-Location -LiteralPath $proyecto
~~~

En ese caso, usa la carpeta `reservas-s15` que acabas de crear en cada bloque que indique «raíz». Las rutas `scripts\`, `k6\`, `db\` y `resultados\` parten de esa raíz. El ejecutor busca allí el script k6 y guarda allí los resultados.

### 2. Iniciar PostgreSQL — terminal 1, Ubuntu en WSL2

Abre **Ubuntu**. Puedes empezar en cualquier carpeta de Linux. La instalación de paquetes se hace una vez. En los siguientes arranques basta con iniciar PostgreSQL y comprobar que acepta conexiones:

~~~bash
# Ubuntu | directorio personal de Linux (~)
cd ~
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
pg_isready -h 127.0.0.1 -p 5432
~~~

Solo la primera vez, si el rol y la base aún no existen, ejecuta en **la misma terminal Ubuntu**, desde `~`:

~~~bash
# Ubuntu | directorio personal de Linux (~)
sudo -u postgres createuser --pwprompt s15
sudo -u postgres createdb --owner=s15 s15_reservas
~~~

Deja Ubuntu abierto durante la práctica.

### 3. Preparar Python y los datos — terminal 2, PowerShell

Abre otra terminal en Windows. En la **raíz del proyecto**, comprueba Python e instala las dependencias una vez. Se requiere Python 3.12 en Windows:

~~~powershell
# B | PowerShell | raíz de la copia local ($proyecto)
$proyecto = Join-Path $HOME 'reservas-s15'  # En otro equipo, si clonaste en el paso 1.
Set-Location -LiteralPath $proyecto
python --version
python -m pip install -r .\requirements.txt
~~~

En esta misma raíz, la aplicación y los scripts leen la conexión desde el archivo local `.dsn`, excluido de Git. Si ya está configurado, continúa al siguiente bloque. Para crearlo por primera vez en **PowerShell**, introduce la contraseña del rol `s15` cuando se solicite:

~~~powershell
# B | PowerShell | raíz de la copia local ($proyecto)
$credencial = Get-Credential -UserName s15 -Message 'Contraseña del rol s15 de PostgreSQL'
$claveUri = [Uri]::EscapeDataString($credencial.GetNetworkCredential().Password)
Set-Content -LiteralPath "$proyecto\.dsn" -Encoding ascii -Value "postgresql://s15:$claveUri@127.0.0.1:5432/s15_reservas"
~~~

Si prefieres configurar `DATABASE_URL`, esa variable tiene prioridad sobre `.dsn` y debe estar disponible en **ambas** terminales PowerShell. Solo para una **base vacía**, carga las 80 salas y las 80 000 reservas desde **PowerShell, raíz del proyecto**:

~~~powershell
# B | PowerShell | raíz de la copia local ($proyecto)
python .\scripts\preparar.py instalar
~~~

Al terminar en una base nueva, ejecuta la comparación completa para medir la línea base y aplicar el índice, o aplica la versión corregida con `python .\scripts\preparar.py corregir` desde PowerShell en la raíz. Para iniciar la API sigue el paso 3. Descarga k6 desde las [publicaciones oficiales](https://github.com/grafana/k6/releases/tag/v2.3.0).

## Evidencias para revisión
- [Guion para grabar el video](GUION-VIDEO.md) con narración, tiempos e indicaciones de pantalla.
- Informe editable: [Informe S15.docx](./Informe%20S15.docx). Video narrado: [descargar MP4](https://github.com/mchiroyl/construir-medir-y-mejorar-una-API/releases/download/entrega/Video-S15.mp4).
- Resultados completos: [antes](./resultados/antes), [después](./resultados/despues) y [comparación por corrida y fase](./resultados/comparacion.csv).
- Diagnóstico y regresión: resultados/plan-antes.txt, resultados/plan-despues.txt y resultados/regresion-*.txt.
- En la primera preparación se corrigió la identificación del socket de Windows antes de arrancar k6. El humo inicial válido es humo-2. En ese humo y en carga-1 inicial faltan los contadores de PostgreSQL; CPU del host, API, generador y memoria sí se recogieron. Los demás muestreos incluyen los contadores de la base.
- Las capturas del cliente de demostración provienen de peticiones HTTP reales. Las demás capturas presentan extractos de los originales o la tabla reconstruida de las series. Para rehacerlas, instalar Pillow y playwright para Python, disponer de Edge, restablecer la semilla y ejecutar scripts/capturas.py desde la raíz.
