"""
Pages views — split into multiple modules for maintainability.

Import all symbols so pages/urls.py can still do `from pages import views`.
"""
from .auth import (
    login_view, register_view, send_code_view, captcha_image_view,
    bind_account_view, wx_login_view, logout_view,
)
from .home import HomeView
from .supply import SupplyDemandView, PublishSupplyView, SupplyDetailView, send_supply_message
from .message import MessageListView, MessageDetailView, send_message
from .profile import (
    ProfileView, PublicProfileView, ProfileSettingsView, ProfileEditView,
    ProfilePreviewView, WorkHistoryView, TagSelectorView, CertificationView,
)
from .activity import (
    ActivityListView, ActivityDetailView, PublishActivityView,
    enroll_activity, cancel_enrollment,
)
from .community import CommunityView, CommunityDetailView, join_community
from .ai import AIAssistantView, AIChatProxyView, AITagsPopupView
from .network import NetworkGraphView, AlumniFilterView
from .followup import FollowupView
from .search import SearchView

# ─── test ───
from .auth import test_page
