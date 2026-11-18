"""A deliberately small HTML vocabulary for staff-written articles."""

from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit

ALLOWED_TAGS = frozenset(
    {
        "p",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "s",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "ul",
        "ol",
        "li",
        "a",
        "hr",
    }
)
VOID_TAGS = frozenset({"br", "hr"})
BLOCKED_TAGS = frozenset(
    {"script", "style", "iframe", "object", "embed", "svg", "math", "form", "template"}
)


def safe_href(value: str) -> bool:
    href = value.strip()
    if not href or any(ord(char) < 32 for char in href):
        return False
    if href.startswith("/") and not href.startswith("//"):
        return True
    parsed = urlsplit(href)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


class ArticleHTMLSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[str] = []
        self.blocked: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in BLOCKED_TAGS:
            self.blocked.append(tag)
            return
        if self.blocked or tag not in ALLOWED_TAGS:
            return
        if tag == "a":
            href = next((value for name, value in attrs if name == "href"), None)
            href_attr = (
                f' href="{escape(href.strip(), quote=True)}" rel="noopener noreferrer"'
                if href and safe_href(href)
                else ""
            )
            self.parts.append(f"<a{href_attr}>")
        else:
            self.parts.append(f"<{tag}>")
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if self.blocked:
            if tag == self.blocked[-1]:
                self.blocked.pop()
            return
        if tag not in self.stack:
            return
        while self.stack:
            opened = self.stack.pop()
            self.parts.append(f"</{opened}>")
            if opened == tag:
                break

    def handle_data(self, data: str) -> None:
        if not self.blocked:
            self.parts.append(escape(data, quote=False))

    def finish(self) -> str:
        while self.stack:
            self.parts.append(f"</{self.stack.pop()}>")
        return "".join(self.parts)


def sanitize_article_html(value: str) -> str:
    parser = ArticleHTMLSanitizer()
    parser.feed(value or "")
    parser.close()
    return parser.finish()
