from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0002_message_audit_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='community',
            name='audit_status',
            field=models.SmallIntegerField(choices=[(0, '待审核'), (1, '审核通过'), (2, '审核拒绝')], default=1),
        ),
        migrations.AddField(
            model_name='community',
            name='audit_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
