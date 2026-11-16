# Guion para grabar la demostración de la API de reservas

**Duración prevista: 2 min 45 s. Máximo de la entrega: 3 min.** Lee solo las citas. Las palabras en negrita indican dónde hacer una pausa o señalar la pantalla. Ensaya con el cronómetro antes de grabar.

## Preparar la pantalla

Inicia PostgreSQL y la API siguiendo los pasos 2 y 3 del [README](README.md). En la ventana C deja preparado este bloque. Durante la grabación ejecuta las dos consultas y deja visibles sus respuestas:

```powershell
# Ventana C | Windows PowerShell 5.1 | raíz del proyecto en la PC de la entrega
$proyecto = 'D:\UMG\QA\[S15] k6 construir, medir y mejorar una API'
Set-Location -LiteralPath $proyecto
Invoke-RestMethod 'http://127.0.0.1:8765/salud'
(Invoke-RestMethod 'http://127.0.0.1:8765/reservas?pagina=1&limite=2').reservas | Format-Table id,recurso,inicio,fin
```

Abre de antemano las evidencias enlazadas en cada escena. En Word, deja preparada la página 3 de [Informe S15.docx](Informe%20S15.docx). Amplía la letra hasta que se distingan las cifras en la grabación. Los resultados citados corresponden a las corridas originales del informe.

### 0:00–0:25 · Mostrar la aplicación

**En pantalla:** Ejecuta las dos consultas. Señala primero `ok` y después las dos filas de la página. Cambia a la [captura de la reserva](evidencias/01-api.png) y señala el 201 y el 409.

> Soy Marvin Chiroy Lopreto. Esta API permite consultar disponibilidad, reservar una sala y listar reservas por páginas. Aquí se ven dos reservas que vienen de **PostgreSQL**. En esta captura, la primera solicitud reservó la sala y recibió un 201. Al pedir otra vez el mismo horario, la API respondió 409: ya estaba ocupado.

### 0:25–1:00 · Explicar una prueba de k6

**En pantalla:** Muestra la demanda en el [plan previo](PLAN.md). Luego abre [la segunda corrida de carga inicial](resultados/antes/carga-2/k6.txt). Señala en `THRESHOLDS` el límite del listado y en `TOTAL RESULTS` la cantidad de checks correctos.

> Antes de medir, fijé una demanda de **cinco operaciones por segundo**. De cada veinte, doce consultaban disponibilidad, cinco pedían una página y tres creaban una reserva. Primero ejecuté humo para comprobar las rutas. Luego repetí la **carga sostenida** durante un minuto, tres veces por versión. Un check verificaba que la página trajera diez filas en orden. Para aprobar, el **percentil 95** de lectura debía quedar por debajo de 300 milisegundos.

### 1:00–1:32 · Mostrar el hallazgo y la corrección

**En pantalla:** Abre los planes SQL [antes](resultados/plan-antes.txt) y [después](resultados/plan-despues.txt). Señala `Seq Scan` y `rows=80000` en el primero. En el segundo señala `Index Scan` y `rows=20`. También puedes usar la [captura comparativa](evidencias/03-sql.png).

> El listado cumplía el umbral, pero era la lectura más lenta. Al revisar el **plan de ejecución**, encontré que PostgreSQL recorría ochenta mil reservas y las ordenaba para entregar diez. Mi hipótesis fue que un **índice** con el mismo orden de la consulta evitaría ese recorrido. Después del cambio, el motor leyó veinte filas: saltó las diez de la primera página y devolvió las diez siguientes.

### 1:32–2:03 · Comparar las tres repeticiones

**En pantalla:** Muestra la página 3 del Word. Señala las tres corridas de «El listado en cada repetición» y luego los valores **12,88** y **2,93** de la fila «Listado». Esos valores resumen tres corridas por versión.

> Repetí la prueba con la misma semilla de datos, el mismo calentamiento, la misma demanda y los mismos umbrales. Comparé el **p95 del listado**: indica el tiempo dentro del cual terminó aproximadamente el 95 % de esas solicitudes. La mediana de las tres corridas bajó de **12,88 a 2,93 milisegundos**, una reducción del **77,24 %**. En la tabla se ve cuánto varió cada repetición.

### 2:03–2:20 · Verificar la regla de negocio

**En pantalla:** En la [regresión posterior](resultados/regresion-despues.txt), señala «Dos altas concurrentes» y después «Reservas persistidas».

> La mejora también tenía que conservar la regla de negocio. En la **regresión funcional**, dos solicitudes intentaron reservar el mismo horario al mismo tiempo. Una obtuvo 201 y la otra 409. La consulta directa a PostgreSQL confirmó que quedó **una sola reserva**.

### 2:20–2:45 · Explicar recuperación y límites

**En pantalla:** Muestra la [tabla de estrés y recuperación](evidencias/05-estres.png). Señala el pico de 15 operaciones por segundo y la última fila a 2. Termina mostrando las carpetas [antes y después](resultados).

> En el **estrés progresivo**, la demanda subió hasta quince operaciones por segundo y volvió a dos para observar la **recuperación**. Con el índice, el p95 global terminó en **3,65 milisegundos**. En las pruebas originales hubo cero iteraciones descartadas. Dentro de este rango no observé saturación. Los resultados originales y los recursos del equipo están disponibles en el repositorio.
