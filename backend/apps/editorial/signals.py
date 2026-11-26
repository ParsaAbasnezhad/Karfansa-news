"""Keep public sitemap caches aligned with editorial and CMS changes."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.news.models import News, NewsTopic
from apps.pages.models import AboutPage, ContactPage

from .models import EditorialArticle, EditorialCategory
from .sitemap import invalidate_sitemaps


@receiver(post_save, sender=EditorialArticle)
@receiver(post_delete, sender=EditorialArticle)
@receiver(post_save, sender=EditorialCategory)
@receiver(post_delete, sender=EditorialCategory)
@receiver(post_save, sender=AboutPage)
@receiver(post_save, sender=ContactPage)
@receiver(post_save, sender=News)
@receiver(post_delete, sender=News)
@receiver(post_save, sender=NewsTopic)
@receiver(post_delete, sender=NewsTopic)
def refresh_public_sitemaps(**kwargs: object) -> None:
    invalidate_sitemaps()
