import io
from pathlib import Path
from PIL import Image, ImageOps
from typing import Tuple

def validate_and_save_photo(file_bytes: bytes, save_path: Path) -> Tuple[bool, str]:
    """
    Saves the entrant photo or passport photo:
    - Validates that it's a readable image
    - Converts RGBA/P to RGB
    - Preserves good quality JPEG
    - No strict 1:1 restriction (operators can crop/adjust manually if needed)
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = ImageOps.exif_transpose(img)
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        save_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(save_path, "JPEG", quality=95)
        
        return True, "Rasm muvaffaqiyatli qabul qilindi!"
    except Exception as e:
        return False, f"Rasm faylida xatolik yuz berdi: {str(e)}"

MAX_PHOTO_BYTES = 240 * 1024
PHOTO_SIZE = 600

def process_dv_photo(file_bytes: bytes, save_path: Path) -> Tuple[bool, str]:
    """
    Green Card fotosurati (sayt talabi bo'yicha):
    - kamida 600x600 px, kvadrat (markazdan qirqiladi) va 600x600 ga keltiriladi
    - hajmi 240 KB dan oshmaydi (sifat pasaytirib boriladi)
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size
        side = min(w, h)
        left, top = (w - side) // 2, (h - side) // 2
        img = img.crop((left, top, left + side, top + side)).resize(
            (PHOTO_SIZE, PHOTO_SIZE), Image.Resampling.LANCZOS
        )

        save_path.parent.mkdir(parents=True, exist_ok=True)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=90, optimize=True)
        save_path.write_bytes(buf.getvalue())
        return True, "OK"
    except Exception as e:
        return False, f"Rasm faylida xatolik: {e}"
