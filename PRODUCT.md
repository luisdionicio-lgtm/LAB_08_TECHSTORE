# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Personal administrativo de TechStore que consulta y actualiza el inventario tecnológico desde un navegador en un entorno académico local.

## Product Purpose

TechStore demuestra un sistema centralizado de inventario para productos tecnológicos. Permite iniciar sesión, consultar existencias y administrar registros mientras Nginx distribuye las solicitudes entre tres instancias idénticas de la aplicación y PostgreSQL conserva el estado compartido.

## Positioning

La aplicación hace visible su arquitectura local balanceada dentro de una experiencia operativa de inventario, de modo que cada acción demuestra qué backend atendió la solicitud sin depender de servicios AWS.

## Operating Context

El proyecto se ejecuta con Docker Compose. Nginx recibe las solicitudes, aplica Round Robin entre tres procesos Flask y todos comparten una base de datos PostgreSQL.

## Capabilities and Constraints

- Ejecución exclusivamente local mediante Docker.
- Sin infraestructura AWS.
- Inicio de sesión básico por usuario o correo con validación de credenciales.
- Inicio de sesión con Google y GitHub OAuth 2.0 configurado mediante variables de entorno.
- Segundo factor TOTP obligatorio después de GitHub OAuth, compatible con Google Authenticator y limitado a tres intentos.
- El JWT interno se emite únicamente después de completar correctamente el segundo factor.
- Token JWT interno en cookie HttpOnly, válido durante 60 minutos y validado en cada ruta protegida.
- Bloqueo de cuenta durante 1 minuto después de tres intentos fallidos; contador atómico para tres backends.
- Tienda y rol asignados a cada usuario.
- CRUD de productos tecnológicos con inventario compartido.
- Cinco perfiles con control de acceso: Administrador, Gerente de Tienda, Empleado de Ventas, Auditor y Cliente.
- Administración de cuentas, roles y tienda asignada disponible únicamente para el Administrador.
- Gerente limitado a productos de su tienda; Ventas limitado a actualizar stock; Auditor en modo de solo lectura.
- Vista de Cliente con catálogo, búsqueda, cantidades y selección de productos sin pagos reales.
- Las nuevas identidades de GitHub y Google reciben el perfil Cliente y acceden al catálogo después de autenticarse.
- Conservación de Nginx, tres backends y PostgreSQL.
- La arquitectura debe seguir siendo demostrable mediante la cabecera y el indicador del backend que atendió cada solicitud.

## Brand Commitments

El producto se llama TechStore. El contenido, los ejemplos y el lenguaje deben pertenecer al comercio y control de inventario tecnológico.

## Evidence on Hand

El repositorio contiene una aplicación Flask funcional, configuración de Docker Compose, Nginx, PostgreSQL, scripts de verificación y una interfaz web existente.

## Product Principles

- Hacer visible el inventario y sus riesgos de un vistazo.
- Mantener las operaciones CRUD simples y verificables.
- Explicar la arquitectura local mediante la propia experiencia del producto.
- Usar datos de demostración claramente identificables y técnicamente coherentes.

## Accessibility & Inclusion

La interfaz debe funcionar con teclado, conservar foco visible, contraste legible y adaptación para escritorio y móvil.
