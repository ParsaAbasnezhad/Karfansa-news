"""Public CMS pages for About and Contact."""

from django.http import HttpRequest
from ninja import Router

from apps.pages import selectors
from apps.pages.schemas import (
    AboutFeatureOut,
    AboutPageOut,
    AboutStatisticOut,
    AboutTeamMemberOut,
    ContactFAQOut,
    ContactPageOut,
)

router = Router()


def _media_url(field) -> str:
    """Return a same-origin media path so Vite/nginx proxies can serve uploads."""
    if not field:
        return ""
    return field.url


@router.get("/about/", response=AboutPageOut, operation_id="pages_about")
def pages_about(request: HttpRequest) -> AboutPageOut:
    page = selectors.ensure_about_page()
    features = [
        AboutFeatureOut(
            id=item.id,
            kind=item.kind,
            label=item.label,
            title=item.title,
            body=item.body,
            sort_order=item.sort_order,
        )
        for item in page.features.filter(is_active=True)
    ]
    statistics = [
        AboutStatisticOut(
            id=item.id,
            label=item.label,
            value=item.value,
            sort_order=item.sort_order,
        )
        for item in page.statistics.filter(is_active=True)
    ]
    team_members = [
        AboutTeamMemberOut(
            id=item.id,
            name=item.name,
            role=item.role,
            bio=item.bio,
            photo=_media_url(item.photo),
            sort_order=item.sort_order,
        )
        for item in page.team_members.filter(is_active=True)
    ]
    return AboutPageOut(
        hero_kicker=page.hero_kicker,
        title=page.title,
        subtitle=page.subtitle,
        intro=page.intro,
        hero_image=_media_url(page.hero_image),
        mission_title=page.mission_title,
        mission=page.mission,
        vision_title=page.vision_title,
        vision=page.vision,
        values_title=page.values_title,
        values=page.values,
        goals_title=page.goals_title,
        goals=page.goals,
        mission_image=_media_url(page.mission_image),
        story_eyebrow=page.story_eyebrow,
        story_title=page.story_title,
        story_body=page.story_body,
        cta_eyebrow=page.cta_eyebrow,
        cta_title=page.cta_title,
        closing_text=page.closing_text,
        primary_cta_label=page.primary_cta_label,
        primary_cta_url=page.primary_cta_url,
        secondary_cta_label=page.secondary_cta_label,
        secondary_cta_url=page.secondary_cta_url,
        show_globe=page.show_globe,
        seo_title=page.seo_title or page.title,
        seo_description=page.seo_description or page.intro[:300],
        features=features,
        statistics=statistics,
        team_members=team_members,
        updated_at=page.updated_at,
    )


@router.get("/contact/", response=ContactPageOut, operation_id="pages_contact")
def pages_contact(request: HttpRequest) -> ContactPageOut:
    page = selectors.ensure_contact_page()
    faqs = [
        ContactFAQOut(
            id=item.id,
            question=item.question,
            answer=item.answer,
            sort_order=item.sort_order,
        )
        for item in page.faqs.filter(is_active=True)
    ]
    return ContactPageOut(
        title=page.title,
        description=page.description,
        support_email=page.support_email,
        business_email=page.business_email,
        phone=page.phone,
        whatsapp=page.whatsapp,
        office_address=page.office_address,
        response_hours=page.response_hours,
        map_url=page.map_url,
        instagram_url=page.instagram_url,
        linkedin_url=page.linkedin_url,
        telegram_url=page.telegram_url,
        support_text=page.support_text,
        form_intro=page.form_intro,
        seo_title=page.seo_title or page.title,
        seo_description=page.seo_description or page.description[:300],
        faqs=faqs,
        updated_at=page.updated_at,
    )
