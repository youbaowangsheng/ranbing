import uuid as uuid_lib
from django.db import models


class AIConversation(models.Model):
    """AI对话会话表"""
    CHANNEL_CHOICES = [
        (1, 'AI助手Q'), (2, 'AI发布引导S'), (3, 'AI匹配反馈K')
    ]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='ai_conversations')
    conversation_id = models.UUIDField(default=uuid_lib.uuid4, unique=True)
    channel = models.SmallIntegerField(choices=CHANNEL_CHOICES)
    title = models.CharField(max_length=256, blank=True, default='')
    context_summary = models.TextField(blank=True, default='')
    message_count = models.IntegerField(default=0)
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_conversations'
        ordering = ['-last_message_at']

    def __str__(self):
        return f'conv:{self.conversation_id}'


class AIMessage(models.Model):
    """AI对话消息表"""
    ROLE_CHOICES = [(1, 'user'), (2, 'assistant'), (3, 'system')]

    id = models.BigAutoField(primary_key=True)
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.SmallIntegerField(choices=ROLE_CHOICES)
    content = models.TextField()
    ai_model = models.CharField(max_length=64, blank=True, default='')
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_messages'
        ordering = ['created_at']

    def __str__(self):
        return f'msg:{self.id} role:{self.role}'
