"""Pages app URL routing — Django template page views."""
from django.urls import path
from . import views

urlpatterns = [
    # Test
    path('test/', views.test_page, name='test'),

    # Auth — 登录/注册/验证码
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('send-code/', views.send_code_view, name='send_code'),
    path('captcha/', views.captcha_image_view, name='captcha_image'),

    # Account binding (微信)
    path('account/bind/', views.bind_account_view, name='bind_account'),
    path('account/wx/login/', views.wx_login_view, name='wx_login'),

    # Core pages
    path('home/', views.HomeView.as_view(), name='home'),
    path('supply/demand/', views.SupplyDemandView.as_view(), name='supply_demand'),
    path('supply/publish/', views.PublishSupplyView.as_view(), name='publish_supply'),
    path('supply/<uuid:uuid>/', views.SupplyDetailView.as_view(), name='supply_detail'),
    path('supply/<uuid:uuid>/message/', views.send_supply_message, name='supply_message'),
    path('messages/', views.MessageListView.as_view(), name='message_list'),
    path('messages/inbox/', views.MessageListView.as_view(), name='message_inbox'),
    path('messages/<uuid:uuid>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('messages/send/', views.send_message, name='send_message'),
    path('profile/', views.ProfileView.as_view(), name='my_profile'),
    path('profile/<uuid:uuid>/', views.ProfileView.as_view(), name='profile_view'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/settings/', views.ProfileSettingsView.as_view(), name='profile_settings'),
    path('profile/work-history/', views.WorkHistoryView.as_view(), name='work_history'),
    path('profile/tags/', views.TagSelectorView.as_view(), name='tag_selector'),
    path('profile/preview/', views.ProfilePreviewView.as_view(), name='profile_preview'),
    path('pub/<uuid:uuid>/', views.PublicProfileView.as_view(), name='pub_profile'),
    path('activities/', views.ActivityListView.as_view(), name='activity_list'),
    path('activities/publish/', views.PublishActivityView.as_view(), name='publish_activity'),
    path('activities/<int:id>/', views.ActivityDetailView.as_view(), name='activity_detail'),
    path('activities/<int:id>/enroll/', views.enroll_activity, name='enroll_activity'),
    path('activities/<int:id>/cancel/', views.cancel_enrollment, name='cancel_enrollment'),
    path('community/', views.CommunityView.as_view(), name='community'),
    path('community/<int:id>/join/', views.join_community, name='join_community'),
    path('ai/', views.AIAssistantView.as_view(), name='ai_assistant'),
    path('ai/tags/popup/', views.AITagsPopupView.as_view(), name='ai_tags_popup'),
    path('network/', views.NetworkGraphView.as_view(), name='network_graph'),
    path('network/filter/', views.AlumniFilterView.as_view(), name='alumni_filter'),
    path('followup/', views.FollowupView.as_view(), name='followup'),
    path('certification/', views.CertificationView.as_view(), name='certification'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('community/<int:id>/', views.CommunityDetailView.as_view(), name='community_detail'),

    # Root redirect
    path('', views.HomeView.as_view(), name='root'),
]
