from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("home", "0010_clinic_service")]

    operations = [
        migrations.AddField(
            model_name="teammember",
            name="is_clinic_doctor",
            field=models.BooleanField(default=False, verbose_name="Врач клиники"),
        ),
    ]
