from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp" / "lab08-video"
WEB = TMP / "web"
WORD = TMP / "word-images"
SCENES = TMP / "scenes"
AUDIO = TMP / "audio"
OUTPUT = ROOT / "output" / "video"
for folder in (SCENES, AUDIO, OUTPUT):
    folder.mkdir(parents=True, exist_ok=True)

W, H = 1920, 1080
NAVY = "#071821"
NAVY_2 = "#123240"
TEAL = "#13b8a6"
MINT = "#6ddbd0"
WHITE = "#f8fafc"
MUTED = "#b8c7cf"
YELLOW = "#f3ce52"
RED = "#e96a72"
BLUE = "#4285f4"
FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\seguisb.ttf"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"


def font(size, bold=False, mono=False):
    return ImageFont.truetype(FONT_MONO if mono else (FONT_BOLD if bold else FONT_REG), size)


def canvas():
    image = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(image)
    for y in range(H):
        ratio = y / H
        color = tuple(int(a + (b - a) * ratio) for a, b in zip((7, 24, 33), (18, 50, 64)))
        draw.line((0, y, W, y), fill=color)
    return image


def wrap(draw, text, x, y, width, fnt, fill=WHITE, spacing=9):
    words, lines, line = text.split(), [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= width:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    draw.multiline_text((x, y), "\n".join(lines), font=fnt, fill=fill, spacing=spacing)


def header(draw, number, title, subtitle):
    draw.rounded_rectangle((72, 58, 185, 112), 25, fill=TEAL)
    draw.text((100, 69), number, font=font(25, True), fill=NAVY)
    draw.text((215, 53), title, font=font(48, True), fill=WHITE)
    draw.text((218, 116), subtitle, font=font(23), fill=MUTED)


def footer(draw):
    draw.rounded_rectangle((72, 1004, 1848, 1044), 18, fill="#0b202b")
    draw.text((98, 1011), "TechStore · Laboratorio 08 · Evidencia académica local", font=font(20, True), fill=MUTED)
    draw.text((1600, 1011), "1080p · 60 FPS", font=font(20, True), fill=MINT)


def contain(base, source, box, background="#e9ece9"):
    x1, y1, x2, y2 = box
    base.paste(background, box)
    source = source.convert("RGB")
    source.thumbnail((x2 - x1, y2 - y1), Image.Resampling.LANCZOS)
    x = x1 + (x2 - x1 - source.width) // 2
    y = y1 + (y2 - y1 - source.height) // 2
    base.paste(source, (x, y))


def screenshot_scene(source, name, number, title, subtitle, focus=None):
    image = canvas()
    draw = ImageDraw.Draw(image)
    header(draw, number, title, subtitle)
    draw.rounded_rectangle((68, 178, 1852, 976), 26, fill="#eef0ea", outline="#31505d", width=3)
    shot = Image.open(source).convert("RGB")
    if focus:
        shot = shot.crop(focus)
    contain(image, shot, (88, 198, 1832, 956), "#eef0ea")
    footer(draw)
    image.save(SCENES / name, quality=95)


scenes = [
    {"id": "01", "title": "Presentación", "narration": "Presentamos TechStore, el sistema de inventario desarrollado para el Laboratorio 08. La demostración se ejecuta localmente con Docker y conserva una arquitectura distribuida: Nginx balancea solicitudes entre tres instancias Flask y PostgreSQL mantiene los datos compartidos. Revisaremos autenticación básica, seguridad, roles, GitHub con MFA y la experiencia del cliente."},
    {"id": "02", "title": "Arquitectura local", "narration": "Docker Compose inicia PostgreSQL y el contenedor de aplicación. Dentro de este último trabajan Nginx y tres backends identificados como backend uno, dos y tres. El navegador utiliza un único punto de entrada en el puerto ochenta ochenta. Las pruebas automáticas confirman una distribución uniforme mediante Round Robin, sin usar servicios de AWS."},
    {"id": "03", "title": "Pantalla de acceso", "narration": "La página principal permite autenticación básica y muestra accesos visuales para Gmail y GitHub. Las cuentas de prueba representan administrador, gerente, ventas, auditor y cliente. La interfaz también informa las reglas aplicadas: JWT interno válido por sesenta minutos, bloqueo temporal por intentos fallidos y tienda asignada."},
    {"id": "04", "title": "Validación de credenciales", "narration": "Para comprobar la protección, ingresamos una contraseña incorrecta. El sistema no revela si falló el usuario o la clave y registra el intento en PostgreSQL. La cuenta dispone de un máximo de tres intentos para esta demostración, de acuerdo con la adaptación solicitada para evidenciar el control durante el laboratorio."},
    {"id": "05", "title": "Bloqueo temporal", "narration": "Después del tercer intento incorrecto, TechStore bloquea la cuenta durante un minuto. Incluso si se escribe la contraseña correcta antes de finalizar ese periodo, el acceso se rechaza. Esta medida limita ataques repetitivos y ofrece una evidencia clara sin obligar a esperar varios minutos durante la exposición."},
    {"id": "06", "title": "Acceso correcto y JWT", "narration": "Con credenciales válidas, el administrador ingresa al inventario y el servidor genera un JWT interno con duración de sesenta minutos. La cookie se configura como HTTP only y SameSite Lax. Cada ruta protegida valida el token, el identificador del usuario, el rol y la tienda antes de permitir la operación."},
    {"id": "07", "title": "Cookie y sesión protegida", "narration": "La evidencia del navegador muestra la cookie techstore access token sin exponer su contenido completo. También aparece la sesión de Flask. En una entrega real nunca deben publicarse tokens, Client Secrets ni contraseñas. Para el laboratorio basta demostrar el nombre de la cookie, su dominio local, vencimiento y protección HTTP only."},
    {"id": "08", "title": "Usuarios y roles", "narration": "El administrador gestiona usuarios, tiendas y perfiles desde una vista central. El gerente administra productos de su tienda; ventas consulta productos y actualiza existencias; el auditor trabaja en modo de lectura; y el cliente utiliza el catálogo. Las restricciones se aplican en el backend, no solamente ocultando botones en la interfaz."},
    {"id": "09", "title": "GitHub OAuth", "narration": "El inicio social funcional se realiza con GitHub OAuth dos punto cero. El usuario revisa el nombre de TechStore y los permisos solicitados, limitados al perfil básico y correo. GitHub devuelve un código temporal al callback local, y TechStore valida el parámetro state para impedir solicitudes falsificadas."},
    {"id": "10", "title": "MFA con TOTP", "narration": "Después de GitHub, TechStore exige un segundo factor. El usuario escanea un código QR con Google Authenticator o una aplicación compatible. El TOTP contiene seis dígitos y cambia cada treinta segundos. El JWT definitivo solo se emite después de validar correctamente este segundo factor."},
    {"id": "11", "title": "Errores de MFA", "narration": "El formulario MFA permite como máximo tres códigos incorrectos. Cada fallo indica los intentos restantes sin mostrar la clave secreta. Si se alcanza el límite, se cancela la autenticación pendiente y el usuario debe comenzar nuevamente desde GitHub. Así se protegen tanto la identidad principal como el segundo factor."},
    {"id": "12", "title": "Catálogo del cliente", "narration": "El perfil Cliente recibe una vista distinta. Puede buscar productos, elegir cantidades y construir una selección con total referencial, pero no modificar precios, usuarios ni inventario administrativo. Las imágenes tecnológicas son referenciales y la confirmación académica no procesa pagos ni genera pedidos reales."},
    {"id": "13", "title": "Gmail en la interfaz", "narration": "El acceso con Gmail se conserva como demostración visual mediante el ícono multicolor solicitado. No se presenta como autenticación activa porque la cuenta institucional no autorizó crear un proyecto de Google Cloud. Esta decisión evita simular credenciales inexistentes y mantiene la evidencia técnicamente correcta."},
    {"id": "14", "title": "Verificación integral", "narration": "La prueba local valida doce solicitudes de salud, cuatro por cada backend; inicio de sesión; creación, lectura, actualización y eliminación de productos; catálogo del cliente; selección de artículos y aislamiento de permisos. PostgreSQL conserva la misma información mientras Nginx distribuye las solicitudes entre las tres instancias."},
    {"id": "15", "title": "Conclusiones", "narration": "TechStore demuestra que la seguridad debe aplicarse en varias capas. El login controla credenciales y bloqueos; el JWT protege rutas; los roles limitan operaciones; GitHub valida la identidad; y TOTP agrega un segundo factor. Docker permite reproducir la arquitectura local y las pruebas confirman que seguridad, inventario y catálogo funcionan de forma consistente."},
]

# Portada
image = canvas(); draw = ImageDraw.Draw(image)
draw.ellipse((1320, -250, 2100, 520), fill="#10566a")
draw.ellipse((-280, 730, 420, 1390), fill="#0a2b3a")
draw.rounded_rectangle((105, 90, 480, 145), 24, fill=TEAL)
draw.text((135, 101), "VIDEO EXPLICATIVO", font=font(24, True), fill=NAVY)
draw.text((105, 235), "TechStore", font=font(102, True), fill=WHITE)
draw.text((112, 365), "Seguridad y gestión de inventario", font=font(53, True), fill=MINT)
wrap(draw, "Laboratorio 08 · Docker · Nginx · PostgreSQL · JWT · OAuth · MFA TOTP", 116, 465, 1250, font(30), MUTED)
draw.rounded_rectangle((105, 690, 1180, 855), 28, fill="#0d2a36", outline="#2b6871", width=2)
draw.text((148, 725), "Recorrido", font=font(25, True), fill=YELLOW)
draw.text((148, 773), "Login, roles, GitHub, MFA y catálogo", font=font(33, True), fill=WHITE)
draw.text((110, 972), "Luis Angel Dionicio Bartolo", font=font(24), fill=MUTED)
image.save(SCENES / "01-title.png", quality=95)

# Arquitectura + captura Docker del Word
image = canvas(); draw = ImageDraw.Draw(image); header(draw, "02", "Arquitectura local", "Un acceso, tres backends y una base de datos compartida")
nodes = [(110, 430, 310, 145, "Navegador", "localhost:8080", MINT), (515, 430, 310, 145, "Nginx", "Round Robin", TEAL), (1000, 280, 315, 125, "backend-1", "Flask", MINT), (1000, 455, 315, 125, "backend-2", "Flask", MINT), (1000, 630, 315, 125, "backend-3", "Flask", MINT), (1495, 430, 310, 145, "PostgreSQL", "Datos compartidos", YELLOW)]
for x, y, w, h, title, sub, color in nodes:
    draw.rounded_rectangle((x, y, x+w, y+h), 22, fill="#0c2936", outline=color, width=3)
    draw.text((x+25, y+26), title, font=font(29, True), fill=WHITE); draw.text((x+25, y+78), sub, font=font(21), fill=MUTED)
draw.line((420, 500, 515, 500), fill=MINT, width=6); draw.line((825, 500, 1000, 345), fill=TEAL, width=4); draw.line((825, 500, 1000, 518), fill=TEAL, width=4); draw.line((825, 500, 1000, 692), fill=TEAL, width=4)
draw.line((1315, 345, 1495, 500), fill=YELLOW, width=4); draw.line((1315, 518, 1495, 500), fill=YELLOW, width=4); draw.line((1315, 692, 1495, 500), fill=YELLOW, width=4)
draw.rounded_rectangle((112, 790, 1805, 940), 22, fill="#0a222e")
draw.text((150, 820), "Docker Compose", font=font(27, True), fill=TEAL); draw.text((150, 872), "Servicios reproducibles · health checks · persistencia local · sin AWS", font=font(27), fill=WHITE)
footer(draw); image.save(SCENES / "02-architecture.png", quality=95)

screenshot_scene(WEB / "01-login.png", "03-login.png", "03", "Pantalla de acceso", "Login básico, Gmail+ visual y GitHub OAuth")
screenshot_scene(WEB / "02-failed-2.png", "04-failed.png", "04", "Validación de credenciales", "Intentos fallidos registrados sin revelar datos sensibles")
screenshot_scene(WEB / "03-locked-correct-password.png", "05-lock.png", "05", "Bloqueo temporal", "Tres intentos incorrectos · bloqueo de un minuto")
screenshot_scene(WEB / "04-admin-dashboard.png", "06-admin.png", "06", "Acceso correcto y JWT", "Administrador · TechStore Lima Centro · token de 60 minutos")
screenshot_scene(WORD / "14-image17.png", "07-cookie.png", "07", "Cookie JWT protegida", "Evidencia en DevTools sin publicar el token completo")
screenshot_scene(WEB / "05-users-roles.png", "08-roles.png", "08", "Usuarios y roles", "Asignación de perfiles y restricciones desde el backend")
screenshot_scene(WORD / "18-image21.png", "09-github.png", "09", "GitHub OAuth 2.0", "Autorización de perfil y correo con callback local")
screenshot_scene(WORD / "19-image22.png", "10-mfa.png", "10", "Segundo factor TOTP", "Código de seis dígitos · cambia cada 30 segundos")
screenshot_scene(WORD / "20-image23.png", "11-mfa-errors.png", "11", "Manejo de errores MFA", "Máximo tres intentos antes de reiniciar el flujo")
screenshot_scene(WEB / "07-client-catalog.png", "12-catalog.png", "12", "Vista del cliente", "Selección de productos sin permisos administrativos")
screenshot_scene(WEB / "06-gmail-github.png", "13-gmail.png", "13", "Gmail+ como evidencia visual", "Google Cloud no configurado · GitHub permanece funcional")

# Verificación
image = canvas(); draw = ImageDraw.Draw(image); header(draw, "14", "Verificación integral", "Pruebas ejecutadas sobre la arquitectura local")
checks = [("12 solicitudes", "4 respuestas por backend", MINT), ("Login y JWT", "Rutas protegidas", TEAL), ("CRUD completo", "Crear · leer · actualizar · eliminar", YELLOW), ("Cliente", "Catálogo, selección y aislamiento", BLUE)]
for i, (title, detail, color) in enumerate(checks):
    x = 115 + (i % 2) * 870; y = 330 + (i // 2) * 270
    draw.rounded_rectangle((x, y, x+755, y+190), 27, fill="#0c2936", outline=color, width=3)
    draw.ellipse((x+38, y+58, x+100, y+120), fill=color); draw.text((x+126, y+40), title, font=font(35, True), fill=WHITE); draw.text((x+126, y+103), detail, font=font(24), fill=MUTED)
footer(draw); image.save(SCENES / "14-verification.png", quality=95)

# Cierre
image = canvas(); draw = ImageDraw.Draw(image); header(draw, "15", "Conclusiones", "Seguridad aplicada en capas y arquitectura reproducible")
items = [("Credenciales", "Bloqueo temporal"), ("JWT", "Sesión de 60 minutos"), ("Roles", "Permisos reales"), ("GitHub + TOTP", "Identidad y segundo factor"), ("Docker", "Tres backends"), ("PostgreSQL", "Datos compartidos")]
for i, (title, detail) in enumerate(items):
    x = 105 + (i % 3) * 595; y = 285 + (i // 3) * 260
    draw.rounded_rectangle((x, y, x+520, y+190), 26, fill="#0c2936", outline=TEAL if i % 2 == 0 else MINT, width=2)
    draw.text((x+32, y+39), title, font=font(31, True), fill=WHITE); draw.text((x+32, y+103), detail, font=font(23), fill=MUTED)
draw.text((110, 875), "Repositorio: github.com/luisdionicio-lgtm/LAB_08_TECHSTORE", font=font(27, True), fill=MINT)
footer(draw); image.save(SCENES / "15-conclusion.png", quality=95)

for scene in scenes:
    (AUDIO / f"{scene['id']}.txt").write_text(scene["narration"], encoding="utf-8")
(TMP / "scenes.json").write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")
(OUTPUT / "GUION_TECHSTORE_LAB08.txt").write_text("GUION VIDEO TECHSTORE LAB08\n\n" + "\n\n".join(f"{s['id']}. {s['title']}\n{s['narration']}" for s in scenes), encoding="utf-8")
print(f"Generadas {len(scenes)} escenas para TechStore LAB08.")
