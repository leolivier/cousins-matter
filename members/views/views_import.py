import logging, csv, random, time, os, math, io, string
from django.core.files import File
from django.forms import ValidationError
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from ..models import Member, Family
from ..forms import CSVImportMembersForm
from cousinsmatter.utils import redirect_to_referer
from django.conf import settings

from ..models import ALL_FIELD_NAMES, MANDATORY_FIELD_NAMES, ACCOUNT_FIELD_NAMES, MEMBER_FIELD_NAMES

logger = logging.getLogger(__name__)

def generate_random_string(length):
    return ''.join(random.choice(string.printable) for _ in range(length))

def t(field): return ALL_FIELD_NAMES[field]

def check_fields(fieldnames):
	for fieldname in fieldnames:
		if fieldname not in ALL_FIELD_NAMES.values():
			raise ValidationError(_(f'Unknwon column in CSV file: "{fieldname}". Valid fields are {ALL_FIELD_NAMES.values()}'))
	for fieldname in MANDATORY_FIELD_NAMES.values():
		if fieldname not in fieldnames:
			raise ValidationError(_(f'Missing column in CSV file: "{fieldname}". Mandatory fields are {MANDATORY_FIELD_NAMES.values()}'))

	return True

class CSVImportView(LoginRequiredMixin, generic.FormView):
	template_name = "members/import_members.html"
	form_class = CSVImportMembersForm
	success_url = "/members"
	
	def get_context_data(self):
		optional_fields = { str(s) for s in ALL_FIELD_NAMES.values() } - { str(s) for s in MANDATORY_FIELD_NAMES.values() }
		return super().get_context_data() | { 
			'mandatory_fields': MANDATORY_FIELD_NAMES.values(),
			'optional_fields': optional_fields,
			'media_root': settings.MEDIA_ROOT,
			}
	
	def _import_csv(self, csv_file):
			nbMembers = 0
			nbLines = 0
			errors = []
			csvf = io.TextIOWrapper(csv_file, encoding="utf-8", newline="")
		# with csv_file.open() as csvf:
			reader = csv.DictReader(csvf)
			check_fields(reader.fieldnames) 
			random.seed()
			for row in reader:
				# search for an existing account with this username
				account_exists = False
				account = User.objects.filter(username=row[t('username')])
				if account.exists(): # found, use it
					account = account.first()
					account_exists = True

					# update account if needed
					changed = False
					# for all account fields but username
					# if new value for this field, then override existing one
					for field in ACCOUNT_FIELD_NAMES:
						if field == 'username': continue
						trfield = t(field)
						if row[trfield] and account.__dict__[field] != row[trfield]: # TODO: What other checks?
							setattr(account, field, row[trfield]) # Needs some conversion?
							changed = True
					if changed:
						account.save()

				else: # not found, create it
					pwd = generate_random_string(16)
					account = User.objects.create_user(row[t('username')], row[t('email')], pwd,
																			first_name=row[t('first_name')], last_name=row[t('last_name')])
			
				if account_exists: # then member also exists
					member = Member.objects.get(account=account)
				
				else: # member will be created by user creation by using signals 
							# so we have to wait for it to be created.
					while True:
						time.sleep(0.1)
						member = Member.objects.filter(account=account)
						if member.exists():
							member = member.first()
							break

				# update member
				changed = False
				for field in MEMBER_FIELD_NAMES:
					trfield = t(field)
					if trfield in row and row[trfield] and member.__dict__[field] != row[trfield]:  # TODO: What other checks?
						if field == 'family':
							family = Family.objects.get_or_create(name=row[trfield], parent=None)
							member.family = family
						elif field == 'avatar':
							# avatar image must already exist
							avatar = os.path.join(settings.MEDIA_ROOT, 'avatars', row[trfield])
							if not os.path.exists(avatar):
								errors.append(_(f"Avatar not found: {avatar} for username {row[t('username')]}. Ignored..."))
							else:
								with open(avatar, 'rb') as image_file:
									image = File(image_file)
									member.avatar.save(avatar, image)
						# elif field == 'birthdate':
						# 	bdate = time.strptime(row[trfield], "%Y-%d-%m")
						else:
							setattr(member, field, row[trfield]) # Needs some conversion?

						changed = True
				
				nbLines += 1
				
				if changed:
					member.save()
					nbMembers += 1
			
			return (nbLines, nbMembers, errors)

	def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
		form = CSVImportMembersForm(request.POST, request.FILES)
		if form.is_valid():
			csv_file = request.FILES["csv_file"]
			if csv_file.multiple_chunks():
				size = math.floor(csv_file.size*100/(1024*1024))/100
				messages.error(request,_("Uploaded file is too big ({size} MB)."))
				return redirect_to_referer(request)
		
			try:
				nbLines, nbMembers, errors = self._import_csv(csv_file)
				messages.success(request, _(f"CSV file uploaded: {nbLines} lines read, {nbMembers} members created or updated"))
				for error in errors: 
					messages.errors(request, _(f"Warning: {error}"))
			except ValidationError as ve:
				messages.error(request, ve.message)
				return redirect_to_referer(request)
			except Exception as e:
				messages.error(request, e.__str__())
				raise
		return super().post(request, *args, **kwargs)
