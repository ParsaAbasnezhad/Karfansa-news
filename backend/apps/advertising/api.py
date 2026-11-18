"""Public advertising slides for the homepage carousel."""

from django.http import HttpRequest
from ninja import Router

from apps.advertising import selectors
from apps.advertising.schemas import AdvertisementSlideListOut, AdvertisementSlideOut
from apps.advertising.validators import safe_destination_url

router = Router()


def _media_url(field) -> str:
    """Return a same-origin media path so Vite/nginx proxies can serve uploads."""
    if not field:
        return ""
    return field.url


@router.get("/slides/", response=AdvertisementSlideListOut, operation_id="advertising_slides")
def advertising_slides(request: HttpRequest) -> AdvertisementSlideListOut:
    slides = list(selectors.list_public_slides())
    results = [
        AdvertisementSlideOut(
            id=slide.id,
            title=slide.title,
            subtitle=slide.subtitle,
            description=slide.description,
            image_desktop=_media_url(slide.image_desktop),
            image_mobile=_media_url(slide.image_mobile) or _media_url(slide.image_desktop),
            button_text=slide.button_text,
            button_url=safe_destination_url(slide.button_url),
            sort_order=slide.sort_order,
        )
        for slide in slides
    ]
    return AdvertisementSlideListOut(results=results, count=len(results))
