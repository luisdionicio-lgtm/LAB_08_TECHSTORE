# Guía de capturas Parte B - AWS EC2 y Application Load Balancer

Esta secuencia demuestra la Parte B del GLAB 07 en AWS, región **Estados Unidos (Ohio), `us-east-2`**. La arquitectura implementada usa una VPC, dos subredes públicas en zonas distintas, dos instancias EC2 con Apache y un Application Load Balancer.

## Recursos creados

| Recurso | Nombre o identificador |
|---|---|
| VPC | `vpc-lab-lb-vpc` - `vpc-0b07e238ea7427db6` - `10.0.0.0/16` |
| Subred pública 1 | `subnet-07fed1c7429919a9b` - `us-east-2a` - `10.0.0.0/20` |
| Subred pública 2 | `subnet-04eb1adb07ba2afad` - `us-east-2b` - `10.0.16.0/20` |
| Grupo de seguridad | `web-lab-sg` - `sg-0289ebc0305cdc0a8` |
| EC2 1 | `web-server-1` - `i-00f84da3c3db2b4cc` - `us-east-2a` |
| EC2 2 | `web-server-2` - `i-05ddccbb48e242903` - `us-east-2b` |
| Grupo de destino | `tg-lab-web` - HTTP puerto 80 |
| Balanceador | `alb-lab-web` - Internet-facing - HTTP puerto 80 |
| DNS público | `alb-lab-web-1429793162.us-east-2.elb.amazonaws.com` |

Las EC2 usan Amazon Linux 2023, tipo `t3.micro`, disco raíz `gp3` de **8 GiB** y la llave `key-server-03`. No se habilitaron NAT Gateway, IP elástica, RDS, WAF, CloudFront ni Global Accelerator.

> Importante: en PowerShell copie únicamente el texto dentro de cada bloque. No copie `PS C:\...>` ni escriba las comillas que rodean una explicación.

## Captura 1 - VPC y subredes

En la consola de VPC abra **Sus VPC** y seleccione `vpc-lab-lb-vpc`. La captura debe mostrar `10.0.0.0/16`. Después abra **Subredes** y capture juntas:

- `subnet-07fed1c7429919a9b`, `10.0.0.0/20`, `us-east-2a`.
- `subnet-04eb1adb07ba2afad`, `10.0.16.0/20`, `us-east-2b`.

Incluya la región `Ohio (us-east-2)` en la parte superior de la consola.

## Captura 2 - Enrutamiento público

En VPC abra **Tablas de enrutamiento**, seleccione la tabla pública de `vpc-lab-lb-vpc` y muestre la pestaña **Rutas**. Deben verse:

- Ruta local `10.0.0.0/16`.
- Ruta `0.0.0.0/0` con destino al Internet Gateway.

La captura demuestra que ambas subredes tienen salida pública sin usar NAT Gateway.

## Captura 3 - Grupo de seguridad

En EC2 abra **Grupos de seguridad** y seleccione `web-lab-sg`. Capture las reglas de entrada:

- HTTP TCP 80 desde `0.0.0.0/0`.
- SSH TCP 22 únicamente desde la IP pública utilizada durante la creación.

Capture también la regla de salida permitida. No exponga el contenido del archivo `.pem`.

## Captura 4 - Dos instancias EC2

En EC2 abra **Instancias** y filtre por `web-server`. Capture las dos filas juntas mostrando:

- Nombres `web-server-1` y `web-server-2`.
- Estado `En ejecución`.
- Tipo `t3.micro`.
- Zonas `us-east-2a` y `us-east-2b`.
- Comprobaciones de estado correctas.

Abra el detalle de una instancia y capture **Almacenamiento** para demostrar el volumen `gp3` de **8 GiB**.

## Captura 5 - Verificación de Apache por SSH

Reemplace `IP_PUBLICA_1` por la IP pública de `web-server-1` que muestra la consola y ejecute:

```powershell
ssh -i "D:\KEY\key-server-03.pem" ec2-user@IP_PUBLICA_1
```

Dentro de la EC2 ejecute:

```bash
hostname
lsblk
sudo systemctl is-active httpd
curl -s http://localhost | grep -o 'web-server-[12]' | head -1
exit
```

La captura debe mostrar el disco de 8 GB, `active` y `web-server-1`. Repita con la IP pública de `web-server-2` si necesita una evidencia individual del segundo servidor.

## Captura 6 - Grupo de destino y health checks

En EC2 abra **Grupos de destino**, seleccione `tg-lab-web` y abra **Comprobaciones de estado**. Capture:

- Protocolo HTTP.
- Puerto de tráfico 80.
- Ruta `/`.
- Código correcto `200`.

Luego abra **Destinos** y capture las dos instancias con estado **Healthy / En buen estado**:

- `i-00f84da3c3db2b4cc` en `us-east-2a`.
- `i-05ddccbb48e242903` en `us-east-2b`.

Si aparecen `Initial` o `Unused`, pulse **Actualizar** y espere uno o dos minutos antes de capturar.

## Captura 7 - Application Load Balancer

En EC2 abra **Balanceadores de carga** y seleccione `alb-lab-web`. Capture el panel de detalles mostrando:

- Estado `Activo`.
- Esquema `Internet-facing`.
- VPC `vpc-0b07e238ea7427db6`.
- Las zonas `us-east-2a` y `us-east-2b`.
- DNS `alb-lab-web-1429793162.us-east-2.elb.amazonaws.com`.

En la pestaña **Agentes de escucha y reglas**, muestre `HTTP:80` reenviando el 100 % a `tg-lab-web`.

## Captura 8 - Resolución DNS y respuesta HTTP

Abra PowerShell y ejecute exactamente:

```powershell
$ALB = "alb-lab-web-1429793162.us-east-2.elb.amazonaws.com"
Resolve-DnsName $ALB
curl.exe -I "http://$ALB"
```

La captura debe mostrar direcciones resueltas y una respuesta `HTTP/1.1 200 OK`.

## Captura 9 - Evidencia del balanceo entre las dos EC2

En la misma ventana de PowerShell ejecute:

```powershell
$ALB = "http://alb-lab-web-1429793162.us-east-2.elb.amazonaws.com"
1..12 | ForEach-Object {
    $html = curl.exe -s -H "Connection: close" "$ALB/?prueba=$_"
    if ($html -match 'web-server-[12]') { $Matches[0] } else { 'sin-respuesta' }
} | Group-Object | Select-Object Name, Count
```

La salida debe contener tanto `web-server-1` como `web-server-2`. Los conteos no necesitan ser exactamente 6 y 6; el ALB distribuye solicitudes entre los destinos saludables y la evidencia válida es que ambos respondan.

## Captura 10 - Páginas servidas por ambos destinos

Abra en el navegador:

```text
http://alb-lab-web-1429793162.us-east-2.elb.amazonaws.com
```

Actualice varias veces con `Ctrl+F5` hasta capturar una respuesta de `web-server-1` y otra de `web-server-2`. Use dos capturas si el informe debe identificar visualmente los dos destinos.

## Comandos de diagnóstico

Si el DNS todavía no responde:

```powershell
Resolve-DnsName alb-lab-web-1429793162.us-east-2.elb.amazonaws.com
```

Si un destino no aparece saludable, conéctese a esa EC2 y ejecute:

```bash
sudo systemctl status httpd --no-pager
sudo ss -lntp | grep ':80'
curl -I http://localhost/
sudo journalctl -u httpd --no-pager -n 30
```

## Orden recomendado en el informe

1. VPC y subredes en dos zonas.
2. Internet Gateway y ruta pública.
3. Reglas del grupo de seguridad.
4. Dos EC2 `t3.micro` con 8 GiB.
5. Apache activo.
6. Grupo de destino y health checks.
7. ALB activo con listener HTTP:80.
8. Resolución DNS y HTTP 200.
9. Distribución entre ambos servidores.
10. Páginas visuales de `web-server-1` y `web-server-2`.

Debajo de cada imagen escriba una oración indicando qué requisito demuestra. Al terminar la evaluación, detenga o elimine los recursos desde AWS para evitar consumo posterior de créditos; no ejecute una eliminación mientras todavía necesite capturas.
