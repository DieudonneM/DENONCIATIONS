from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_finalize_core_province'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='temp_password_used_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]