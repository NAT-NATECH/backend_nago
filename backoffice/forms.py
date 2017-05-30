# -*- coding: utf-8 -*-
from datetime import date
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


class ReportDatesForm(forms.Form):
    """
    Date from - Date to
    """

    date_from = forms.DateField(initial=date.today)
    date_to = forms.DateField(initial=date.today)

    def clean(self):
        cleaned_data = super(ReportDatesForm, self).clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            msg = 'Error en la fecha.'
            self.add_error('date_from', msg)

    def __init__(self, *args, **kwargs):
        super(ReportDatesForm, self).__init__(*args, **kwargs)
        self.fields['date_from'].label = "Desde"
        self.fields['date_to'].label = "Hasta"
        for key in self.fields:
            self.fields[key].widget.attrs.update({
                'class': 'datepicker form-control',
                'data-date-format':'yyyy-mm-dd'
            })