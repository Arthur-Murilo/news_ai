import html
import ipaddress
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from src.utils import strip_markdown_code_fences

ALLOWED_HTML_TAGS = {
    "a",
    "br",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "hr",
    "img",
    "li",
    "ol",
    "p",
    "span",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}
VOID_HTML_TAGS = {"br", "hr", "img"}
ALLOWED_GLOBAL_ATTRIBUTES = {"style", "align"}
ALLOWED_TAG_ATTRIBUTES = {
    "a": {"href", "style", "title"},
    "img": {"src", "alt", "style", "width", "height"},
    "div": {"style", "align"},
    "p": {"style", "align"},
    "span": {"style"},
    "h1": {"style", "align"},
    "h2": {"style", "align"},
    "h3": {"style", "align"},
    "ul": {"style"},
    "ol": {"style"},
    "li": {"style"},
    "hr": {"style"},
    "strong": {"style"},
    "em": {"style"},
    "br": set(),
    "table": {"style", "align", "width", "cellpadding", "cellspacing", "border"},
    "tbody": {"style"},
    "thead": {"style"},
    "tr": {"style", "align"},
    "td": {"style", "align", "width", "colspan", "valign"},
    "th": {"style", "align", "width", "colspan", "valign"},
}
BLOCKED_CONTENT_TAGS = {
    "embed",
    "head",
    "iframe",
    "noscript",
    "object",
    "script",
    "style",
    "svg",
    "template",
    "title",
}
ALLOWED_CSS_PROPERTIES = {
    "background-color",
    "border",
    "border-bottom",
    "border-color",
    "border-left",
    "border-radius",
    "border-right",
    "border-style",
    "border-top",
    "border-width",
    "color",
    "display",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "height",
    "letter-spacing",
    "line-height",
    "list-style",
    "list-style-type",
    "margin",
    "margin-bottom",
    "margin-left",
    "margin-right",
    "margin-top",
    "max-height",
    "max-width",
    "min-height",
    "min-width",
    "overflow",
    "padding",
    "padding-bottom",
    "padding-left",
    "padding-right",
    "padding-top",
    "text-align",
    "text-decoration",
    "vertical-align",
    "white-space",
    "width",
}
_UNSAFE_CSS = re.compile(
    r"url\s*\(|expression\s*\(|javascript:|@import|behavior\s*:|-moz-binding|\\\\",
    re.IGNORECASE,
)

_HTML_HINTS = (
    "<div",
    "<html",
    "<h1",
    "<h2",
    "<h3",
    "<p",
    "<table",
    "<span",
    "<ul",
    "<ol",
    "<body",
    "<main",
    "<article",
    "<section",
    "<header",
)


def is_safe_public_url(url: str | None) -> bool:
    if not url:
        return False

    candidate = url.strip()
    if not candidate:
        return False

    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc or parsed.username or parsed.password:
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    normalized_host = hostname.rstrip(".").lower()
    if normalized_host == "localhost":
        return False

    try:
        ip_value = ipaddress.ip_address(normalized_host)
    except ValueError:
        if "." not in normalized_host:
            return False
    else:
        if (
            ip_value.is_private
            or ip_value.is_loopback
            or ip_value.is_link_local
            or ip_value.is_multicast
            or ip_value.is_reserved
            or ip_value.is_unspecified
        ):
            return False

    return True


def sanitize_css(style: str | None) -> str | None:
    if not style or not style.strip():
        return None

    parts: list[str] = []
    for declaration in style.split(";"):
        if ":" not in declaration:
            continue
        property_name, value = declaration.split(":", 1)
        name = property_name.strip().lower()
        cleaned_value = value.strip()
        if name not in ALLOWED_CSS_PROPERTIES or not cleaned_value:
            continue
        if "\\" in cleaned_value or _UNSAFE_CSS.search(cleaned_value):
            continue
        if any(char in cleaned_value for char in ("<", ">", "{", "}")):
            continue
        parts.append(f"{name}: {cleaned_value}")

    if not parts:
        return None
    return "; ".join(parts)


def looks_like_html(text: str) -> bool:
    if not text or not text.strip():
        return False
    stripped = strip_markdown_code_fences(text).strip()
    first_tag = stripped.find("<")
    if first_tag != -1:
        stripped = stripped[first_tag:].strip()
    lower = stripped.lower()
    if not lower.startswith("<"):
        return False
    return any(hint in lower for hint in _HTML_HINTS)


def _preprocess_html(raw_html: str) -> str:
    if not raw_html or not raw_html.strip():
        return ""
    cleaned = strip_markdown_code_fences(raw_html)
    cleaned = re.sub(r"<!DOCTYPE[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(
        r"<head(?:\s+[^>]*)?>.*?</head>",
        "",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    cleaned = re.sub(
        r"<(?:script|style|svg|iframe|noscript|title|template)(?:\s+[^>]*)?>.*?</(?:script|style|svg|iframe|noscript|title|template)>",
        "",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    first_tag = cleaned.find("<")
    if first_tag != -1:
        cleaned = cleaned[first_tag:]
    return cleaned.strip()


class SafeHtmlSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.output: list[str] = []
        self.block_depth = 0
        self.tag_stack: list[str] = []

    def _render_attrs(self, attrs: list[tuple[str, str | None]]) -> str:
        return "".join(
            f' {name}="{html.escape(value, quote=True)}"'
            for name, value in attrs
            if value is not None
        )

    def _sanitize_attrs(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> tuple[str, list[tuple[str, str | None]]] | None:
        allowed_attrs = ALLOWED_GLOBAL_ATTRIBUTES | ALLOWED_TAG_ATTRIBUTES.get(
            tag, set()
        )
        sanitized_attrs: list[tuple[str, str | None]] = []

        for name, value in attrs:
            attr_name = name.lower()
            if attr_name.startswith("on") or attr_name not in allowed_attrs:
                continue
            if tag == "a" and attr_name == "href" and not is_safe_public_url(value):
                continue
            if tag == "img" and attr_name == "src" and not is_safe_public_url(value):
                return None
            if attr_name == "style":
                value = sanitize_css(value)
                if value is None:
                    continue
            sanitized_attrs.append((attr_name, value))

        if tag == "a" and not any(name == "href" for name, _ in sanitized_attrs):
            tag = "span"
            sanitized_attrs = [
                (name, value)
                for name, value in sanitized_attrs
                if name in ALLOWED_TAG_ATTRIBUTES["span"]
            ]

        return tag, sanitized_attrs

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in BLOCKED_CONTENT_TAGS:
            self.block_depth += 1
            return
        if self.block_depth > 0 or tag not in ALLOWED_HTML_TAGS:
            return

        sanitized = self._sanitize_attrs(tag, attrs)
        if sanitized is None:
            return
        output_tag, sanitized_attrs = sanitized
        self.output.append(f"<{output_tag}{self._render_attrs(sanitized_attrs)}>")

        if output_tag not in VOID_HTML_TAGS:
            self.tag_stack.append(output_tag)

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if (
            tag in BLOCKED_CONTENT_TAGS
            or self.block_depth > 0
            or tag not in ALLOWED_HTML_TAGS
        ):
            return

        sanitized = self._sanitize_attrs(tag, attrs)
        if sanitized is None:
            return
        output_tag, sanitized_attrs = sanitized
        self.output.append(f"<{output_tag}{self._render_attrs(sanitized_attrs)} />")

    def handle_endtag(self, tag: str) -> None:
        if tag in BLOCKED_CONTENT_TAGS:
            if self.block_depth > 0:
                self.block_depth -= 1
            return
        if self.block_depth > 0 or not self.tag_stack:
            return

        stacked = self.tag_stack[-1]
        if tag == stacked or (tag == "a" and stacked == "span"):
            self.output.append(f"</{self.tag_stack.pop()}>")

    def handle_data(self, data: str) -> None:
        if self.block_depth == 0:
            self.output.append(html.escape(data))

    def handle_entityref(self, name: str) -> None:
        if self.block_depth == 0:
            self.output.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self.block_depth == 0:
            self.output.append(f"&#{name};")

    def get_html(self) -> str:
        while self.tag_stack:
            self.output.append(f"</{self.tag_stack.pop()}>")
        return "".join(self.output)


def sanitize_newsletter_html(raw_html: str) -> str:
    cleaned = _preprocess_html(raw_html)
    if not cleaned:
        return ""
    sanitizer = SafeHtmlSanitizer()
    sanitizer.feed(cleaned)
    sanitizer.close()
    return sanitizer.get_html().strip()
