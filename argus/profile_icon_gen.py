"""Generate simple high-contrast PNG app marks (Golden Path tokens; no SVG)."""

from __future__ import annotations

from collections.abc import Callable

from argus.profile_png import encode_rgba_png

# Golden Path tokens: dark surface, primary/secondary, onSurface.
_BG, _FG = (0x1A, 0x1A, 0x2E, 255), (0xE6, 0xE6, 0xF0, 255)
_ACCENT, _SECONDARY = (0xD3, 0x30, 0x4E, 255), (0x9B, 0xB8, 0xE8, 255)
_SIZE = 512


def _px(buf: bytearray, x: int, y: int, rgba: tuple[int, int, int, int]) -> None:
    if 0 <= x < _SIZE and 0 <= y < _SIZE:
        buf[(y * _SIZE + x) * 4 : (y * _SIZE + x) * 4 + 4] = bytes(rgba)


def _fill(buf: bytearray, rgba: tuple[int, int, int, int]) -> None:
    pix = bytes(rgba)
    for i in range(0, len(buf), 4):
        buf[i : i + 4] = pix


def _rect(buf: bytearray, x0: int, y0: int, x1: int, y1: int, rgba: tuple[int, int, int, int]) -> None:
    for y in range(max(0, y0), min(_SIZE, y1)):
        for x in range(max(0, x0), min(_SIZE, x1)):
            _px(buf, x, y, rgba)


def _circle(buf: bytearray, cx: int, cy: int, r: int, rgba: tuple[int, int, int, int]) -> None:
    r2 = r * r
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                _px(buf, x, y, rgba)


def _ring(buf: bytearray, cx: int, cy: int, r_out: int, r_in: int, rgba: tuple[int, int, int, int]) -> None:
    for y in range(cy - r_out, cy + r_out + 1):
        for x in range(cx - r_out, cx + r_out + 1):
            d = (x - cx) ** 2 + (y - cy) ** 2
            if r_in * r_in < d <= r_out * r_out:
                _px(buf, x, y, rgba)


def _motif_chat(buf: bytearray, a: tuple[int, int, int, int]) -> None:
    _rect(buf, 96, 120, 320, 300, a)
    _rect(buf, 192, 220, 416, 400, _FG)
    _rect(buf, 220, 250, 388, 370, _BG)


def _motif_camera(buf: bytearray, a: tuple[int, int, int, int]) -> None:
    _rect(buf, 96, 160, 416, 400, a)
    _rect(buf, 180, 120, 280, 170, _FG)
    _circle(buf, 256, 280, 88, _FG)
    _circle(buf, 256, 280, 48, _BG)


def _motif_clock(buf: bytearray, a: tuple[int, int, int, int]) -> None:
    _ring(buf, 256, 256, 160, 120, a)
    _rect(buf, 248, 140, 264, 270, _FG)
    _rect(buf, 248, 248, 360, 264, a)


def _motif_bars(buf: bytearray, a: tuple[int, int, int, int]) -> None:
    for i, h in enumerate((120, 180, 260, 200)):
        x0 = 110 + i * 80
        _rect(buf, x0, 400 - h, x0 + 48, 400, a if i % 2 == 0 else _FG)


def _motif_lock(buf: bytearray, a: tuple[int, int, int, int]) -> None:
    _ring(buf, 256, 180, 70, 40, _FG)
    _rect(buf, 150, 200, 362, 400, a)
    _circle(buf, 256, 300, 28, _FG)


def _motif_home(buf: bytearray, a: tuple[int, int, int, int]) -> None:
    for y in range(80, 240):
        w = (y - 80) * 2
        _rect(buf, 256 - w // 2, y, 256 + w // 2, y + 1, a)
    _rect(buf, 150, 230, 362, 420, _FG)
    _rect(buf, 220, 300, 292, 420, _BG)


def _motif_link(buf: bytearray, a: tuple[int, int, int, int]) -> None:
    _ring(buf, 190, 256, 90, 55, a)
    _ring(buf, 322, 256, 90, 55, _FG)


def _motif_play(buf: bytearray, a: tuple[int, int, int, int]) -> None:
    _circle(buf, 256, 256, 160, a)
    for y in range(160, 352):
        t = (y - 160) / 192
        right = int(220 + 140 * (1 - abs(2 * t - 1)))
        _rect(buf, 220, y, right, y + 1, _FG)


def _motif_dial(buf: bytearray, a: tuple[int, int, int, int]) -> None:
    _ring(buf, 256, 280, 150, 110, a)
    _rect(buf, 248, 140, 264, 280, _FG)
    _circle(buf, 256, 280, 24, _FG)


def _motif_mark(buf: bytearray, a: tuple[int, int, int, int]) -> None:
    _circle(buf, 256, 256, 140, a)
    _circle(buf, 256, 256, 70, _BG)
    _circle(buf, 256, 256, 36, _FG)


_RULES: list[tuple[tuple[str, ...], Callable[..., None]]] = [
    (("message", "sms", "chat", "mail", "inbox"), _motif_chat),
    (("camera", "photo", "shoot", "lens"), _motif_camera),
    (("alarm", "clock", "time", "chrono"), _motif_clock),
    (("bot", "trend", "algo", "trade", "pulse"), _motif_bars),
    (("vault", "lock", "secure", "crypto", "key"), _motif_lock),
    (("launch", "home", "hermes", "desktop"), _motif_home),
    (("link", "share", "sync", "bridge"), _motif_link),
    (("media", "video", "ingest", "stream"), _motif_play),
    (("gauge", "obd", "map", "nav", "gps"), _motif_dial),
]


def choose_motif(name: str, description: str | None) -> Callable[..., None]:
    blob = f"{name} {description or ''}".lower()
    for keys, fn in _RULES:
        if any(k in blob for k in keys):
            return fn
    return _motif_mark


def generate_icon_png(name: str, description: str | None = None) -> bytes:
    """512×512 PNG: dark surface + motif from name/description."""
    buf = bytearray(_SIZE * _SIZE * 4)
    _fill(buf, _BG)
    accent = _ACCENT if (sum(map(ord, name)) % 2 == 0) else _SECONDARY
    choose_motif(name, description)(buf, accent)
    return encode_rgba_png(_SIZE, _SIZE, buf)


def icon_asset_path(repo_name: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in repo_name)
    return f"assets/argus-icons/{safe}.png"


def icon_raw_url(profile_login: str, repo_name: str) -> str:
    path = icon_asset_path(repo_name)
    return f"https://raw.githubusercontent.com/{profile_login}/{profile_login}/main/{path}"
