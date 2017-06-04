# -*- coding: utf-8 -*-
from datetime import date
from django import forms
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
                'data-date-format':'yyyy-mm-dd',
                'style':'max-width:120px;'
            })

#############################################################

class LoanShowForm(forms.ModelForm):      

    class Meta:
        model = Loan
        exclude = []


class LoanRequestShowForm(forms.ModelForm):      

    class Meta:
        model = LoanRequest
        exclude = []


class NotificationShowForm(forms.ModelForm):      

    class Meta:
        model = Notification
        exclude = []