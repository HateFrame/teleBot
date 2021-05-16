from django.contrib import admin

from .forms import ProfileForm
from .models import Profile
from .models import Message
from .models import CharacterData


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name', 'statement')
    form = ProfileForm


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'text', 'created_at')

    #def get_queryset(self, request):
    #    return


@admin.register(CharacterData)
class CharacterDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'first_name', 'last_name', 'phone_number', 'email')

# Register your models here.
