"""Small, dependency-free set of inline Lucide-compatible SVG icons."""

from html import escape


_PATHS = {
    "landmark": '<path d="M3 22h18"/><path d="M6 18v-7"/><path d="M10 18v-7"/><path d="M14 18v-7"/><path d="M18 18v-7"/><path d="M12 2 3 7h18L12 2Z"/><path d="M4 11h16"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 22a8 8 0 0 1 16 0"/>',
    "hard-hat": '<path d="M2 18a10 10 0 0 1 20 0"/><path d="M4 18h16"/><path d="M12 4v5"/><path d="M4 18v2h16v-2"/>',
    "building": '<rect width="16" height="20" x="4" y="2" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M8 10h.01M16 10h.01M8 14h.01M16 14h.01"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V5l8-3 8 3v8Z"/><path d="m9 12 2 2 4-4"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "route": '<circle cx="6" cy="19" r="3"/><path d="M9 19h5.5a3.5 3.5 0 0 0 0-7H9"/><circle cx="18" cy="5" r="3"/>',
    "camera": '<path d="M14.5 4 16 7h4a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h4l1.5-3Z"/><circle cx="12" cy="13" r="3"/>',
    "zap": '<path d="m13 2-9 12h8l-1 8 9-12h-8l1-8Z"/>',
    "circle-check": '<circle cx="12" cy="12" r="10"/><path d="m8 12 2.5 2.5L16 9"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
    "sparkles": '<path d="m12 3-1.9 5.8L4 10.7l6.1 1.8L12 18l1.9-5.5 6.1-1.8-6.1-1.9L12 3Z"/><path d="m19 16-.7 2.3L16 19l2.3.7L19 22l.7-2.3L22 19l-2.3-.7L19 16Z"/>',
    "map-pin": '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "tag": '<path d="M12.6 2.6H5a2 2 0 0 0-2 2v7.6a2 2 0 0 0 .6 1.4l7.8 7.8a2 2 0 0 0 2.8 0l7.2-7.2a2 2 0 0 0 0-2.8l-7.8-7.8a2 2 0 0 0-1.4-.6Z"/><circle cx="7.5" cy="7.5" r="1"/>',
    "trash": '<path d="M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6M10 11v6M14 11v6"/>',
    "waves": '<path d="M2 12c1.5 1.5 3 1.5 4.5 0s3-1.5 4.5 0 3 1.5 4.5 0 3-1.5 4.5 0"/><path d="M2 18c1.5 1.5 3 1.5 4.5 0s3-1.5 4.5 0 3 1.5 4.5 0 3-1.5 4.5 0"/><path d="M2 6c1.5 1.5 3 1.5 4.5 0s3-1.5 4.5 0 3 1.5 4.5 0 3-1.5 4.5 0"/>',
    "droplet": '<path d="M12 2s7 7 7 12a7 7 0 0 1-14 0c0-5 7-12 7-12Z"/>',
    "construction": '<path d="M3 22h18"/><path d="M6 22V9l6-4 6 4v13M9 22v-5h6v5M3 9h18"/>',
    "lightbulb": '<path d="M9 18h6M10 22h4"/><path d="M9 14a6 6 0 1 1 6 0c-1 1-1 2-1 3h-4c0-1 0-2-1-3Z"/>',
    "cloud-rain": '<path d="M17.5 19H9a7 7 0 1 1 6.7-9A5 5 0 1 1 17.5 19Z"/><path d="M8 19v2M12 19v2M16 19v2"/>',
    "accessibility": '<circle cx="12" cy="4" r="2"/><path d="M5 8h14M12 6v16M8 22l4-8 4 8"/>',
    "folder": '<path d="M3 6a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6Z"/>',
    "megaphone": '<path d="m3 11 18-5v12L3 13v-2Z"/><path d="M11.6 15.6 13 21H8l-1.5-6.5"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/><path d="M14 2v6h6M8 13h8M8 17h8"/>',
    "file-code": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/><path d="M14 2v6h6M10 13l-2 2 2 2M14 17l2-2-2-2"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 16 4-5 3 2 5-7"/>',
    "eye": '<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2"/>',
    "log-out": '<path d="M10 17l5-5-5-5"/><path d="M15 12H3"/><path d="M21 19V5a2 2 0 0 0-2-2h-6"/>',
}


def icon_svg(name: str, *, size: int = 24, color: str = "currentColor", label: str = "") -> str:
    """Return an accessible, inline SVG using Lucide's 24px stroke convention."""
    paths = _PATHS.get(name, _PATHS["sparkles"])
    title = f"<title>{escape(label)}</title>" if label else ""
    aria = f'aria-label="{escape(label)}" role="img"' if label else 'aria-hidden="true"'
    return (
        f'<svg class="civic-icon" {aria} width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{escape(color)}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{title}{paths}</svg>'
    )


def category_icon(slug: str) -> str:
    """Return a distinct SVG and theme colour for each civic problem category."""
    icon, color = {
        "garbage": ("trash", "#475569"),
        "open-sewage": ("waves", "#7C3AED"),
        "drainage": ("waves", "#0284C7"),
        "water-leakage": ("droplet", "#0284C7"),
        "water-supply": ("droplet", "#0EA5E9"),
        "pothole": ("construction", "#D97706"),
        "streetlight": ("lightbulb", "#CA8A04"),
        "flooding": ("cloud-rain", "#2563EB"),
        "public-sanitation": ("accessibility", "#0F766E"),
        "illegal-dumping": ("trash", "#B45309"),
        "damaged-infrastructure": ("construction", "#64748B"),
    }.get(slug, ("tag", "#475569"))
    return icon_svg(icon, size=20, color=color, label="")
