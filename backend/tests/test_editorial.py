"""Editorial publication, public API, and staff workflow regressions."""

import io
from datetime import timedelta
from urllib.parse import quote

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory, override_settings
from django.utils import timezone
from PIL import Image

from apps.editorial.admin import PUBLISH_PERMISSION, EditorialArticleAdmin, publish_articles
from apps.editorial.models import (
    EditorialArticle,
    EditorialCategory,
    EditorialImage,
    EditorialTag,
    featured_image_path,
)


def article(title: str, **kwargs) -> EditorialArticle:
    summary = kwargs.pop("summary", f"خلاصه {title}")
    content = kwargs.pop("content", f"<p>متن کامل {title}</p>")
    return EditorialArticle.objects.create(
        title=title,
        summary=summary,
        content=content,
        **kwargs,
    )


@pytest.mark.django_db
def test_model_slug_reading_time_and_rich_text_safety() -> None:
    first = article(
        "گزارش بازار امروز",
        content="<h2 onclick='alert(1)'>تیتر</h2><script>alert(2)</script>"
        "<p>خبر <a href='javascript:alert(3)'>بد</a> "
        "<a href='https://example.com'>خوب</a></p>",
    )
    second = article("گزارش بازار امروز")
    assert first.slug == "گزارش-بازار-امروز"
    assert second.slug == "گزارش-بازار-امروز-2"
    assert "onclick" not in first.content
    assert "script" not in first.content
    assert "javascript:" not in first.content
    assert '<a href="https://example.com" rel="noopener noreferrer">' in first.content
    assert first.reading_time == 1
    assert featured_image_path(first, "original.jpg") != featured_image_path(first, "original.jpg")


@override_settings(MEDIA_URL="/media/")
@pytest.mark.django_db
def test_image_variants_have_real_widths_and_random_paths(tmp_path, client: Client) -> None:
    with override_settings(MEDIA_ROOT=tmp_path):
        buffer = io.BytesIO()
        Image.new("RGB", (1200, 675), "#bb5533").save(buffer, format="JPEG")
        upload = SimpleUploadedFile("cover.jpg", buffer.getvalue(), content_type="image/jpeg")
        item = article(
            "تصویر خبر",
            featured_image=upload,
            status=EditorialArticle.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(minutes=1),
        )
        gallery = EditorialImage.objects.create(
            article=item,
            image=SimpleUploadedFile("gallery.jpg", buffer.getvalue(), content_type="image/jpeg"),
        )
        assert item.featured_image.name.startswith("editorial/featured/")
        assert "cover.jpg" not in item.featured_image.name
        assert set(item.featured_image_variants) == {"480", "960", "1200"}
        assert set(gallery.variants) == {"480", "960", "1200"}
        response = client.get(f"/api/v1/editorial/{item.slug}/")
        payload = response.json()["item"]
        assert payload["featured_image_width"] == 1200
        assert payload["featured_image_height"] == 675
        assert "/media/" in payload["featured_image_srcset"]
        assert " 480w" in payload["featured_image_srcset"]
        assert " 1200w" in payload["gallery"][0]["image_srcset"]


@pytest.mark.django_db
def test_public_visibility_priority_filters_and_detail(client: Client) -> None:
    now = timezone.now()
    category = EditorialCategory.objects.create(name="اقتصاد")
    tag = EditorialTag.objects.create(name="بورس")
    ordinary = article(
        "خبر عادی",
        category=category,
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(days=2),
        priority=1,
        source_url="https://example.com/ordinary",
    )
    ordinary.tags.add(tag)
    high = article(
        "خبر مهم",
        category=category,
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(days=1),
        priority=90,
    )
    pinned = article(
        "خبر سنجاق",
        category=category,
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now - timedelta(days=3),
        is_pinned=True,
    )
    draft = article("پیش‌نویس پنهان")
    review = article("در صف بررسی", status=EditorialArticle.Status.PENDING_REVIEW)
    future = article(
        "انتشار آینده",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=now + timedelta(days=1),
    )
    archived = article("خبر آرشیوی", status=EditorialArticle.Status.ARCHIVED)

    featured = client.get("/api/v1/editorial/featured/")
    assert featured.status_code == 200
    assert featured.json()["featured"]["id"] == pinned.pk
    assert [item["id"] for item in featured.json()["secondary"]] == [high.pk, ordinary.pk]

    latest = client.get("/api/v1/editorial/latest/")
    assert [item["id"] for item in latest.json()["results"]] == [high.pk, ordinary.pk, pinned.pk]

    listing = client.get(
        "/api/v1/editorial/", {"category": category.slug, "ordering": "priority", "page_size": 2}
    )
    assert listing.status_code == 200
    body = listing.json()
    assert body["count"] == 3
    assert body["total_pages"] == 2
    assert [item["id"] for item in body["results"]] == [pinned.pk, high.pk]
    assert body["categories"] == [
        {
            "id": category.pk,
            "slug": category.slug,
            "name": category.name,
            "seo_title": "",
            "seo_description": "",
            "seo_social_image_url": "",
            "seo_noindex": False,
            "seo_canonical_url": "",
        }
    ]

    searched = client.get("/api/v1/editorial/", {"q": "عادی"}).json()
    assert searched["count"] == 1
    assert searched["results"][0]["source_url"] == "https://example.com/ordinary"
    assert searched["results"][0]["tags"] == ["بورس"]
    assert client.get("/api/v1/editorial/", {"ordering": "status"}).status_code == 400
    assert client.get("/api/v1/editorial/", {"page_size": 100}).status_code == 422

    detail = client.get(f"/api/v1/editorial/{ordinary.slug}/")
    assert detail.status_code == 200
    assert detail.json()["item"]["source_url"] == "https://example.com/ordinary"
    assert detail.json()["item"]["reading_time"] == 1
    assert detail.json()["related"][0]["id"] == high.pk
    client.get(f"/api/v1/editorial/{ordinary.slug}/")
    ordinary.refresh_from_db()
    assert ordinary.view_count == 1
    for hidden in (draft, review, future, archived):
        assert client.get(f"/api/v1/editorial/{hidden.slug}/").status_code == 404


@pytest.mark.django_db
def test_staff_publish_permission_preview_and_sitemap(client: Client) -> None:
    user_model = get_user_model()
    writer = user_model.objects.create_user(username="writer", password="secret", is_staff=True)
    editor = user_model.objects.create_user(username="editor", password="secret", is_staff=True)
    permissions = Permission.objects.filter(
        content_type__app_label="editorial",
        codename__in=["view_editorialarticle", "change_editorialarticle"],
    )
    writer.user_permissions.add(*permissions)
    editor.user_permissions.add(*permissions)
    editor.user_permissions.add(Permission.objects.get(codename="publish_editorialarticle"))
    draft = article("داخلی", content="<p>متن محرمانه</p>")
    client.force_login(writer)
    preview = client.get(f"/admin/editorial/editorialarticle/{draft.pk}/preview/")
    assert preview.status_code == 200
    assert "متن محرمانه" in preview.content.decode()
    assert client.get(f"/api/v1/editorial/{draft.slug}/").status_code == 404

    model_admin = EditorialArticleAdmin(EditorialArticle, admin.site)
    request = RequestFactory().post("/admin/editorial/editorialarticle/")
    request.user = writer
    draft.status = EditorialArticle.Status.PUBLISHED
    with pytest.raises(PermissionDenied):
        model_admin.save_model(request, draft, None, True)
    draft.refresh_from_db()
    assert draft.status == EditorialArticle.Status.DRAFT
    assert "publish_articles" not in model_admin.get_actions(request)

    request.user = editor
    assert editor.has_perm(PUBLISH_PERMISSION)
    model_admin.message_user = lambda *args, **kwargs: None
    publish_articles(model_admin, request, EditorialArticle.objects.filter(pk=draft.pk))
    draft.refresh_from_db()
    assert draft.status == EditorialArticle.Status.PUBLISHED
    assert draft.published_at is not None
    assert (
        client.post(
            f"/admin/editorial/editorialarticle/{draft.pk}/change/",
            {"title": "تغییر غیرمجاز"},
        ).status_code
        == 403
    )

    client.logout()
    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert f"/editorial/{quote(draft.slug, safe='')}" in sitemap.content.decode()
    assert "/editorial</loc>" in sitemap.content.decode()


@pytest.mark.django_db
def test_admin_can_create_draft_with_rich_text(client: Client) -> None:
    user = get_user_model().objects.create_superuser(
        username="chief", password="secret", email="chief@example.com"
    )
    client.force_login(user)
    add_url = "/admin/editorial/editorialarticle/add/"
    form = client.get(add_url)
    assert form.status_code == 200
    assert b"editorial/editor.js" in form.content
    assert b"editorial/seo-admin.js" in form.content
    response = client.post(
        add_url,
        {
            "title": "گزارش تحریریه",
            "slug": "",
            "summary": "خلاصه گزارش تحریریه",
            "content": "<h2>تیتر میانی</h2><p>متن خبر</p>",
            "category": "",
            "author": "",
            "editor": "",
            "source_name": "",
            "source_url": "",
            "status": EditorialArticle.Status.DRAFT,
            "published_at": "",
            "priority": "0",
            "seo_title": "",
            "seo_description": "",
            "gallery-TOTAL_FORMS": "0",
            "gallery-INITIAL_FORMS": "0",
            "gallery-MIN_NUM_FORMS": "0",
            "gallery-MAX_NUM_FORMS": "1000",
            "_save": "Save",
        },
    )
    assert response.status_code == 302, (
        response.context["adminform"].form.errors,
        [inline.formset.errors for inline in response.context["inline_admin_formsets"]],
    )
    created = EditorialArticle.objects.get(title="گزارش تحریریه")
    assert created.author_id == user.pk
    assert created.status == EditorialArticle.Status.DRAFT
    assert created.slug == "گزارش-تحریریه"


@pytest.mark.django_db
def test_editorial_seo_overrides_validate_public_canonical_targets(client: Client) -> None:
    published = article(
        "گزارش اصلی",
        status=EditorialArticle.Status.PUBLISHED,
        published_at=timezone.now() - timedelta(hours=1),
    )
    duplicate = article(
        "نسخه تکراری",
        status=EditorialArticle.Status.PUBLISHED,
        seo_title="گزارش بازار",
        seo_description="خلاصه اختصاصی گزارش بازار",
        seo_noindex=True,
        seo_canonical_url=f"https://karfansa.news.ir/editorial/{published.slug}",
    )
    payload = client.get(f"/api/v1/editorial/{duplicate.slug}/").json()["item"]
    assert payload["seo_title"] == "گزارش بازار"
    assert payload["seo_noindex"] is True
    assert payload["seo_canonical_url"].endswith(published.slug)

    duplicate.seo_canonical_url = "https://example.com/editorial/other"
    with pytest.raises(ValidationError):
        duplicate.full_clean()
    duplicate.seo_canonical_url = "https://karfansa.news.ir/editorial/missing"
    with pytest.raises(ValidationError):
        duplicate.save()

    category = EditorialCategory.objects.create(name="بازار")
    empty = EditorialCategory(
        name="صنعت",
        seo_canonical_url=f"https://karfansa.news.ir/editorial/category/{category.slug}",
    )
    with pytest.raises(ValidationError):
        empty.full_clean()
    published.category = category
    published.save()
    empty.full_clean()
    empty.save()
