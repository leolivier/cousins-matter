from allauth.socialaccount.models import SocialLogin, SocialAccount
from allauth.socialaccount.adapter import get_adapter
from django.contrib.messages.storage.fallback import FallbackStorage
from members.models import Member
from members.tests.tests_member_base import MemberTestCase, get_fake_request
from members.registration_link_manager import RegistrationLinkManager


class OAuthActivationTests(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.adapter = get_adapter()
    self.inactive_member = self.create_member(is_active=False)
    self.token_manager = RegistrationLinkManager()
    # The provider is already configured via settings.SOCIALACCOUNT_PROVIDERS

  def test_pre_social_login_activation_success(self):
    """Test that an inactive member is activated if session has valid token."""
    token = self.token_manager.make_token(self.inactive_member.email)

    # Setup session
    session = self.client.session
    session["invitation_token"] = token
    session["invitation_email"] = self.inactive_member.email
    session.save()

    # Mock social login
    user = Member(email=self.inactive_member.email)
    sociallogin = SocialLogin(user=user, account=SocialAccount(user=user, provider="google"))

    # Setup request with session and messages
    request = get_fake_request()
    request.session = session
    setattr(request, "_messages", FallbackStorage(request))

    # Run adapter method
    self.adapter.pre_social_login(request, sociallogin)

    # Verify member is now active
    self.inactive_member.refresh_from_db()
    self.assertTrue(self.inactive_member.is_active)
    self.assertIsNone(self.inactive_member.member_manager)

  def test_pre_social_login_no_invitation_rejection(self):
    """Test that social login is rejected if no invitation in session."""
    user = Member(email="uninvited@example.com")
    sociallogin = SocialLogin(user=user, account=SocialAccount(user=user, provider="google"))

    request = get_fake_request()
    request.session = self.client.session  # empty session
    setattr(request, "_messages", FallbackStorage(request))

    from allauth.core.exceptions import ImmediateHttpResponse

    with self.assertRaises(ImmediateHttpResponse):
      self.adapter.pre_social_login(request, sociallogin)

  def test_pre_social_login_already_active(self):
    """Test that an already active member can log in normally."""
    user = Member(email=self.member.email)
    sociallogin = SocialLogin(user=user, account=SocialAccount(user=user, provider="google"))

    request = get_fake_request()
    request.session = self.client.session
    setattr(request, "_messages", FallbackStorage(request))

    # Should return normally (no exception, no change)
    self.adapter.pre_social_login(request, sociallogin)
    self.assertTrue(self.member.is_active)

  def test_pre_social_login_new_member_with_invitation(self):
    """Test that a non-existent member with a valid invitation is allowed but currently fails."""
    email = "new_invited@example.com"
    token = self.token_manager.make_token(email)

    # Setup session
    session = self.client.session
    session["invitation_token"] = token
    session["invitation_email"] = email
    session.save()

    # Mock social login for a user that doesn't exist in DB
    user = Member(email=email)
    sociallogin = SocialLogin(user=user, account=SocialAccount(user=user, provider="google"))

    # Setup request
    request = get_fake_request()
    request.session = session
    setattr(request, "_messages", FallbackStorage(request))

    # This should NOT raise ImmediateHttpResponse
    self.adapter.pre_social_login(request, sociallogin)

    # Verify sociallogin.user is now set to active (unsaved yet)
    self.assertTrue(sociallogin.user.is_active)
