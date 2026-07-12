from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('denunciations', '0005_add_accepted_privacy'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeur',
            name='adresse_complete',
            field=models.TextField(blank=True),
        ),
    ]
