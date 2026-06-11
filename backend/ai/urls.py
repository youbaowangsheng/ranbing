from django.urls import path
from .views import (
    AIRecognizeIntentView, AIExtractTagsView, AIMatchView, AIGenerateScriptView,
    AIChatProxyView, AIChatProxyV2View, AISupplyMatchesView,
    ai_publish_guide
)

urlpatterns = [
    path('recognize-intent/', AIRecognizeIntentView.as_view(), name='ai-recognize-intent'),
    path('extract-tags/', AIExtractTagsView.as_view(), name='ai-extract-tags'),
    path('match/', AIMatchView.as_view(), name='ai-match'),
    path('generate-script/', AIGenerateScriptView.as_view(), name='ai-generate-script'),
    path('chat/', AIChatProxyView.as_view(), name='ai-chat'),
    path('chat-v2/', AIChatProxyV2View.as_view(), name='ai-chat-v2'),
    path('supply-matches/', AISupplyMatchesView.as_view(), name='ai-supply-matches'),
    path('publish-guide/', ai_publish_guide, name='ai_publish_guide'),
]
