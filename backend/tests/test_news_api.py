from datetime import timedelta

import pytest
from django.test import Client, override_settings
from django.utils import timezone

from apps.contact.models import ContactMessage
from apps.news.models import News, NewsSource, NewsTopic

LOCMEM_CACHE = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}


@pytest.mark.django_db
def test_public_news_list_detail_and_headlines(client: Client) -> None:
    active_before = NewsSource.objects.filter(is_active=True).count()
    source = NewsSource.objects.create(
        name="تسنیم",
        rss_url="https://example.com/rss.xml",
        website_url="https://example.com",
        is_active=True,
        is_headline_source=True,
    )
    topic, _ = NewsTopic.objects.get_or_create(
        name="اقتصاد",
        defaults={"keywords": ["اقتصاد"], "is_active": True},
    )
    other, _ = NewsTopic.objects.get_or_create(
        name="انرژی",
        defaults={"keywords": ["نفت"], "is_active": True},
    )
    published = timezone.now()
    earlier = published - timedelta(days=1)
    lead = News.objects.create(
        source=source,
        topic=topic,
        title="رشد اقتصاد",
        summary="خلاصه خبر اقتصادی",
        original_url="https://example.com/a",
        image_url="https://example.com/a.jpg",
        published_at=published,
        score=80,
        is_published=True,
        is_pinned=True,
    )
    News.objects.create(
        source=source,
        topic=other,
        title="صادرات انرژی",
        summary="خلاصه انرژی",
        original_url="https://example.com/b",
        published_at=earlier,
        score=40,
        is_published=True,
    )
    News.objects.create(
        source=source,
        topic=topic,
        title="خبر حذف‌شده",
        summary="امتیاز کافی ندارد",
        original_url="https://example.com/c",
        published_at=published,
        score=0,
    )
    News.objects.create(
        source=source,
        topic=topic,
        title="خبر تأییدنشده",
        summary="امتیاز بالاست اما در صف انتشار است",
        original_url="https://example.com/unpublished",
        published_at=published,
        score=75,
        is_published=False,
    )

    listed = client.get("/api/v1/news/", {"q": "رشد", "ordering": "-published_at"})
    assert listed.status_code == 200
    body = listed.json()
    assert body["count"] == 1
    assert body["results"][0]["title"] == "رشد اقتصاد"
    assert body["results"][0]["source_name"] == "تسنیم"
    assert body["results"][0]["is_pinned"] is True
    assert "اقتصاد" in body["topics"]
    assert "انرژی" in body["topics"]

    filtered = client.get("/api/v1/news/", {"topic": "انرژی"})
    assert filtered.status_code == 200
    assert filtered.json()["count"] == 1
    assert filtered.json()["results"][0]["topic"] == "انرژی"

    invalid = client.get("/api/v1/news/", {"ordering": "score"})
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "bad_request"

    detail = client.get(f"/api/v1/news/{lead.pk}/")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["item"]["summary"] == "خلاصه خبر اقتصادی"
    assert payload["item"]["source_website"] == "https://example.com"
    assert payload["related"] == []

    hidden = client.get("/api/v1/news/", {"q": "حذف‌شده"})
    assert hidden.json()["count"] == 0
    unpublished = client.get("/api/v1/news/", {"q": "تأییدنشده"})
    assert unpublished.json()["count"] == 0
    missing_id = News.objects.get(original_url="https://example.com/c").pk
    assert client.get(f"/api/v1/news/{missing_id}/").status_code == 404

    headlines = client.get("/api/v1/news/headlines/")
    assert headlines.status_code == 200
    home = headlines.json()
    assert home["featured"]["id"] == lead.pk
    assert home["source_count"] == active_before + 1
    assert home["pinned"][0]["id"] == lead.pk
    topics = [section["topic"] for section in home["sections"]]
    assert topics == ["اقتصاد", "انرژی"]


@override_settings(CACHES=LOCMEM_CACHE)
@pytest.mark.django_db
def test_contact_message_is_stored(client: Client) -> None:
    response = client.post(
        "/api/v1/contact/",
        data={
            "name": "کاربر نمونه",
            "phone": "09121234567",
            "email": "A@Example.com",
            "subject": "اصلاح خبر",
            "message": "این یک پیام آزمایشی است.",
            "website": "",
        },
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["message"] == "پیام شما با موفقیت ثبت شد."
    stored = ContactMessage.objects.get()
    assert stored.phone == "+989121234567"
    assert stored.email == "a@example.com"
    assert stored.is_read is False


@override_settings(CACHES=LOCMEM_CACHE)
@pytest.mark.django_db
def test_contact_honeypot_is_rejected(client: Client) -> None:
    response = client.post(
        "/api/v1/contact/",
        data={
            "name": "ربات",
            "phone": "+989121234567",
            "email": "bot@example.com",
            "subject": "سایر موارد",
            "message": "پیام ناخواسته برای آزمون.",
            "website": "https://spam.example",
        },
        content_type="application/json",
    )
    assert response.status_code == 400
    assert ContactMessage.objects.count() == 0
