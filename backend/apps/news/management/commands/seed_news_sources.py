from django.core.management.base import BaseCommand

from apps.news.models import NewsSource
from apps.news.source_catalog import SOURCE_CATALOG


class Command(BaseCommand):
    help = (
        "Add the checked Persian business and economy RSS sources without overwriting admin choices"
    )

    def handle(self, *args, **options):
        created_count = 0
        existing_count = 0

        for source_data in SOURCE_CATALOG:
            _, created = NewsSource.objects.get_or_create(
                rss_url=source_data["rss_url"],
                defaults={**source_data, "is_active": True},
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Added: {source_data['name']}"))
            else:
                existing_count += 1
                self.stdout.write(f"Exists, unchanged: {source_data['name']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Source seed complete: {created_count} added, {existing_count} already present."
            )
        )
