from pathlib import Path
from zipfile import ZipFile
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

SOURCE = Path(r"C:\Users\Luis Angel\Downloads\GLAB-S08-JFARFAN-2026-02.docx")
OUT = Path(__file__).resolve().parents[1] / "tmp" / "lab08-video" / "word-images"
OUT.mkdir(parents=True, exist_ok=True)

font = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 24)
cards = []
with ZipFile(SOURCE) as archive:
    media = [name for name in archive.namelist() if name.startswith("word/media/")]
    for index, name in enumerate(media, 1):
        image = Image.open(BytesIO(archive.read(name))).convert("RGB")
        target = OUT / f"{index:02}-{Path(name).name}"
        image.save(target)
        thumb = image.copy()
        thumb.thumbnail((420, 250), Image.Resampling.LANCZOS)
        card = Image.new("RGB", (460, 310), "white")
        card.paste(thumb, ((460 - thumb.width) // 2, 42 + (250 - thumb.height) // 2))
        draw = ImageDraw.Draw(card)
        draw.text((16, 10), f"{index:02} · {Path(name).name} · {image.width}×{image.height}", font=font, fill="#111827")
        cards.append(card)

sheet = Image.new("RGB", (1380, ((len(cards) + 2) // 3) * 310), "#d9e2e8")
for index, card in enumerate(cards):
    sheet.paste(card, ((index % 3) * 460, (index // 3) * 310))
sheet.save(OUT.parent / "word-images-contact-sheet.jpg", quality=92)
print(OUT.parent / "word-images-contact-sheet.jpg")
