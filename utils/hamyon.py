"""hamyon-api.uz mijozi.

Hujjatda javob formatlari ko'rsatilmagan, shuning uchun maydonlar bir nechta nom bo'yicha
qidiriladi, xom javoblar esa logga yoziladi (muammo bo'lsa Render Logs'dan ko'ring).
"""
import hashlib
import json
import logging
from typing import Any, Optional

import aiohttp

from config import HAMYON_BASE_URL, HAMYON_SHOP_ID, HAMYON_SHOP_KEY

log = logging.getLogger(__name__)


class HamyonError(Exception):
    pass


def enabled() -> bool:
    return bool(HAMYON_SHOP_ID and HAMYON_SHOP_KEY)


def find(obj: Any, keys: tuple) -> Optional[Any]:
    """Ichma-ich JSON ichidan birinchi mos kalitni topadi."""
    if isinstance(obj, dict):
        for k in keys:
            if obj.get(k) not in (None, ""):
                return obj[k]
        for v in obj.values():
            r = find(v, keys)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find(v, keys)
            if r is not None:
                return r
    return None


async def _request(method: str, path: str, **kwargs):
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.request(method, f"{HAMYON_BASE_URL}{path}", **kwargs) as resp:
            text = await resp.text()
            try:
                data = json.loads(text)
            except Exception:
                data = {}
            # shop_key logga tushmasligi uchun faqat javob matni yoziladi
            log.info("hamyon %s %s -> %s %s", method, path, resp.status, text[:500])
            return resp.status, data


async def create_payment(amount: int, order_id: str) -> dict:
    """To'lov yaratadi. Qaytaradi: {payment_id, card, amount}. Xatolikda HamyonError."""
    last_err = ""
    # Bir xil summali ikkita ochiq to'lov bo'lmasligi uchun band bo'lsa summani 1 so'mdan oshiramiz
    for offset in range(0, 6):
        amt = amount + offset
        payload = {
            "shop_id": HAMYON_SHOP_ID,
            "shop_key": HAMYON_SHOP_KEY,
            "amount": amt,
            "order_id": order_id,
        }
        for kind in ("json", "data"):
            try:
                status, data = await _request("POST", "/payment/create", **{kind: payload})
            except Exception as e:
                last_err = str(e)
                continue
            pid = find(data, ("payment_id", "id"))
            card = find(data, ("card", "card_number", "card_num", "card_no", "pan"))
            if status < 400 and pid is not None and card is not None:
                return {
                    "payment_id": str(pid),
                    "card": str(card),
                    "amount": int(float(find(data, ("amount", "pay_amount", "total")) or amt)),
                }
            last_err = f"status={status} data={str(data)[:200]}"
            if kind == "json" and status < 400 and not data:
                continue
        # Boshqa urinishlar faqat 'summa band' holatida mantiqli, lekin sababini bilmaymiz — keyingi summani sinaymiz
    raise HamyonError(last_err or "unknown error")


async def get_status(payment_id: str) -> tuple[Optional[str], Optional[float]]:
    """(status, summa). status: prepare / pending / paid / cancel yoki None."""
    params = {"shop_id": HAMYON_SHOP_ID, "shop_key": HAMYON_SHOP_KEY, "payment_id": payment_id}
    status, data = await _request("GET", "/payment/status", params=params)
    if status >= 400:
        return None, None
    st = find(data, ("status", "state"))
    amt = find(data, ("amount",))
    try:
        amt = float(amt) if amt is not None else None
    except (TypeError, ValueError):
        amt = None
    return (str(st).lower() if st is not None else None), amt


def verify_sign(shop_id: str, payment_id: str, amount: str, sign: str) -> bool:
    raw = f"{shop_id}{payment_id}{amount}{HAMYON_SHOP_KEY}"
    return hashlib.md5(raw.encode()).hexdigest().lower() == str(sign).strip().lower()
