from django.db import migrations, models
import django.db.models.deletion


def seed_topics(apps, schema_editor):
    from apps.news.topic_catalog import TOPIC_CATALOG

    NewsTopic = apps.get_model("news", "NewsTopic")
    for item in TOPIC_CATALOG:
        topic, created = NewsTopic.objects.get_or_create(
            name=item["name"],
            defaults={
                "keywords": item["keywords"],
                "is_active": True,
                "position": item["position"],
            },
        )
        if created:
            continue
        updates = []
        if not topic.keywords:
            topic.keywords = item["keywords"]
            updates.append("keywords")
        if topic.position == 0:
            topic.position = item["position"]
            updates.append("position")
        if updates:
            topic.save(update_fields=updates)


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0002_tasnim_headline_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="newssource",
            name="last_fetch_error",
            field=models.CharField(blank=True, max_length=300, verbose_name="خطای آخرین دریافت"),
        ),
        migrations.AddField(
            model_name="newssource",
            name="last_fetch_status",
            field=models.CharField(blank=True, max_length=16, verbose_name="وضعیت آخرین دریافت"),
        ),
        migrations.AddField(
            model_name="newstopic",
            name="position",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش"),
        ),
        migrations.AlterModelOptions(
            name="newstopic",
            options={
                "ordering": ["position", "name"],
                "verbose_name": "موضوع خبری",
                "verbose_name_plural": "موضوعات خبری",
            },
        ),
        migrations.CreateModel(
            name="NewsIntake",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("original_url", models.URLField(max_length=1000, unique=True, verbose_name="لینک اصلی")),
                ("guid", models.CharField(blank=True, max_length=1000, verbose_name="شناسه RSS")),
                ("title", models.CharField(max_length=300, verbose_name="عنوان")),
                (
                    "status",
                    models.CharField(
                        choices=[("approved", "تأیید شده"), ("rejected", "رد شده")],
                        max_length=16,
                        verbose_name="وضعیت بررسی",
                    ),
                ),
                ("score", models.PositiveSmallIntegerField(default=0, verbose_name="امتیاز ارتباط")),
                ("topic_name", models.CharField(blank=True, max_length=100, verbose_name="موضوع")),
                ("reviewed_at", models.DateTimeField(auto_now_add=True, verbose_name="زمان بررسی")),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="intakes",
                        to="news.newssource",
                        verbose_name="منبع",
                    ),
                ),
            ],
            options={
                "verbose_name": "بررسی خبر",
                "verbose_name_plural": "بررسی اخبار",
                "ordering": ["-reviewed_at"],
            },
        ),
        migrations.RunPython(seed_topics, migrations.RunPython.noop),
    ]
