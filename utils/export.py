"""Anketani ZIP ga yig'ish: info.txt (ma'lumotlar) + PNG rasmlar."""
import io
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from config import PHOTOS_DIR

MAX_ZIP_BYTES = 48 * 1024 * 1024  # Telegram bot fayl limiti ~50 MB


def _safe(text: Optional[str]) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", (text or "").strip()).strip("_") or "NA"


def _v(x: Any) -> str:
    return str(x).strip() if x not in (None, "") else "—"


def _place(region: Optional[str], city: Optional[str], country: Optional[str]) -> str:
    parts = [p for p in (region, city, country) if p]
    return ", ".join(parts) if parts else "—"


def _person_block(title: str, p: Dict[str, Any]) -> List[str]:
    return [
        f"--- {title} ---",
        f"Familiya (Last name): {_v(p.get('last_name'))}",
        f"Ism (First name):     {_v(p.get('first_name'))}",
        f"Jinsi:                {_v(p.get('gender'))}",
        f"Tug'ilgan sana:       {_v(p.get('birth_date'))}",
        f"Tug'ilgan joyi:       {_place(p.get('birth_region'), p.get('birth_city') or p.get('birth_district'), p.get('birth_country'))}",
    ]


def build_info_text(app_id: Any, data: Dict[str, Any], tg: Dict[str, Any]) -> str:
    live_region = data.get("district_state") or data.get("live_region")
    live_city = data.get("city") or data.get("live_district")
    lines = [
        f"GREEN CARD ANKETASI  #{app_id}",
        f"Yaratilgan: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        f"Telegram: @{tg.get('username') or 'yo_q'}  |  ID: {_v(tg.get('id'))}  |  Ism: {_v(tg.get('full_name'))}",
        "",
    ]
    lines += _person_block("ASOSIY ARIZACHI", data)
    lines += [
        f"Pasport raqami:       {_v(data.get('passport_number'))}",
        f"Pasport muddati:      {_v(data.get('passport_expiry'))}",
        f"Yashash davlati:      {_v(data.get('live_country') or data.get('country'))}",
        f"Yashash viloyati:     {_v(live_region)}",
        f"Yashash tumani:       {_v(live_city)}",
        f"Manzil:               {_v(data.get('address_line1'))}",
        f"Telefon:              {_v(data.get('phone_number'))}",
        f"Email:                {_v(data.get('email'))}",
        f"Ta'lim darajasi:      {_v(data.get('education_level'))}",
        f"Oilaviy holati:       {_v(data.get('marital_status'))}",
        f"Farzandlar soni:      {_v(data.get('children_count', 0))}",
        "",
    ]
    spouse = data.get("spouse")
    if spouse:
        lines += _person_block("TURMUSH O'RTOG'I", spouse)
        lines += [f"Ta'lim darajasi:      {_v(spouse.get('education_level'))}", ""]
    for i, ch in enumerate(data.get("children") or [], start=1):
        lines += _person_block(f"FARZAND #{ch.get('child_index') or i}", ch)
        lines.append("")
    return "\n".join(lines)


def _png_bytes(src: Path) -> Optional[bytes]:
    try:
        with Image.open(src) as img:
            buf = io.BytesIO()
            img.convert("RGB").save(buf, "PNG", optimize=True)
            return buf.getvalue()
    except Exception:
        return None


def _photo_list(data: Dict[str, Any]) -> List[Tuple[str, Optional[str]]]:
    items: List[Tuple[str, Optional[str]]] = [
        ("01_asosiy_foto", data.get("photo_path")),
        ("02_pasport", data.get("passport_photo_path")),
    ]
    spouse = data.get("spouse")
    if spouse:
        items.append(("03_turmush_ortogi_foto", spouse.get("photo_path")))
    for i, ch in enumerate(data.get("children") or [], start=1):
        items.append((f"04_farzand_{ch.get('child_index') or i}_foto", ch.get("photo_path")))
    return items


def build_application_zip(app_id: Any, data: Dict[str, Any], tg: Dict[str, Any], out_dir: Path) -> Path:
    """ZIP yaratadi va yo'lini qaytaradi. PNG hajmi katta bo'lsa, rasmlar JPEG holida qo'shiladi."""
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"anketa_{app_id}_{_safe(data.get('last_name'))}_{_safe(data.get('first_name'))}.zip"
    info = build_info_text(app_id, data, tg)
    photos = [(name, PHOTOS_DIR / fn) for name, fn in _photo_list(data) if fn and (PHOTOS_DIR / fn).exists()]

    for as_png in (True, False):
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("info.txt", info)
            for name, src in photos:
                if as_png:
                    content = _png_bytes(src)
                    if content is not None:
                        zf.writestr(f"{name}.png", content)
                        continue
                zf.write(src, f"{name}.jpg")
        if zip_path.stat().st_size <= MAX_ZIP_BYTES:
            break
    return zip_path


def delete_application_photos(data: Dict[str, Any]) -> int:
    """Anketaga tegishli rasmlarni serverdan o'chiradi. O'chirilgan fayllar sonini qaytaradi."""
    n = 0
    for _, fn in _photo_list(data):
        if not fn:
            continue
        f = PHOTOS_DIR / Path(fn).name
        try:
            if f.exists():
                f.unlink()
                n += 1
        except Exception:
            pass
    return n


def cleanup_old_photos(days: int) -> int:
    """PHOTOS_DIR dagi `days` kundan eski fayllarni o'chiradi."""
    import time
    cutoff = time.time() - days * 86400
    n = 0
    for f in PHOTOS_DIR.iterdir():
        try:
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
                n += 1
        except Exception:
            pass
    return n
