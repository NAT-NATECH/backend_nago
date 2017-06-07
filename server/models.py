# -*- coding: utf-8 -*-
from django.core.validators import MaxValueValidator,MinValueValidator
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User._meta.get_field('email')._unique = True
User._meta.get_field('email')._blank = False

class Friendship(models.Model):
    FRIENDS = 1
    CANCELED = 2
    PROCESS = 3

    TYPE_CHOICES = (
        (FRIENDS, 'Amigos'),
        (CANCELED, 'Cancelada'),
        (PROCESS, 'En proceso')
    )
    state = models.PositiveIntegerField("Estado",choices=TYPE_CHOICES,default=PROCESS,
                                        validators=[MaxValueValidator(3)])
    friend1 = models.ForeignKey(User, related_name='friend1',verbose_name='ID de Usuario 1')
    friend2 = models.ForeignKey(User, related_name='friend2',verbose_name='ID de Usuario 2')

    def clean(self):
        direct = FriendShip.objects.filter(friend1=self.friend1, friend2=self.friend2)
        reverse = FriendShip.objects.filter(friend1=self.friend2, friend2=self.friend1) 

        if direct.exists() or reverse.exists():
            raise ValidationError({'key':'Esta relación la existe.'})

    def __str__(self):
        return self.friend1.get_full_name() + " y " + self.friend2.get_full_name()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,verbose_name='ID de Usuario')
    num_visit = models.PositiveIntegerField("Número de visita",default=0)
    code = models.CharField("Código",max_length=10,null=True, blank=True)
    pin = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField("Descripción",max_length=100,null=True ,blank=True)
    birthdate = models.DateField("Fecha de nacimiento", null=True, blank=True)
    phone = models.CharField("Teléfono",max_length=30, null=True, blank=True)
    image = models.ImageField("Imagen de perfil",upload_to="profile/", null=True, blank=True)
    
    def get_friendships(self):
        direct = Friendship.objects.filter(friend1=self.user)
        reverse = Friendship.objects.filter(friend2=self.user) 
        return direct | reverse

    def get_friends_list(self):
        direct = Friendship.objects.filter(friend1=self.user)        
        reverse = Friendship.objects.filter(friend2=self.user) 
        return [f.friend1 for f in reverse] + [f.friend2 for f in direct] 

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,verbose_name='ID de Usuario')
    amount_available = models.DecimalField("Monto disponible",
                                            decimal_places=2,max_digits=12,
                                            default=0.0) 
    amount_locked = models.DecimalField("Monto bloqueado",
                                        validators=[MinValueValidator(0.0)],
                                        decimal_places=2,max_digits=12,
                                        default=0.0)
    amount_invested = models.DecimalField("Monto invertido",
                                            validators=[MinValueValidator(0.0)],
                                            decimal_places=2,max_digits=12,
                                            default=0.0)
    customer_dwolla = models.TextField(max_length=150,null=True, blank=True)

@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Account.objects.create(user=instance)
    instance.profile.save()
    instance.account.save()

class LoanRequest(models.Model):
    user = models.ForeignKey(User,verbose_name='ID de Usuario')
    friendship = models.ForeignKey(Friendship,verbose_name='ID de Amistad')
    state = models.BooleanField("Estado",default=False)
    amount_available = models.DecimalField("Monto disponible",decimal_places=2,max_digits=12)
    amount_request = models.DecimalField("Monto sugerido",
                                            validators=[MinValueValidator(0.0)],
                                            decimal_places=2,max_digits=12)
    interest = models.DecimalField("Interes",decimal_places=2,max_digits=12)
    commentary = models.CharField("Comentario",max_length=150)
    date_return = models.PositiveIntegerField("Días de devolución")
    date_expiration = models.DateField("Fecha de Expiración")
    deadline = models.DateField("Fecha límite")
    date_create = models.DateField("Fecha de creación",auto_now_add=True)

    def get_lender(self):
        direct = Friendship.objects.filter(friend1=self.user)
        reverse = Friendship.objects.filter(friend2=self.user) 
        return direct[0].friend2 if direct else reverse[0].friend1

class Loan(models.Model):
    loan_request = models.ForeignKey(LoanRequest,verbose_name='ID de Solicitud')
    state = models.BooleanField("Estado",default=False)
    amount_loan = models.DecimalField("Monto del prestamos",
                                        validators=[MinValueValidator(0.0)],
                                        decimal_places=2,max_digits=12)
    amount_interest = models.DecimalField("Monto del interes",
                                            validators=[MinValueValidator(0.0)],
                                            decimal_places=2,max_digits=12)

class Notification(models.Model):
    FRIENDS = "F"
    REQUEST_LOANS = "RL"
    LOANS = "L"

    TYPE_CHOICES = (
        (FRIENDS, 'Amistad'),
        (REQUEST_LOANS, 'Solicitud de prestamo'),
        (LOANS, 'Prestamo')
    )

    user = models.ForeignKey(User,verbose_name='ID de Usuario')
    message = models.TextField("Mensaje",max_length=150)
    date = models.DateField("Fecha",auto_now_add=True)
    read = models.BooleanField("Leído",default=True)
    about = models.CharField("Tipo",max_length=2,choices=TYPE_CHOICES)
    friendship = models.ForeignKey(Friendship, null=True, blank=True,verbose_name='ID de Amistad')
    loans = models.ForeignKey(Loan, null=True, blank=True,verbose_name='ID de Prestamo')
    request_loans = models.ForeignKey(LoanRequest, null=True, blank=True,verbose_name='ID de Solicitud')

    class Meta:
        ordering = ['date']