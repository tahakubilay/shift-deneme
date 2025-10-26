# Generated migration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('schedules', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vardiyaistegi',
            name='hedef_calisan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aldigi_istekler', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='vardiyaistegi',
            name='hedef_vardiya',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='alinmak_istenen_istekler', to='schedules.vardiya'),
        ),
        migrations.AddField(
            model_name='vardiyaistegi',
            name='yedek_calisan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='yedek_atandigi_istekler', to=settings.AUTH_USER_MODEL),
        ),
    ]
