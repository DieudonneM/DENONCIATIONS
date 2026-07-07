from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('denunciations', '0004_incident_department_assigné'),
    ]

    operations = [
        migrations.AddField(
            model_name='incident',
            name='accepted_privacy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='incident',
            name='accepted_privacy_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
