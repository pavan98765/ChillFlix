from django.forms import ModelForm
from .models import Profile, CustomUser


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        exclude = ["uuid"]
