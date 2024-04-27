
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  
from django.core.mail import send_mail
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from ..registration_link_manager import RegistrationLinkManager
from accounts.forms import AccountRegisterForm
from ..forms import MemberInvitationForm, RegistrationRequestForm, MemberUpdateForm, \
										AddressUpdateForm, FamilyUpdateForm
from cousinsmatter.utils import redirect_to_referer
from .views_member import MEMBER_MODE
from ..models import Member
from verify_email.email_handler import send_verification_email
from cousinsmatter import settings

class RegistrationCheckingView(generic.CreateView):
	mode = MEMBER_MODE.signup
	template_name = "members/member_upsert.html"

	def check_before_register(self, request, encoded_email, token):
		if RegistrationLinkManager().decrypt_link(encoded_email, token):
			# check if user is already logged in
			if request.user.is_authenticated:
				messages.error(request, _("You are already logged in"))
				return redirect_to_referer(request)
			# check if member is already registered
			account = User.objects.filter(email=request.POST.get("email"))
			if account.exists():
				account = account.first()
				# if member is already registered but account not active, ask him to contact his/her managing account
				if account.is_active:
					messages.error(request, _("A member with the same account name or email address is already registered. Please sign in instead"))
					return redirect_to_referer(request)
				else:
					manager = Member.objects.get(account__id=account.id).managing_account
					messages.error(request, _("You are already registered but not active. Please contact %s to activate your account") % manager.member.get_full_name())
					return redirect_to_referer(request)
			else:
					account = User.objects.filter(email=request.POST.get("username"))
			# TODO: how to control self registration by an admin?
			return None
		else:
			return HttpResponseBadRequest(_("Invalid link. Please contact the administrator."))

	def get(self, request, encoded_email, token):
		checked_ko = self.check_before_register(request, encoded_email, token)
		if checked_ko:
			return checked_ko
		else:
			return render(request, self.template_name, {
					"m_form": MemberUpdateForm(), 
					"u_form": AccountRegisterForm(), 
					"addr_form": AddressUpdateForm(), 
					"family_form": FamilyUpdateForm(),
					"mode": self.mode.name,
			})


	def post(self, request, encoded_email, token):
		checked_ko = self.check_before_register(request, encoded_email, token)
		if checked_ko: return checked_ko

		# start with account
		u_form = AccountRegisterForm(request.POST)

		if u_form.is_valid():
			account = send_verification_email(request, u_form)
			# if new member, it has been created by the account creation
			# retrieve it and recreate the member form with this instance
			member = Member.objects.get(account=account)
			m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
			if m_form.is_valid():
				member = m_form.save()

				username = u_form.cleaned_data.get('username')
				messages.success(request, _('Hello %(username)s, your account has been created! You will now receive an email to verify your email address. Click in the link inside the mail to finish the registration.') % {"username": username})
				return redirect("accounts:login")

		return redirect_to_referer(request)

class MemberInvitationView(LoginRequiredMixin, generic.View):

	def post(self, request):
		"""
		Sends an email with a registration link to the user's email address.
		The self registration can be done only after receiving
		an invitation link from the admin. This link is sent to the user by email and contains a token.
		The user can then use the link to open the registration form and register.
		"""
		if not request.user.is_staff:
			raise PermissionError(_("Only staff users can send invitations."))
		
		form = MemberInvitationForm(request.POST)
		if not form.is_valid():
			messages.error(request, form.errors)
			return redirect_to_referer(request)
		
		email = form.cleaned_data['email']
		invited = form.cleaned_data['invited']

		if User.objects.filter(email=email).exists():
			messages.error(request, _('User with this email already exists.'))
			return redirect_to_referer(request)
		
		invitation_url = RegistrationLinkManager().generate_link(request, email)
		site_name = settings.SITE_NAME
		admin = request.user.get_full_name()
		from_email = request.user.email

		msg = render_to_string(
			"members/registration_invite_email.html",
			{"link": invitation_url, "admin": admin, "site_name": site_name, "invited": invited}, 
			request=request
		)

		send_mail(
			_(f"You are invited to register on {site_name}"), strip_tags(msg),
			from_email=from_email,
			recipient_list=[email], html_message=msg
		)
		messages.success(request, _("Invitation sent to {email}.").format(email=email))
		return redirect_to_referer(request)

	def get(self, request):
		email = request.GET.get('mail')
		if email:
			form = MemberInvitationForm(initial={'email': email})
		else:
			form = MemberInvitationForm()
		return render(request, "members/registration_invite.html", {'form': form})

class RegistrationRequestView(LoginRequiredMixin, generic.View):

	def post(self, request):
		"""
		Allows a user to request a registration link.	
		"""
		form = RegistrationRequestForm(request.POST)
		# Validate the form: the captcha field will automatically
		# check the input
		if form.is_valid(): # human = True

			site_name = settings.SITE_NAME
			requester_email = request.POST.get("email")
			if User.objects.filter(email=requester_email).exists():
				messages.error(request, _('User with this email already exists.'))
				return redirect_to_referer(request)

			requester_name = request.POST.get("name")
			requester_message = request.POST.get("message")
			link = reverse("members:invite")
			absolute_link = request.build_absolute_uri(link)

			context = {
				"site_name": site_name,
				"requester" : {
					"email": requester_email,
					"name": requester_name,
					"message": requester_message
				},
				"link": absolute_link
			}

			msg = render_to_string("members/registration_request_email.html", context, request=request)
			admin = User.objects.filter(is_superuser=True).first()
			send_mail(
				_(f"Registration request for {site_name}"), strip_tags(msg),
				from_email=settings.DEFAULT_FROM_EMAIL,
				recipient_list=[admin.email], html_message=msg
			)
			messages.success(request, _("Registration request sent."))
			return redirect_to_referer(request)

	def get(self, request):
		form = RegistrationRequestForm()
		return render(request, 'members/registration_request.html', {'form': form})
