from django.db import migrations, models


def migrate_existing_subscriptions(apps, schema_editor):
    MobileDeviceToken = apps.get_model('denunciations', 'MobileDeviceToken')
    Incident = apps.get_model('denunciations', 'Incident')

    for device in MobileDeviceToken.objects.exclude(code_suivi='').iterator():
        incident_id = device.incident_id
        if incident_id is None:
            incident_id = (
                Incident.objects.filter(code_suivi=device.code_suivi)
                .values_list('id', flat=True)
                .first()
            )
        if incident_id is not None:
            device.tracked_incidents.add(incident_id)


class Migration(migrations.Migration):

    dependencies = [
        ('denunciations', '0014_mobiledevicetoken_staff_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobiledevicetoken',
            name='tracked_incidents',
            field=models.ManyToManyField(
                blank=True,
                related_name='subscribed_device_tokens',
                to='denunciations.incident',
            ),
        ),
        migrations.RunPython(
            migrate_existing_subscriptions,
            migrations.RunPython.noop,
        ),
    ]