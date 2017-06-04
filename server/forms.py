# -*- coding: utf-8 -*-
from django import forms
from server.models import Profile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserForm(UserCreationForm):
    """
    Ceate or modify a User
    """
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico'
        }

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        for key in self.fields:
            self.fields[key].widget.attrs.update({
                'class': 'form-control'
            })

class UserModifyForm(forms.ModelForm):
    """
    Modify a User
    """
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', )
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico'
        }

    def __init__(self, *args, **kwargs):
        super(UserModifyForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].widget.attrs.update({
                'class': 'form-control'
            })


class ProfileForm(forms.ModelForm):
    """
    Ceate or modify a Profile 
    """

    class Meta:
        model = Profile
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].widget.attrs.update({
                'class': 'form-control'
            })
        self.fields['image'].widget.attrs.update({'class': ''})
