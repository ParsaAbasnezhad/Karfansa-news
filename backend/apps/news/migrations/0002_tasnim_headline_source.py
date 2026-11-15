from django.db import migrations, models


TASNIM_RSS_URL = "https://www.tasnimnews.com/fa/rss/feed/0/8/0/"


def add_tasnim_source(apps, schema_editor):
    NewsSource = apps.get_model("news", "NewsSource")
    NewsSource.objects.update_or_create(
        rss_url=TASNIM_RSS_URL,
        defaults={
            "name": "تسنیم - مهم‌ترین اخبار روز",
            "website_url": "https://www.tasnimnews.com/fa/",
            "is_active": True,
            "is_headline_source": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="newssource",
            name="is_headline_source",
            field=models.BooleanField(default=False, verbose_name="منبع تیترهای مهم"),
        ),
        migrations.RunPython(add_tasnim_source, migrations.RunPython.noop),
    ]
