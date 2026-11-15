import json

from django.core.management.base import BaseCommand

from apps.news.services.rss_fetcher import fetch_all_sources


class Command(BaseCommand):
    help = "Fetch and filter news from active RSS sources"

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Print machine-readable results")

    def handle(self, *args, **options):
        if not options["json"]:
            self.stdout.write("Starting RSS fetching...")

        results = fetch_all_sources()

        metrics = (
            "fetched",
            "accepted",
            "rejected",
            "skipped",
            "duplicates",
            "created",
            "saved",
            "errors",
        )
        totals = {key: sum(r.get(key, 0) for r in results) for key in metrics}
        totals["new_articles"] = totals["saved"]
        totals["sources"] = sum("source" in r for r in results)
        totals["failed_sources"] = sum(r["status"] == "failed" for r in results)
        totals["partial_sources"] = sum(r["status"] == "partial" for r in results)
        totals["run_id"] = results[0].get("run_id") if results else None
        if options["json"]:
            self.stdout.write(
                json.dumps({"sources": results, "totals": totals}, ensure_ascii=False)
            )
            return

        for result in results:
            if result["status"] in ("success", "partial"):
                style = self.style.WARNING if result["status"] == "partial" else self.style.SUCCESS
                self.stdout.write(
                    style(
                        f"{result['source']}: "
                        f"{result['created']} saved, "
                        f"{result['rejected']} rejected, "
                        f"{result['duplicates']} duplicates, "
                        f"{result['errors']} errors"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"{result.get('source', 'RSS')}: "
                        f"{result.get('error', result.get('reason', result['status']))}"
                    )
                )

        self.stdout.write(f"RSS fetching completed. Totals: {totals}")
