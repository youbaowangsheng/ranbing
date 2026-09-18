"""
[已废弃] 原用于创建 Card（电子名片）表。

问题：此处的 Card 定义（profile 外键 + 无展示配置字段）与最终采用的
supplies.models.Card（owner 一对一 + 展示配置字段）不一致，属于历史遗留。

为避免建出错误的表结构，改为空操作（no-op），保留迁移节点以维持依赖图
完整（profiles/0006_merge_20260608_0727 依赖本迁移）。
Card 表的实际创建见 supplies/migrations/0006_create_card.py。
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_add_notifications'),
    ]

    operations = [
        # 空操作：Card 表由 supplies.0006_create_card 负责创建
    ]
