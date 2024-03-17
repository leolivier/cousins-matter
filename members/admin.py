from django.contrib import admin

from .models import Member, Family, Address

admin.site.register(Member)
admin.site.register(Family)
admin.site.register(Address)
