from django.core.management.base import BaseCommand

from apps.news.services.retention import NEWS_RETENTION_DAYS, cleanup_expired_news


class Command(BaseCommand):
    help = "Delete news older than the 35-day retention window"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Count expired news without deleting"
        )

    def handle(self, *args, **options):
        count = cleanup_expired_news(dry_run=options["dry_run"])
        action = "would delete" if options["dry_run"] else "deleted"
        self.stdout.write(
            self.style.SUCCESS(
                f"{count} news item(s) {action}; retention is {NEWS_RETENTION_DAYS} days."
            )
        )
