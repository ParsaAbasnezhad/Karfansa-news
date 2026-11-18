"""Sitemap for the public editorial pages."""

from urllib.parse import quote
from xml.etree.ElementTree import Element, SubElement, tostring

from django.http import HttpRequest, HttpResponse

from .selectors import public_articles


def editorial_sitemap(request: HttpRequest) -> HttpResponse:
    root = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    index = SubElement(root, "url")
    SubElement(index, "loc").text = request.build_absolute_uri("/editorial")
    articles = (
        public_articles()
        .select_related(None)
        .prefetch_related(None)
        .order_by("-published_at", "-id")
        .values_list("slug", "updated_at")[:49999]
    )
    for slug, updated_at in articles.iterator(chunk_size=1000):
        entry = SubElement(root, "url")
        SubElement(entry, "loc").text = request.build_absolute_uri(
            f"/editorial/{quote(slug, safe='')}"
        )
        SubElement(entry, "lastmod").text = updated_at.date().isoformat()
    xml = tostring(root, encoding="utf-8", xml_declaration=True)
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")
