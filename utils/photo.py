import io
from pathlib import Path
from PIL import Image
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
        
        # Convert RGBA/P to RGB if needed
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        save_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(save_path, "JPEG", quality=95)
        
        return True, "Rasm muvaffaqiyatli qabul qilindi!"
    except Exception as e:
        return False, f"Rasm faylida xatolik yuz berdi: {str(e)}"
