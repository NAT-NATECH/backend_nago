# -*- coding: utf-8 -*-
# Django
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from braces.views import LoginRequiredMixin,StaffuserRequiredMixin
from django.views.generic import TemplateView, View

class Home(LoginRequiredMixin, StaffuserRequiredMixin, TemplateView):
    """
    Home
    """
    template_name = 'backoffice/index.html'