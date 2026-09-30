# Guía de capturas Parte A GLAB 07

Esta secuencia reúne evidencias suficientes para demostrar la aplicación monolítica con LOGIN, CRUD, PostgreSQL y balanceo local mediante Nginx.

## Preparación

Abra PowerShell dentro de la carpeta `Lab07_nube` y ejecute:

```powershell
docker compose up --build -d
docker compose ps
```

Espere hasta que los servicios `app` y `db` aparezcan como `healthy`. Mantenga el navegador en `http://localhost:8080` y use un zoom de 90 % o 100 %.

## Captura 1 Estado de los contenedores

Ejecute:

```powershell
docker compose ps
```

La captura debe mostrar:

- Contenedor `app` saludable.
- Contenedor `db` saludable.
- Puertos `8080`, `8081`, `8082` y `8083` publicados.

## Captura 2 Pantalla de LOGIN

1. Abra `http://localhost:8080/login`.
2. Capture la pantalla completa antes de ingresar.
3. Verifique que se vea el diagrama Cliente → Nginx → tres backends y el indicador de infraestructura disponible.

Esta imagen demuestra la existencia del LOGIN y presenta la arquitectura local.

## Captura 3 Creación de una tarea

1. Ingrese con `admin` y `admin123`.
2. Pulse `Nueva tarea`.
3. Complete:
   - Título: `Validar balanceo Round Robin`
   - Descripción: `Comprobar la distribución de solicitudes entre los tres backends locales.`
4. Capture el formulario lleno antes de guardar.
5. Pulse `Guardar tarea`.

Esta imagen demuestra la operación CREATE.

## Captura 4 Listado y lectura del CRUD

1. Cree dos tareas adicionales para que el tablero tenga contenido:
   - `Verificar PostgreSQL`
   - `Documentar evidencias`
2. Deje al menos una tarea pendiente y una completada.
3. Capture el tablero completo mostrando:
   - Contadores de tareas.
   - Porcentaje de progreso.
   - Tarjetas pendientes y completadas.
   - Indicador del backend en el pie de página.

Esta imagen demuestra la operación READ y la interfaz principal.

## Captura 5 Edición de una tarea

1. Pulse `Editar` en una tarjeta.
2. Cambie la descripción y active `Marcar como completada`.
3. Capture el formulario antes de guardar.
4. Guarde y capture el mensaje de confirmación en el tablero.

Esta imagen demuestra la operación UPDATE.

## Captura 6 Eliminación de una tarea

1. Pulse `Eliminar` en una tarea de prueba.
2. Capture el cuadro de confirmación del navegador.
3. Confirme y capture el tablero sin el registro y con el mensaje de eliminación.

Esta imagen demuestra la operación DELETE.

## Captura 7 Balanceo Round Robin

En PowerShell ejecute:

```powershell
1..12 | ForEach-Object { (Invoke-RestMethod http://localhost:8080/health).backend } | Group-Object | Select-Object Name, Count
```

La salida esperada es una distribución uniforme:

```text
backend-1  4
backend-2  4
backend-3  4
```

Capture el comando y el resultado completo.

## Captura 8 Configuración y validación de Nginx

Abra `nginx/nginx.conf` en Visual Studio Code y capture el bloque `upstream backend_pool` con los tres servidores. Después ejecute:

```powershell
docker compose exec app nginx -t
```

Capture el mensaje `syntax is ok` y `test is successful`.

## Captura 9 PostgreSQL

Ejecute:

```powershell
docker compose exec db psql -U lab07 -d lab07 -c "SELECT id, title, completed FROM tasks ORDER BY id;"
```

Capture la consulta y sus registros. Esto demuestra que el CRUD persiste la información en PostgreSQL.

## Captura 10 Prueba automatizada final

Ejecute:

```powershell
.\scripts\verify-local.ps1
```

Capture la distribución 4/4/4 y el mensaje que confirma el LOGIN y las cuatro operaciones del CRUD.

## Orden recomendado en el informe

1. Arquitectura y contenedores.
2. LOGIN.
3. CREATE.
4. READ.
5. UPDATE.
6. DELETE.
7. Balanceo Round Robin.
8. Validación de Nginx.
9. Persistencia en PostgreSQL.
10. Prueba automatizada.

Debajo de cada imagen añada una descripción breve que explique qué requisito demuestra; no coloque capturas sin contexto.
