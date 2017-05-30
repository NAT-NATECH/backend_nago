# -*- coding: utf-8 -*-
# Django
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from braces.views import LoginRequiredMixin,StaffuserRequiredMixin
from django.views.generic import TemplateView, View
#Project
from server.models import Person
from backoffice.forms import UserForm,PersonForm,UserModifyForm

class Home(LoginRequiredMixin, StaffuserRequiredMixin, TemplateView):
    """
    Home
    """
    template_name = 'backoffice/home.html'

################################################################
class PersonList(LoginRequiredMixin,StaffuserRequiredMixin,TemplateView):
    template_name = 'backoffice/person/list.html'

    def get_context_data(self, **kwargs):
        context = super(PersonList, self).get_context_data(**kwargs)
        context['persons'] = Person.objects.all()
        return context

class PersonCreateModify(LoginRequiredMixin,StaffuserRequiredMixin,TemplateView):
    template_name = 'backoffice/person/create-modify.html'

    def get_context_data(self, **kwargs):
        context = super(PersonCreateModify, self).get_context_data(**kwargs)
        if 'pk' in kwargs:
            person = get_object_or_404(Person, pk=int(kwargs['pk']))
            personForm = PersonForm(instance=person)
            userForm = UserModifyForm(instance=person.fk_user)
            context['Title'] = "Modificar usuario"
        else:
            personForm = PersonForm()
            userForm = UserForm()
            context['Title'] = "Crear Usuario"

        context['PersonForm'] = personForm 
        context['UserForm'] = userForm 
        return context

    def post(self, request, *args, **kwargs):
        post_values = request.POST.copy()

        if 'pk' in kwargs:
            person = get_object_or_404(Person, pk=int(kwargs['pk']))
            personForm = PersonForm(request.POST,instance=person)
            userForm = UserModifyForm(request.POST,instance=person.fk_user)
            title = "Modificar usuario"
        else:
            personForm = PersonForm(request.POST)
            userForm = UserForm(request.POST)
            title = "Crear Usuario"

        if personForm.is_valid() and userForm.is_valid():
            user = userForm.save(commit=False)
            user.is_active = True
            user.save()
            person = personForm.save(commit=False)
            person.fk_user = user
            person.save()

            #¿ enviar correo de registro ?
            messages.add_message(request, messages.SUCCESS, 'Usuario registrado exitosamente')
            return redirect('PersonList')

        messages.add_message(request, messages.ERROR, 'Error: no se realizo la operación')
        return render(request, self.template_name, {'PersonForm':personForm,'UserForm':userForm,'Title':title})

class PersonDeleteAjax(LoginRequiredMixin,StaffuserRequiredMixin,View):
    """
    Delete requested Prod
    """

    def post(self, request, *args, **kwargs):
        post_values = request.POST.copy()
        try:
            person = Person.objects.get(pk = request.POST['pk'])
            user = person.fk_user
            person.delete()
            user.delete()
            messages.add_message(request, messages.SUCCESS, 'Se elimino correctamente')
            data={'deleted' : 1}
        except:
            messages.add_message(request, messages.ERROR, 'Error: no se realizo la operación')
            data={'deleted' : 0}
        
        return HttpResponse(json.dumps(data), content_type='application/json')