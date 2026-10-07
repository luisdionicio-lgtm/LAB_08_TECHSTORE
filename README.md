# TechStore inventario local con Docker

TechStore es una aplicación web de inventario tecnológico construida sobre la arquitectura local del GLAB 07. La solución conserva Nginx, tres instancias Flask y PostgreSQL, pero no utiliza servicios AWS.

Consulta [GUIA_LAB07.md](GUIA_LAB07.md) para seguir la ejecución, las pruebas y las nueve capturas recomendadas para el informe.

## Arquitectura

```text
Navegador
   |
   v
Nginx :8080
   |
   +-- backend-1 :8081
   +-- backend-2 :8082
   +-- backend-3 :8083
              |
              v
        PostgreSQL 16
```

Nginx distribuye las solicitudes mediante Round Robin. Las tres instancias ejecutan el mismo código y comparten PostgreSQL, por lo que el inventario permanece consistente sin importar qué backend procese cada operación. La cabecera `X-Backend-Server` y el pie de la interfaz permiten observar el balanceo.

## Funcionalidades

- Inicio de sesión local.
- Inicio de sesión con GitHub mediante OAuth 2.0.
- Token JWT interno válido por 60 minutos para ambos métodos de acceso.
- Bloqueo temporal de 15 minutos después de tres intentos fallidos.
- Tienda y rol asignados a cada usuario.
- Panel de inventario con productos, unidades, alertas y valor acumulado.
- Registro, edición y eliminación de productos tecnológicos.
- SKU único, marca, categoría, precio, stock y stock mínimo.
- Estados disponible, stock bajo, agotado e inactivo.
- Búsqueda y filtros inmediatos en el navegador.
- Datos iniciales de laptops, monitores, redes, almacenamiento, accesorios y móviles.
- Producto destacado PC Gamer Nebula RTX 4070 e imagen referencial de una estación gamer.
- Diseño adaptable para escritorio y dispositivos móviles.

## Ejecución

Requisitos: Docker Desktop con Docker Compose.

```powershell
docker compose up --build -d
docker compose ps
```

Abra `http://localhost:8080` e ingrese con:

- Usuario: `admin`
- Contraseña: `admin123`

El acceso acepta el nombre `admin` o el correo `admin@techstore.local`. La cuenta pertenece a `TechStore Lima Centro`.

## Configurar GitHub OAuth

Registre una OAuth App en GitHub y complete estos valores:

- Application name: `TechStore Local Luis`
- Homepage URL: `http://localhost:8080`
- Application description: `Sistema local de inventario tecnológico con autenticación GitHub, JWT y Docker.`
- Redirect URI: `http://localhost:8080/auth/github/callback`
- Allow wildcard matching: desactivado.
- Enable Device Flow: desactivado.
- Expire user access tokens: activado.

Después de registrar la aplicación, copie el Client ID y genere un Client Secret. Guárdelos únicamente en `.env`:

```dotenv
GITHUB_CLIENT_ID=su_client_id
GITHUB_CLIENT_SECRET=su_client_secret
GITHUB_REDIRECT_URI=http://localhost:8080/auth/github/callback
GITHUB_DEFAULT_STORE=TechStore Lima Centro
```

Reconstruya el contenedor para cargar las variables:

```powershell
docker compose up --build -d
```

## Verificar el balanceo

```powershell
1..6 | ForEach-Object { Invoke-RestMethod http://localhost:8080/health }
```

Las respuestas deben alternar entre `backend-1`, `backend-2` y `backend-3`.

## Comandos útiles

```powershell
# Ver registros
docker compose logs -f app

# Validar Nginx
docker compose exec app nginx -t

# Detener sin borrar los datos
docker compose down

# Detener y eliminar la base de datos local
docker compose down -v
```

## Alcance académico

La aplicación demuestra balanceo de carga local, persistencia compartida, contenerización y un CRUD operativo. AWS queda fuera del alcance de esta versión.
