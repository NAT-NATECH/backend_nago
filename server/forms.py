# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
#Project
from server.models import Profile

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

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        email = cleaned_data.get('email')

        if not email:
            self.add_error(email, "El campo de correo no puede estar vacío.")
            
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        for key in self.fields:
            self.fields[key].help_text = None
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
            self.fields[key].help_text = None
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
        self.fields['birthdate'].widget.attrs.update({
                'class': 'datepicker form-control',
                'data-date-format':'dd/mm/yyyy'
            })
        self.fields['birthdate'].widget.format = '%d/%m/%Y'
        self.fields['birthdate'].input_formats = ['%d/%m/%Y']