# -*- coding: utf-8 -*-
from datetime import date
from django import forms
from django.contrib.auth.models import User
#Project
from server.models import Loan, LoanRequest, Notification

#############################################################

class DateTypeForm(forms.Form):
    """
    Date Type
    """

    TYPE_CHOICES = (
        (1, "F. Creación"),
        (2, "F. Expiración"),
        (3, "F. Limite")
    )            

    date_type = forms.ChoiceField(choices=TYPE_CHOICES, required=True, label="Filtrar por")

    def __init__(self, *args, **kwargs):
        super(DateTypeForm, self).__init__(*args, **kwargs)
        self.fields['date_type'].widget.attrs['class'] = 'form-control'

class DateRangeForm(forms.Form):
    """
    Date from - Date to
    """          

    date_from = forms.DateField()
    date_to = forms.DateField()

    def clean(self):
        cleaned_data = super(DateRangeForm, self).clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            msg = 'Error en la fecha.'
            self.add_error('date_from', msg)

    def __init__(self, *args, **kwargs):
        super(DateRangeForm, self).__init__(*args, **kwargs)
        self.fields['date_from'].label = "desde"
        self.fields['date_to'].label = "hasta"
        for key in self.fields:
            self.fields[key].widget.attrs.update({
                'class': 'datepicker form-control',
                'data-date-format':'dd/mm/yyyy',
                'style':'max-width:120px;'
            })
            self.fields[key].input_formats = ['%d/%m/%Y']

class UserTypeForm(forms.ModelForm):
    """
    Form to choice if user is superuser or staff
    """          

    class Meta:
        model = User
        fields = ('is_superuser', 'is_staff', )
        labels = {
            'is_superuser':'¿Es superusuario?', 
            'is_staff':'¿Es staff?'
        }
        help_texts = {
            'is_superuser':'Usuario con todos los permisos en el admin.', 
            'is_staff':'Usuario con permisos restringidos en el admin.'
        }


#############################################################
#### DISPLAY FORMS ####

class LoanShowForm(forms.ModelForm):      

    class Meta:
        model = Loan
        exclude = ['friendship','loan_request']


class LoanRequestShowForm(forms.ModelForm):      

    class Meta:
        model = LoanRequest
        exclude = ['user']
