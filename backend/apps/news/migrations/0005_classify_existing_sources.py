from django.db import migrations


def classify_existing_sources(apps, schema_editor):
    NewsSource = apps.get_model("news", "NewsSource")
    categories = {
        "https://tejaratnews.com/feed": "business",
        "https://donya-e-eqtesad.com/rss": "economy",
    }
    for rss_url, category in categories.items():
        NewsSource.objects.filter(rss_url=rss_url).update(category=category)


class Migration(migrations.Migration):
    dependencies = [("news", "0004_rss_monitoring")]

    operations = [
        migrations.RunPython(classify_existing_sources, migrations.RunPython.noop),
    ]
