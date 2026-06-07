"""
Django Template Views for Ranbing pages — no API, direct template render.

This module is a backward-compatibility shim.
All views have been split into pages/views_split/ submodules.
"""
from .views_split import (
    login_view, register_view, send_code_view, captcha_image_view,
    bind_account_view, wx_login_view, logout_view, test_page,
    HomeView,
    SupplyDemandView, PublishSupplyView, SupplyDetailView, send_supply_message,
    MessageListView, MessageDetailView, send_message,
    ProfileView, PublicProfileView, ProfileSettingsView, ProfileEditView,
    ProfilePreviewView, WorkHistoryView, TagSelectorView, CertificationView,
    ActivityListView, ActivityDetailView, PublishActivityView,
    enroll_activity, cancel_enrollment,
    CommunityView, CommunityDetailView, join_community,
    AIAssistantView, AIChatProxyView, AITagsPopupView,
    NetworkGraphView, AlumniFilterView,
    FollowupView,
    SearchView,
)
