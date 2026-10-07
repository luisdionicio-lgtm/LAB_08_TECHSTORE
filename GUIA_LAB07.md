# Guía de ejecución y evidencias — Lab07 TechStore

## 1. Objetivo del laboratorio

Implementar una tienda tecnológica local con autenticación básica, Google y GitHub OAuth, emisión de JWT, bloqueo después de tres credenciales incorrectas y un inventario compartido. La arquitectura usa Docker Compose, Nginx como balanceador Round Robin, tres procesos Flask/Gunicorn y PostgreSQL. No se despliega ningún recurso en AWS; únicamente se conserva el patrón arquitectónico distribuido.

## 2. Preparación

1. Abrir Docker Desktop y esperar a que indique que el motor está activo.
2. Abrir en Visual Studio Code la carpeta `C:\Users\Luis Angel\Documents\ChatGPT\Lab07_nube`.
3. Abrir una terminal integrada en esa carpeta.
4. Confirmar que el archivo `.env` existe. Contiene secretos locales y está excluido por `.gitignore`; nunca debe aparecer en una captura ni subirse a Git.
5. En GitHub, la OAuth App debe usar:
   - Homepage URL: `http://localhost:8080`
   - Authorization callback URL: `http://localhost:8080/auth/github/callback`
6. En Google Cloud, el cliente OAuth de tipo Aplicación web debe usar:
   - Origen autorizado: `http://localhost:8080`
   - URI de redireccionamiento: `http://localhost:8080/auth/google/callback`

## 3. Construcción y ejecución

Ejecutar:

```powershell
docker compose up --build -d
docker compose ps
```

El segundo comando debe mostrar `app` y `db` en ejecución y saludables. La aplicación queda disponible en `http://localhost:8080`.

### Captura 1 — Contenedores saludables

- Mostrar la terminal completa con `docker compose ps`.
- Deben verse los servicios `app` y `db`, el estado `running` y la condición `healthy`.
- No mostrar el contenido de `.env`.
- Pie sugerido: **Figura 1. Servicios de TechStore ejecutándose localmente con Docker Compose.**

## 4. Evidencia de la arquitectura

Abrir `http://localhost:8080/login`. La pantalla explica el flujo Navegador → Nginx → tres backends → PostgreSQL y declara que no se usa AWS.

### Captura 2 — Login y arquitectura

- Capturar la ventana completa del navegador.
- Deben verse el formulario, el botón de GitHub, la referencia PC gamer y el diagrama local.
- Evitar que aparezcan marcadores, contraseñas guardadas o datos personales del navegador.
- Pie sugerido: **Figura 2. Acceso de TechStore y arquitectura local balanceada.**

## 5. Autenticación básica y JWT

Usar las cuentas demostrativas:

| Perfil | Usuario | Contraseña | Permiso principal |
|---|---|---|---|
| Administrador del Sistema | `admin` | `Admin123!` | Control total y gestión de usuarios y roles |
| Gerente de Tienda | `gerente` | `Gerente123!` | Gestiona productos de su tienda |
| Empleado de Ventas | `ventas` | `Ventas123!` | Consulta productos y actualiza únicamente el stock |
| Auditor | `auditor` | `Auditor123!` | Consulta global en modo de solo lectura |

Al validar las credenciales, Flask genera un JWT con duración de 60 minutos y lo guarda en una cookie `HttpOnly`. Después redirige al inventario de la tienda asignada `TechStore Lima Centro`.

### Captura 3 — Login básico correcto

- Ingresar con la cuenta demostrativa.
- Capturar el inventario inmediatamente después del acceso.
- Deben verse la tienda asignada, la leyenda “Sesión básica protegida con JWT”, las métricas y el backend que atendió la solicitud.
- Pie sugerido: **Figura 3. Sesión básica validada y protegida mediante JWT.**

## 6. Bloqueo al tercer intento

1. Cerrar sesión.
2. Escribir `admin` y una contraseña incorrecta.
3. Repetir la operación tres veces.
4. En el tercer intento debe aparecer: `Cuenta bloqueada durante 1 minuto por tres intentos fallidos.`

### Captura 4 — Protección ante intentos fallidos

- Tomar la captura justo después del tercer fallo.
- Mostrar el aviso completo y el formulario.
- Pie sugerido: **Figura 4. Bloqueo temporal activado en el tercer intento fallido.**

Para continuar la demostración sin esperar 1 minuto, ejecutar:

```powershell
docker compose exec -T db psql -U lab07 -d lab07 -c "UPDATE users SET failed_attempts=0, locked_until=NULL WHERE username='admin';"
```

## 7. Autenticación con GitHub

1. Seleccionar **Ingresar con GitHub**.
2. GitHub mostrará la autorización de la OAuth App.
3. Autorizar la aplicación.
4. GitHub devolverá el navegador a `/auth/github/callback`.
5. TechStore crea o actualiza el usuario local, asigna la tienda y emite su propio JWT.

### Captura 5 — Autorización GitHub

- Capturar la pantalla oficial de autorización de GitHub.
- Mostrar el nombre de la aplicación y los permisos solicitados.
- Ocultar correo, nombre de cuenta u otros datos personales si aparecen.
- Nunca mostrar Client Secret, tokens ni DevTools.
- Pie sugerido: **Figura 5. Autorización de acceso mediante GitHub OAuth 2.0.**

### Captura 6 — Retorno desde GitHub

- Capturar el inventario después de autorizar.
- La cabecera debe indicar `Sesión GitHub OAuth protegida con JWT`.
- Pie sugerido: **Figura 6. Usuario autenticado con GitHub y sesión interna JWT.**

## 7A. Autenticación con Google

1. Seleccionar **Ingresar con Google**.
2. Elegir una cuenta en la pantalla oficial de Google.
3. Autorizar el acceso al perfil básico y correo.
4. Google devuelve el navegador a `/auth/google/callback`.
5. TechStore valida el estado OAuth, exige un correo verificado, crea o actualiza el usuario y emite su JWT interno.

### Captura 6A — Selección o autorización de Google

- Mostrar la pantalla oficial de Google y el nombre de la aplicación.
- Ocultar correo, foto u otros datos personales si fuera necesario.
- Nunca mostrar Client Secret, access token, JWT ni contenido de `.env`.
- Pie sugerido: **Figura 6A. Autenticación mediante Google OAuth y OpenID Connect.**

### Captura 6B — Retorno desde Google

- Capturar el inventario después del retorno.
- Debe aparecer `Sesión Google OAuth protegida con JWT`.
- Pie sugerido: **Figura 6B. Sesión interna JWT generada después del acceso con Google.**

## 8. CRUD del inventario

1. Seleccionar **Registrar producto**.
2. Usar datos tecnológicos reconocibles, por ejemplo:
   - SKU: `TS-GPU-508`
   - Nombre: `Tarjeta gráfica RTX 5080`
   - Marca: `NVIDIA`
   - Categoría: `Componentes`
   - Stock: `6`
   - Stock mínimo: `3`
   - Precio: `6299.00`
3. Guardar el producto.
4. Buscarlo por SKU o nombre.
5. Editar el stock para demostrar actualización.
6. La eliminación puede demostrarse al final con un registro creado solo para pruebas.

### Captura 7 — Registro de producto

- Capturar el formulario completamente llenado antes de guardar.
- No usar datos personales.
- Pie sugerido: **Figura 7. Registro de un producto tecnológico en el inventario.**

### Captura 8 — Inventario compartido

- Capturar el producto nuevo dentro de la tabla.
- Mostrar las métricas, el buscador, su estado de stock y el identificador del backend en el pie.
- Actualizar la página varias veces permite observar distintos backends sin perder los datos, demostrando la persistencia común.
- Pie sugerido: **Figura 8. Producto persistido en PostgreSQL y visible desde los backends balanceados.**

## 8A. Usuarios y control de acceso por roles

Inicie sesión como `admin` con `Admin123!` y seleccione **Usuarios y roles**. El Administrador puede registrar cuentas y cambiar el perfil o la tienda asignada.

### Captura 8A — Administración de usuarios

- Mostrar el formulario de registro y la tabla con las cuatro cuentas.
- Deben verse Administrador del Sistema, Gerente de Tienda, Empleado de Ventas y Auditor.
- Pie sugerido: **Figura 8A. Gestión centralizada de cuentas, perfiles y tiendas por el Administrador.**

Pruebe después cada perfil cerrando sesión:

- `gerente / Gerente123!`: puede registrar, editar y eliminar productos de TechStore Lima Centro; no accede a Usuarios y roles.
- `ventas / Ventas123!`: solo ve la acción **Actualizar stock**; el precio y los datos comerciales permanecen protegidos.
- `auditor / Auditor123!`: consulta el inventario completo y cada fila indica **Solo lectura**.

### Captura 8B — Perfil Gerente

- Mostrar el inventario con **Registrar producto**, **Editar** y **Eliminar**.
- Pie sugerido: **Figura 8B. Gerente gestionando productos correspondientes a su tienda.**

### Captura 8C — Perfil Ventas

- Abrir **Actualizar stock** y mostrar que solo la existencia es editable.
- Pie sugerido: **Figura 8C. Empleado de Ventas actualizando existencias sin permiso para modificar precios.**

### Captura 8D — Perfil Auditor

- Mostrar el inventario con la etiqueta **Solo lectura** y sin botones de modificación.
- Pie sugerido: **Figura 8D. Auditor consultando el inventario sin permisos de modificación.**

## 9. Evidencia de Round Robin

Actualizar el navegador varias veces y observar el texto `Solicitud atendida por backend-N` al pie. También puede ejecutarse:

```powershell
1..9 | ForEach-Object { (Invoke-WebRequest http://localhost:8080/health).Content }
```

### Captura 9 — Balanceo de carga

- Mostrar varias respuestas consecutivas con identificadores de backend diferentes.
- Pie sugerido: **Figura 9. Nginx distribuye solicitudes entre tres instancias mediante Round Robin.**

## 10. Cierre y lista de comprobación

- Login básico válido.
- JWT de 60 minutos en cookie `HttpOnly`.
- Bloqueo en el tercer intento y duración de 1 minuto.
- Inicio de sesión mediante GitHub OAuth.
- Inicio de sesión mediante Google OAuth y OpenID Connect.
- Tienda `TechStore Lima Centro` asignada.
- Crear, listar, buscar, editar y eliminar productos.
- Nginx distribuyendo solicitudes entre tres backends.
- PostgreSQL conservando el mismo inventario.
- Interfaz correcta en escritorio y móvil.
- Ninguna captura muestra `.env`, Client Secret, token o cookie.

Para detener el laboratorio sin borrar la base de datos:

```powershell
docker compose down
```

No añadir `-v`, porque esa opción elimina el volumen de PostgreSQL y los datos guardados.
