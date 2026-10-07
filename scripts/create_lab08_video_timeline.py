from pathlib import Path
import json, re, wave

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp" / "lab08-video"
scenes = json.loads((TMP / "scenes.json").read_text(encoding="utf-8"))


def stamp(seconds):
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


timeline, subtitles, clock, subtitle_index = [], [], 0.0, 1
for scene in scenes:
    audio = TMP / "audio" / f"{scene['id']}.wav"
    with wave.open(str(audio), "rb") as source:
        spoken = source.getnframes() / source.getframerate()
    duration = spoken + 0.85
    image = next((TMP / "scenes").glob(f"{scene['id']}-*.png"))
    timeline.append({**scene, "image": str(image), "audio": str(audio), "duration": round(duration, 3), "start": round(clock, 3)})
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", scene["narration"]) if part.strip()]
    weights = [max(1, len(sentence.split())) for sentence in sentences]
    available = max(0.5, spoken - 0.2)
    local = clock + 0.12
    for sentence, weight in zip(sentences, weights):
        segment = available * weight / sum(weights)
        subtitles.extend([str(subtitle_index), f"{stamp(local)} --> {stamp(local + segment)}", sentence, ""])
        subtitle_index += 1
        local += segment
    clock += duration

(TMP / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
(TMP / "subtitles.srt").write_text("\n".join(subtitles), encoding="utf-8")
print(f"Duración estimada: {clock:.1f} segundos ({clock/60:.2f} minutos)")
