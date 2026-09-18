"""
创建 Card（电子名片）表

背景：Card 模型定义在 supplies/models.py，但历史建表迁移错放在
profiles/migrations/0005_add_card_model.py，且字段结构与代码不符，
导致 cards 表从未在数据库建立、/cards/me/ 报 500。

本迁移只做一件事：按当前 supplies.models.Card 的定义建表。
不触碰 supply 的其他字段。
"""
import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # Card 在 profiles 的历史迁移中被创建(0005)又删除(0007)，
        # 这里依赖 0007 确保 profiles 侧状态已收敛，再在 supplies 建表。
        ('profiles', '0007_contacttag_contacttagrelation_and_more'),
        ('supplies', '0005_merge_20260608_0727'),
    ]

    operations = [
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                # 名片内容（小程序编辑页使用）
                ('name', models.CharField(blank=True, default='', max_length=64)),
                ('company', models.CharField(blank=True, default='', max_length=128)),
                ('position', models.CharField(blank=True, default='', max_length=128)),
                ('phone', models.CharField(blank=True, default='', max_length=32)),
                ('wechat', models.CharField(blank=True, default='', max_length=64)),
                ('email', models.CharField(blank=True, default='', max_length=128)),
                ('tags', models.JSONField(default=list)),
                ('is_default', models.BooleanField(default=False)),
                ('visibility', models.SmallIntegerField(default=1)),
                # 展示配置
                ('title', models.CharField(blank=True, default='', max_length=128)),
                ('bio', models.TextField(blank=True, default='')),
                ('show_company', models.BooleanField(default=True)),
                ('show_position', models.BooleanField(default=True)),
                ('show_education', models.BooleanField(default=True)),
                ('show_tags', models.BooleanField(default=True)),
                ('show_contact', models.BooleanField(default=True)),
                ('style_config', models.JSONField(default=dict)),
                ('view_count', models.IntegerField(default=0)),
                ('status', models.SmallIntegerField(choices=[(1, '有效'), (2, '已禁用')], default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='card',
                    to='profiles.profile',
                )),
            ],
            options={
                'db_table': 'cards',
                'ordering': ['-is_default', '-created_at'],
            },
        ),
    ]
