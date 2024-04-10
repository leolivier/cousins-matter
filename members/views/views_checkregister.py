
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

from ..registration_link_manager import RegistrationLinkManager
from ..forms import MemberInvitationForm, RegistrationRequestForm
from .utils import redirect_to_referer
from .views_member import register_member

from cousinsmatter import settings


def check_register(request, encoded_email, token):
	if RegistrationLinkManager().decrypt_link(encoded_email, token):
		return register_member(request)
	else:
		# we don't know what happened, should have raised before
		return HttpResponseBadRequest(_("Invalid link. Please contact the administrator."))

@login_required
def send_registration_invitation(request):
	"""
	Sends an email with a registration link to the user's email address.
	The self registration can be done only after receiving
	an invitation link from the admin. This link is sent to the user by email and contains a token.
	The user can then use the link to open the registration form and register.
	"""
	if not request.user.is_staff:
		raise PermissionError(_("Only staff users can send invitations."))
	
	if request.method == 'POST':
		email = request.POST.get('email', None)
		if not email:
			messages.error(request, _("Email is required."))
			return redirect_to_referer(request)
		
		if User.objects.filter(email=email).exists():
			messages.error(request, _('User with this email already exists.'))
			return redirect_to_referer(request)
		
		invitation_url = RegistrationLinkManager().generate_link(request, email)
		site_name = settings.SITE_NAME
		admin = request.user.get_full_name()
		from_email = request.user.email

		msg = render_to_string(
			"members/registration_invite_email.html",
			{"link": invitation_url, "admin": admin, "site_name": site_name}, 
			request=request
		)
		send_mail(
			_(f"You are invited to register on {site_name}"), strip_tags(msg),
			from_email=from_email,
			recipient_list=[email], html_message=msg
		)
		messages.success(request, _("Invitation sent to {email}.").format(email=email))
		return redirect_to_referer(request)
	else:
		email = request.GET.get('mail')
		if email:
			form = MemberInvitationForm(initial={'email': email})
		else:
			form = MemberInvitationForm()
		return render(request, "members/registration_invite.html", {'form': form})
	
def register_request(request):
	"""
	Allows a user to request a registration link.	
	"""
	if request.POST:
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
	else:
			form = RegistrationRequestForm()

	return render(request, 'members/registration_request.html', {'form': form})