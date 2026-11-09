# Reservas de salas con PostgreSQL y k6

Proyecto individual de Marvin Chiroy Lopreto, carné 2890-22-20336. El informe editable y el video se entregan en este repositorio. El protocolo previo está en PLAN.md. Los archivos originales se encuentran en resultados/ y las capturas en evidencias/.

## Preparar el laboratorio
Se probó con Python 3.12 para Windows, PostgreSQL 18.6 en Ubuntu bajo WSL2 y k6 2.3.0 para Windows. Flask despacha las rutas, Waitress sirve HTTP local con ocho hilos y psycopg usa un pool de dos a ocho conexiones. PostgreSQL aplica la regla de exclusión de horarios incluso ante escrituras concurrentes. La separación permite observar los procesos de API, generador y base. Sin contenedores. Solo la API escucha en 127.0.0.1:8765.

1. Clonar este repositorio y entrar al directorio. Para reconstruir únicamente el estado inicial usar una copia en la etiqueta `antes`. La semilla y el esquema inicial también están disponibles en la rama principal.
2. Instalar Python 3.12, k6 y PostgreSQL con el módulo btree_gist. Para repetir el muestreo de recursos, ejecutar Python y k6 en Windows y PostgreSQL en una distribución WSL2 llamada Ubuntu. En Ubuntu: `sudo apt install postgresql postgresql-contrib`; iniciar PostgreSQL con `sudo service postgresql start`. Mantener Ubuntu activo durante la práctica. Comprobar que PostgreSQL escuche localmente en 5432. Descargar k6 desde las publicaciones oficiales de Grafana, agregarlo al PATH o asignar su ruta completa a la variable K6_BIN. Verificar con `k6 version`.
3. Crear una base exclusiva. En Ubuntu ejecutar `sudo -u postgres createuser --pwprompt s15` y `sudo -u postgres createdb --owner=s15 s15_reservas`. Guardar la URI de conexión en la variable de sesión DATABASE_URL o en un archivo local .dsn (excluido de Git). Formato: `postgresql://s15:CLAVE@127.0.0.1:5432/s15_reservas`. Codificar los caracteres reservados de la contraseña para una URI.
4. Desde PowerShell, instalar las dependencias y el conjunto ficticio. En una base vacía ejecutar:

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/preparar.py instalar
python app.py
~~~

En una segunda consola activar el mismo entorno y verificar `Invoke-RestMethod http://127.0.0.1:8765/salud`. Instalar se ejecuta una vez por base vacía. Para volver al conjunto inicial durante las pruebas, detener los clientes y ejecutar `python scripts/preparar.py restablecer`. Este comando elimina las altas del experimento, conserva las 80 000 reservas originales y reinicia el próximo ID en 80001. Para restablecer el esquema inicial tras la corrección quitar únicamente el índice de la práctica con `DROP INDEX IF EXISTS reservas_orden_inicio_id` en s15_reservas.

## Contrato
- GET /disponibilidad acepta recurso, inicio y fin con zona horaria. Devuelve disponible. El inicio es inclusivo y el fin exclusivo.
- POST /reservas recibe el mismo objeto JSON. Devuelve 201 y la fila creada; 409 si se traslapa; 400 si el intervalo es inválido; 404 si la sala no existe.
- GET /reservas?pagina=1&limite=10 permite 1–100 filas por página. Orden descendente por inicio y luego por id. Los datos reflejan la base al momento de cada consulta. Si hay escrituras entre dos páginas, su contenido puede moverse.
- Los datos se generan con una fórmula determinista, sin azar ni datos personales: 80 salas × 1 000 intervalos consecutivos de una hora, ocupados durante los primeros 30 minutos.

## Repetir el experimento
Ejecutar desde la raíz con la API activa. Usar un nuevo número de corrida si la carpeta ya existe: el ejecutor protege los originales. Para una reproducción limpia, clonar en otra carpeta y mover la carpeta resultados original a otra ubicación antes de medir. El ejecutor prepara los datos y calienta cada vez. No ejecutar pruebas simultáneas.
 
~~~powershell
python scripts/regresion.py
python scripts/medir.py antes humo 1
1..3 | ForEach-Object { python scripts/medir.py antes carga $_ }
python scripts/medir.py antes estres 1
python scripts/preparar.py restablecer
python scripts/preparar.py diagnosticar
python scripts/preparar.py corregir
python scripts/preparar.py diagnosticar
python scripts/regresion.py
python scripts/medir.py despues humo 1
1..3 | ForEach-Object { python scripts/medir.py despues carga $_ }
python scripts/medir.py despues estres 1
python scripts/resumir.py
~~~

El script k6/reservas.js contiene los tres escenarios. El ejecutor aplica el límite de recursos del host, conserva el log, el código de salida, la serie JSON comprimida y las muestras de recursos aproximadamente cada dos segundos. Tras un aborto por seguridad esperar hasta recuperar el margen de CPU/RAM, revisar /salud y ejecutar humo con un nuevo número. En k6.txt se encuentra la evaluación de thresholds; comparacion.csv se reconstruye a partir de las series. En CPU de proceso, 100 % equivale a un procesador lógico; las cifras de RSS de PostgreSQL pueden contar páginas compartidas más de una vez. Las tasas por fase en el CSV se calculan con su duración nominal. k6 puede iniciar una iteración junto al límite de una etapa.

Documentación del ejecutor y criterios: https://grafana.com/docs/k6/latest/ y https://grafana.com/docs/k6/latest/using-k6/thresholds/

## Evidencias para revisión
- Informe editable: [Informe S15.docx](./Informe%20S15.docx). Video narrado: [descargar MP4](https://github.com/mchiroyl/construir-medir-y-mejorar-una-API/releases/download/entrega/Video-S15.mp4).
- Resultados completos: [antes](./resultados/antes), [después](./resultados/despues) y [comparación por corrida y fase](./resultados/comparacion.csv).
- Diagnóstico y regresión: resultados/plan-antes.txt, resultados/plan-despues.txt y resultados/regresion-*.txt.
- En la primera preparación se corrigió la identificación del socket de Windows antes de arrancar k6. El humo inicial válido es humo-2. En ese humo y en carga-1 inicial faltan los contadores de PostgreSQL; CPU del host, API, generador y memoria sí se recogieron. Los demás muestreos incluyen los contadores de la base.
- Las capturas del cliente de demostración provienen de peticiones HTTP reales. Las demás capturas presentan extractos de los originales o la tabla reconstruida de las series. Para rehacerlas, instalar Pillow y playwright para Python, disponer de Edge, restablecer la semilla y ejecutar scripts/capturas.py desde la raíz.
