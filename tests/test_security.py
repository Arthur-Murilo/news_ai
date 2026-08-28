from __future__ import annotations

from src.security import looks_like_html, sanitize_css, sanitize_newsletter_html


def test_sanitize_css_keeps_safe_properties():
    assert (
        sanitize_css("color: #111; font-size: 16px") == "color: #111; font-size: 16px"
    )


def test_sanitize_css_drops_url_and_expression():
    assert sanitize_css("background: url(javascript:alert(1))") is None
    assert sanitize_css("width: expression(alert(1))") is None
    assert (
        sanitize_css("color: red; background: url('https://evil.test')") == "color: red"
    )


def test_sanitize_css_rejects_escapes_and_background_shorthand():
    assert sanitize_css(r"background: \75rl(https://evil.test/pixel.gif)") is None
    assert sanitize_css(r"color: \72ed") is None
    html = sanitize_newsletter_html(
        r'<p style="background: \75rl(https://evil.test/x.gif); color: #111">ok</p>'
    )
    assert "evil.test" not in html
    assert "color: #111" in html
    assert "ok" in html


def test_sanitize_html_strips_scripts_and_event_handlers():
    raw = '<div onclick="alert(1)"><script>alert(1)</script><p>ok</p></div>'
    html = sanitize_newsletter_html(raw)
    assert "script" not in html.lower()
    assert "onclick" not in html
    assert "ok" in html


def test_sanitize_html_blocks_unsafe_links_and_images():
    raw = (
        '<a href="javascript:alert(1)">x</a>'
        '<a href="http://127.0.0.1/secret">local</a>'
        '<img src="http://localhost/pixel.gif" />'
        '<a href="https://example.com/news">ok</a>'
    )
    html = sanitize_newsletter_html(raw)
    assert "javascript" not in html
    assert "127.0.0.1" not in html
    assert "<img" not in html
    assert 'href="https://example.com/news"' in html


def test_sanitize_html_ignores_mismatched_end_tags():
    html = sanitize_newsletter_html("<h1>Title</p> more</h1>")
    assert html.startswith("<h1>")
    assert html.endswith("</h1>")
    assert "</p>" not in html


def test_looks_like_html():
    assert looks_like_html("<div>newsletter</div>")
    assert not looks_like_html("Status de validacao: NAO APTO")
