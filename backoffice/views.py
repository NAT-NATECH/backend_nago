# -*- coding: utf-8 -*-
# Django
import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from braces.views import LoginRequiredMixin,StaffuserRequiredMixin,SuperuserRequiredMixin
from django.views.generic import TemplateView, View
#Project
from server.forms import UserForm,UserModifyForm,ProfileForm
from server.models import User,LoanRequest,Loan,Notification,Friendship,Notification
from backoffice.forms import *

class Home(LoginRequiredMixin, StaffuserRequiredMixin, TemplateView):
    """
    Home
    """
    template_name = 'backoffice/home.html'

################################################################
class UserList(LoginRequiredMixin,StaffuserRequiredMixin,TemplateView):
    template_name = 'backoffice/user/list.html'

    def get_context_data(self, **kwargs):
        context = super(UserList, self).get_context_data(**kwargs)
        context['users'] = User.objects.all()
        context['Title'] = "Usuarios"
        return context

class UserFriendsList(LoginRequiredMixin,SuperuserRequiredMixin,TemplateView):
    template_name = 'backoffice/user/friends.html'

    def get_context_data(self, **kwargs):
        context = super(UserFriendsList, self).get_context_data(**kwargs)
        user = get_object_or_404(User, pk=int(kwargs['pk']))
        context['friends'] = user.profile.get_friends_list()
        context['Title'] = "Amistades"
        return context

class UserCreateModify(LoginRequiredMixin,SuperuserRequiredMixin,TemplateView):
    '''
    Create and modify User
    4 forms are used:
        UserForm : Create User model
        ProfileForm : Create and modify Profile user model
        UserModifyForm : Modify User model
        UserTypeForm : set is_superuser and is_staff to User model 
    '''
    template_name = 'backoffice/user/create-modify.html'

    def get_context_data(self, **kwargs):
        context = super(UserCreateModify, self).get_context_data(**kwargs)
        #MODIFY
        if 'pk' in kwargs: 
            user = get_object_or_404(User, pk=int(kwargs['pk']))
            profileForm = ProfileForm(instance=user.profile)
            userForm = UserModifyForm(instance=user)
            userTypeForm = UserTypeForm(instance=user)
            context['Title'] = "Modificar usuario"
        #CREATE
        else: 
            profileForm = ProfileForm()
            userForm = UserForm()
            userTypeForm = UserTypeForm()
            context['Title'] = "Crear Usuario"

        context['ProfileForm'] = profileForm 
        context['UserForm'] = userForm 
        context['UserTypeForm'] = userTypeForm
        return context

    def post(self, request, *args, **kwargs):
        #MODIFY
        if 'pk' in kwargs:
            user = get_object_or_404(User, pk=int(kwargs['pk']))
            userForm = UserModifyForm(request.POST,instance=user)
            title = "Modificar usuario"
        #CREATE
        else:
            userForm = UserForm(request.POST)
            title = "Crear Usuario"

        userTypeForm = UserTypeForm(request.POST)
        profileForm = ProfileForm(request.POST,request.FILES)

        if profileForm.is_valid() and userForm.is_valid():
            user = userForm.save(commit=False)

            #check if user is superuser or staff
            is_staff = request.POST.get("is_staff", None)
            is_superuser = request.POST.get("is_superuser", None)
            user.is_superuser = True if is_superuser else False
            user.is_staff = True if is_superuser or is_staff else False

            user.save()
            ProfileForm(request.POST,request.FILES,instance=user.profile).save()

            #¿ enviar correo de registro ?
            messages.add_message(request, messages.SUCCESS, 'Usuario registrado exitosamente')
            return redirect('UserList')

        messages.add_message(request, messages.ERROR, 'Error: no se realizo la operación')
        return render(request, self.template_name, {'ProfileForm':profileForm,
                                                    'UserForm':userForm,
                                                    'UserTypeForm':userTypeForm,
                                                    'Title':title})

class UserDeleteAjax(LoginRequiredMixin,SuperuserRequiredMixin,View):
    """
    Delete requested Prod
    """

    def post(self, request, *args, **kwargs):
        post_values = request.POST.copy()
        try:
            user = User.objects.get(pk = request.POST['pk'])
            user.delete()
            messages.add_message(request, messages.SUCCESS, 'Se elimino correctamente')
            data={'deleted' : 1}
        except:
            messages.add_message(request, messages.ERROR, 'Error: no se realizo la operación')
            data={'deleted' : 0}
        
        return HttpResponse(json.dumps(data), content_type='application/json')


##########################################################################

class LoansList(LoginRequiredMixin,StaffuserRequiredMixin,TemplateView):
    """
    List all Loans
    """

    template_name = 'backoffice/transaction/loans-list.html'
    title = 'Lista de prestamos'

    def get_context_data(self, **kwargs):
        context = super(LoansList, self).get_context_data(**kwargs)
        context['objects'] = Loan.objects.all()
        context['Title'] = self.title
        return context

class LoansShow(LoginRequiredMixin,StaffuserRequiredMixin,TemplateView):
    """
    Display a Loan
    """

    template_name = 'backoffice/transaction/display.html'
    title = 'Prestamo'

    def get_context_data(self, **kwargs):
        context = super(LoansShow, self).get_context_data(**kwargs)
        obj = get_object_or_404(Loan, pk=int(kwargs['pk']))
        context['object'] = LoanShowForm(instance=obj)
        context['Title'] = self.title
        return context

#############################################################################

class LoansRequestList(LoginRequiredMixin,StaffuserRequiredMixin,TemplateView):
    """
    List all LoansRequest
    """

    template_name = 'backoffice/transaction/loans-request-list.html'
    title = 'Lista de solicitudes'

    def get_context_data(self, **kwargs):
        context = super(LoansRequestList, self).get_context_data(**kwargs)
        context['objects'] = LoanRequest.objects.all()
        context['Title'] = self.title
        context['dateRangeForm'] = DateRangeForm() 
        context['dateTypeForm'] = DateTypeForm()
        return context

    def post(self, request, *args, **kwargs):
        post_values = request.POST.copy()

        dateRangeForm = DateRangeForm(post_values) 
        dateTypeForm = DateTypeForm(post_values)
        context = {'Title':self.title,'dateRangeForm':dateRangeForm,'dateTypeForm':dateTypeForm}

        if dateRangeForm.is_valid() and dateTypeForm.is_valid():
            date_from = datetime.strptime(post_values['date_from'], '%d/%m/%Y').strftime('%Y-%m-%d')
            date_to = datetime.strptime(post_values['date_to'], '%d/%m/%Y').strftime('%Y-%m-%d')
            date_range = (date_from,date_to)
            date_type = int(post_values['date_type'])
            if date_type == 1: #(1, "F. Creación")
                context['objects'] = LoanRequest.objects.filter(date_create__range=date_range)
            if date_type == 2: #(2, "F. Expiración")
                context['objects'] = LoanRequest.objects.filter(date_expiration__range=date_range)
            if date_type == 3: #(3, "F. Limite")
                context['objects'] = LoanRequest.objects.filter(deadline__range=date_range)
        else:
            messages.add_message(request, messages.ERROR, 'Error: no se realizo la operación')

        return render(request, self.template_name,context)


class LoansRequestShow(LoginRequiredMixin,StaffuserRequiredMixin,TemplateView):
    """
    Display a Loan Request
    """

    template_name = 'backoffice/transaction/display.html'
    title = 'Solicitud'

    def get_context_data(self, **kwargs):
        context = super(LoansRequestShow, self).get_context_data(**kwargs)
        obj = get_object_or_404(LoanRequest, id=int(kwargs['pk']))
        context['object'] = LoanRequestShowForm(instance=obj)
        context['users'] = [obj.friendship.friend1,obj.friendship.friend2] 
        context['friendship'] = obj.friendship
        context['Title'] = self.title
        return context

#############################################################################

class NotificationList(LoginRequiredMixin,StaffuserRequiredMixin,TemplateView):
    """
    List all Notification
    """

    template_name = 'backoffice/transaction/notifications-list.html'
    title = 'Lista de notificaciones'

    def get_context_data(self, **kwargs):
        context = super(NotificationList, self).get_context_data(**kwargs)
        context['objects'] = Notification.objects.all()
        context['Title'] = self.title
        context['dateRangeForm'] = DateRangeForm() 
        return context

    def post(self, request, *args, **kwargs):
        post_values = request.POST.copy()
        dateRangeForm = DateRangeForm(post_values) 
        context = {'Title':self.title,'dateRangeForm':dateRangeForm}

        if dateRangeForm.is_valid():
            date_from = datetime.strptime(post_values['date_from'], '%d/%m/%Y').strftime('%Y-%m-%d')
            date_to = datetime.strptime(post_values['date_to'], '%d/%m/%Y').strftime('%Y-%m-%d')
            context['objects'] = Notification.objects.filter(
                                    date__range=(date_from,date_to))
        else:
            messages.add_message(request, messages.ERROR, 'Error: no se realizo la operación')

        return render(request, self.template_name,context)

class NotificationShow(LoginRequiredMixin,StaffuserRequiredMixin,TemplateView):
    """
    Display a Notification
    """

    template_name = 'backoffice/transaction/display.html'
    title = 'Notificación'

    def get_context_data(self, **kwargs):
        context = super(NotificationShow, self).get_context_data(**kwargs)
        obj = get_object_or_404(Notification, pk=int(kwargs['pk']))
        context['object'] = NotificationShowForm(instance=obj)
        if obj.friendship:
            context['friendship'] = obj.friendship
            context['users'] = [obj.friendship.friend1,obj.friendship.friend2] 
        else:
            context['users'] = [obj.user] 
        context['Title'] = self.title
        return context