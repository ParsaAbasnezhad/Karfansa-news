
from django.core.management.base import BaseCommand

from apps.news.services.news_scorer import classify_unclassified_news


class Command(BaseCommand):
    help = "Classify unclassified news articles"

    def handle(self, *args, **options):
        self.stdout.write("Starting news classification...")

        results = classify_unclassified_news()

        for result in results:
            self.stdout.write(
                f'Title: {result["title"][:70]}'
            )

            self.stdout.write(
                f'Topic: {result["topic"] or "بدون موضوع"}'
            )

            self.stdout.write(
                f'Score: {result["score"]}/100'
            )

            self.stdout.write("-" * 50)

        self.stdout.write(
            self.style.SUCCESS(
                f"Classification completed: {len(results)} news articles."
            )
        )
