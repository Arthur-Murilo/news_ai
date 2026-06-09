import html
import ipaddress
from html.parser import HTMLParser
from urllib.parse import urlsplit

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
}
BLOCKED_CONTENT_TAGS = {"script", "style", "iframe", "object", "embed", "svg"}


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
        allowed_attrs = ALLOWED_GLOBAL_ATTRIBUTES | ALLOWED_TAG_ATTRIBUTES.get(tag, set())
        sanitized_attrs: list[tuple[str, str | None]] = []

        for name, value in attrs:
            attr_name = name.lower()
            if attr_name.startswith("on") or attr_name not in allowed_attrs:
                continue
            if tag == "a" and attr_name == "href" and not is_safe_public_url(value):
                continue
            if tag == "img" and attr_name == "src" and not is_safe_public_url(value):
                return None
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
        if tag in BLOCKED_CONTENT_TAGS or self.block_depth > 0 or tag not in ALLOWED_HTML_TAGS:
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
    sanitizer = SafeHtmlSanitizer()
    sanitizer.feed(raw_html)
    sanitizer.close()
    return sanitizer.get_html()
