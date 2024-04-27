
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  
from django.core.mail import send_mail
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from ..registration_link_manager import RegistrationLinkManager
from ..forms import MemberInvitationForm, RegistrationRequestForm
from .utils import redirect_to_referer
from .views_member import RegisterMemberView
from ..models import Member

from cousinsmatter import settings

class RegistrationCheckingView(generic.View):

	def get(self, request, encoded_email, token):
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

			return RegisterMemberView(request)
		
		else:
			# we don't know what happened, should have raised before
			return HttpResponseBadRequest(_("Invalid link. Please contact the administrator."))

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
