from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactmessage",
            name="phone",
            field=models.CharField(default="", max_length=16, verbose_name="شماره موبایل"),
            preserve_default=False,
        ),
    ]
