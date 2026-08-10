from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('denunciations', '0013_piecejointe_type_fichier_len_120'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobiledevicetoken',
            name='receives_staff_notifications',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='mobiledevicetoken',
            name='user_role',
            field=models.CharField(
                blank=True,
                choices=[
                    ('travailleur', 'Travailleur'),
                    ('agent', 'Agent'),
                    ('administrateur', 'Administrateur'),
                ],
                db_index=True,
                max_length=20,
            ),
        ),
    ]
