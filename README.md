# GLAB 07 Parte A Aplicacion local con balanceo de carga

Este proyecto implementa la Parte A del GLAB 07 como una aplicacion monolitica sencilla en Docker: inicio de sesion y CRUD de tareas en un unico codigo, tres procesos identicos del monolito y Nginx para distribuir las solicitudes. PostgreSQL se ejecuta en un contenedor independiente para mantener los datos persistentes y compartidos.

## Arquitectura local

```text
Navegador o curl
       |
       v
Nginx :8080 (Round Robin)
       |
       +---- backend-1 :8081
       +---- backend-2 :8082
       +---- backend-3 :8083
                    |
                    v
              PostgreSQL
```

Nginx y las tres instancias de la aplicacion viven en el contenedor `app`; PostgreSQL vive en el contenedor `db`. Nginx escucha en el puerto 80 interno y se publica como `http://localhost:8080` para evitar conflictos en Windows; se puede usar el puerto 80 estableciendo `NGINX_PORT=80`.

## Ejecucion

Requisitos: Docker Desktop con Docker Compose.

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```

Abra `http://localhost:8080` e ingrese con:

- Usuario: `admin`
- Contrasena: `admin123`

La pantalla permite crear, listar, editar, marcar como completadas y eliminar tareas. El pie de cada respuesta identifica el backend que la atendio.

## Verificacion de la Parte A

La secuencia completa de evidencias está documentada en [`GUIA_CAPTURAS.md`](GUIA_CAPTURAS.md).

Ejecute la prueba automatizada desde PowerShell:

```powershell
.\scripts\verify-local.ps1
```

La primera prueba realiza doce solicitudes a `/health` y debe mostrar respuestas de `backend-1`, `backend-2` y `backend-3`. La segunda inicia sesion y crea un registro mediante Nginx para comprobar el LOGIN y el CRUD.

Tambien puede probar cada backend directamente:

```powershell
Invoke-RestMethod http://localhost:8081/health
Invoke-RestMethod http://localhost:8082/health
Invoke-RestMethod http://localhost:8083/health
```

## Comandos utiles

```powershell
# Ver registros
docker compose logs -f app

# Validar la configuracion de Nginx
docker compose exec app nginx -t

# Detener el entorno conservando los datos
docker compose down

# Eliminar tambien la base de datos del laboratorio
docker compose down -v
```

## Parte B en AWS

La infraestructura de la Parte B se implementó en AWS `us-east-2` con dos EC2 en zonas distintas y un Application Load Balancer. La secuencia de evidencias y los comandos de comprobación están en [`GUIA_CAPTURAS_PARTE_B.md`](GUIA_CAPTURAS_PARTE_B.md).
