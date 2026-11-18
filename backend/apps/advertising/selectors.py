from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.advertising.models import AdvertisementSlide


def list_public_slides() -> QuerySet[AdvertisementSlide]:
    now = timezone.now()
    return (
        AdvertisementSlide.objects.filter(is_active=True)
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        .order_by("sort_order", "-updated_at")
    )
