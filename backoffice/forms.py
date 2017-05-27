# -*- coding: utf-8 -*-
from django import forms
from server.models import Person
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
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña',
            'email': 'Correo electrónico'
        }

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
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


class PersonForm(forms.ModelForm):
    """
    Ceate or modify a Person 
    """

    class Meta:
        model = Person
        exclude = ['fk_user','name', 'lastname']

    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].widget.attrs.update({
                'class': 'form-control'
            })
