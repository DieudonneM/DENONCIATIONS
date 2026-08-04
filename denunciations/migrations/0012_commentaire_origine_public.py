from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('denunciations', '0011_mobiledevicetoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentaire',
            name='origine_public',
            field=models.CharField(
                choices=[('ministere', 'Ministère'), ('denonciateur', 'Dénonciateur')],
                db_index=True,
                default='ministere',
                help_text='Origine des commentaires publics (ministère ou dénonciateur).',
                max_length=20,
            ),
        ),
    ]
