from apps.pages.defaults import (
    ABOUT_DEFAULTS,
    ABOUT_FEATURE_DEFAULTS,
    CONTACT_DEFAULTS,
    CONTACT_FAQ_DEFAULTS,
)
from apps.pages.models import AboutFeature, AboutPage, ContactFAQ, ContactPage


def ensure_about_page() -> AboutPage:
    page, created = AboutPage.objects.get_or_create(pk=1, defaults=ABOUT_DEFAULTS)
    if created or not page.features.exists():
        for item in ABOUT_FEATURE_DEFAULTS:
            AboutFeature.objects.get_or_create(
                page=page,
                kind=item["kind"],
                title=item["title"],
                defaults={
                    "label": item["label"],
                    "body": item["body"],
                    "sort_order": item["sort_order"],
                    "is_active": True,
                },
            )
    return page


def ensure_contact_page() -> ContactPage:
    page, created = ContactPage.objects.get_or_create(pk=1, defaults=CONTACT_DEFAULTS)
    if created or not page.faqs.exists():
        for item in CONTACT_FAQ_DEFAULTS:
            ContactFAQ.objects.get_or_create(
                page=page,
                question=item["question"],
                defaults={
                    "answer": item["answer"],
                    "sort_order": item["sort_order"],
                    "is_active": True,
                },
            )
    return page
