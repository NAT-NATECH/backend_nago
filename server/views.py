# -*- coding: utf-8 -*-

from django.http import JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core import serializers
from django.contrib import auth
from . import models
from django.conf import settings
from datetime import datetime, timedelta
from smtplib import SMTP
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q

import base64
import random 
import json
import sys
import os
import dwollav2

NUM_CODE = 4

# Navigate to https://www.dwolla.com/applications (production) or https://dashboard-uat.dwolla.com/applications (Sandbox) for your application key and secret.
#APP_KEY = '6cZg5joGComrIg3orR8bOMDK9H6GhlmCdUIK8p3mtJyRYWq0Hf'
#APP_SECRET = 'gy8kylCejScwP6vUxYOhAc5e6ckW1UdsOWRKobtFCBQRYGEWRB'
#ACCESS_TOKEN = 'huqnYtuILQEXfU7jMPzEQtdb28dKBBffrGB3rKSBeMdwjzoR0k'
APP_KEY = '2AWiAmEyRhW8VV1sCgPpTAaG5AQpyhaLTuSnCRLMMoxjRbnPPm'
APP_SECRET = 'grU6Ne1ScFXiEaBQ8mxD9pNJMLtrQlxngPe6qfhbx0nYcQR2EG'
ACCESS_TOKEN = 'ghMe50QC7JoLwzzvNofKqGHbZBeJwg6LMcHm9PVmDO4XnQMOd7'
SERVER_URL = "http://localhost:8000"
EMAIL_FROM = ""

def method_post(funcion):
	def decorador(*args, **kwargs):
		if args[0].method != "POST":
			return HttpResponse(json.dumps('false'), content_type='application/json')
		else:
			return funcion(*args, **kwargs)

	return decorador

def code_generator(n=5):
	# code = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789_!@#&/'
	code = '0123456789'
	code_final = ''
	for i in list(range(n)):
		code_final += code[random.randint(0, len(code)-1)]

	return code_final

def exist_username(username):
	if len(User.objects.filter(username=username)) > 0: return True
	else: return False

def exist_email(email):
	if len(User.objects.filter(email=email)) > 0: return True
	else: return False

def exist_email_my(email, id):

	if len(User.objects.filter(email=email).exclude(id=id)) > 0: 
		return True
	else: 
		return False

def title_text(text):
	list_text = text.split(' ')
	text_final = ''
	for t in list(range(len(list_text))):
		if t != 0:
			text_final += ' '+list_text[t].title()
		else:
			text_final += list_text[t].title()

	return text_final

def is_friend(id_person, id_friend):
	response = 'false'
	
	if len(models.Friendship.objects.filter(friend1=id_person, friend2=id_friend, state=1)) > 0:
		response = 'true'

	return response

def exist_id_person(id):
	if len(models.Profile.objects.filter(id=id)) > 0: return True
	else: return False

def exclude_friends(id, persons):
	persons_finally = []
	insert = True
	friends = models.Friendship.objects.filter(friend2=id, state=1)
	
	if len(friends) > 0:
		for person in persons:
			for friend in friends:
				if friend.friend2.id == person.id:
					insert = False
					break
			
			if insert:		
				persons_finally.append(person)
			else:
				insert = not insert

		return persons_finally
	else:
		return persons

def validate_args(*args, **kwargs):
	for i in list(args[1:len(args)]):
		if i not in args[0].POST:
			return False
	return True

def validate_request_loan(person_id):
	print "Excede limite:" + str(len(models.LoanRequest.objects.filter(user__id=int(person_id), state=True)) > 0)
	if len(models.LoanRequest.objects.filter(user__id=int(person_id), state=True)) > 0:
		return False

	return True

def have_friends(person_id):
	print "Have Friends:" + str(len(models.Friendship.objects.filter(friend1__id=int(person_id), state=1)) > 0)
	if len(models.Friendship.objects.filter(friend1__id=int(person_id), state=1)) > 0:
		return True
	return False

def filterUser(users):
	result = []
	for user in users:
		result.append(models.Profile.objects.get(user=user))

	print(result)
	return result

def addDate(fday, fdate):
	result = datetime.strptime(fdate.strftime('%Y-%m-%d'), '%Y-%m-%d') + timedelta(days=fday)
	return result

def updateSolicitudes():
	for request_loans in models.LoanRequest.objects.filter(state=True):
		date_expired = request_loans.date_expiration
		date_today = datetime.now().strftime('%Y-%m-%d')
		print('date_expired: '+str(date_expired))
		print('date_today: '+date_today)
		if (str(date_expired) < str(date_today)) or  (request_loans.amount_available >= request_loans.amount_request):
			pass
			#updateLoansProcess(request_loans)

def updateLoansProcess(request_loans):
	print('entro aqui!')
	request_loans.state = False
	request_loans.save()

	person_solicitud = models.Profile.objects.get(id=request_loans.friend.id)

	account_solicitud = models.Account.objects.get(user=person.user_solicitud)
	account_solicitud.amount_available += account_solicitud.amount_locked
	account_solicitud.amount_locked = 0
	account_solicitud.save()

	for friend_loan in models.Friendships_Loans.objects.filter(fk_request_loans=request_loans):
		loan = models.Loans.objects.get(fk_friend_loans=friend_loan)
		loan.state = True
		loan.save()
		amount = loan.amount_loan
		friend = models.Friendship.objects.get(id=friend_loan.fk_friends.id)
		person_invest = models.Profile.objects.get(id=friend.friend.id)
		account_invest = models.Account.objects.get(user=person.user_invest)
		account_invest.amount_invested = 0
		account_invest.save()

# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------

@csrf_exempt
@method_post
def register(request):
	response = False
	account = None
	if validate_args(request, 'name', 'lastname','username', 'email', 'password', 'app') and not exist_username(request.POST['username']): #and (not exist_email(request.POST['email']))
		print "validated"
		try:
			pin = code_generator(NUM_CODE)
			root = User(username=request.POST['username'], first_name=request.POST['name'], last_name=request.POST['lastname'], email=request.POST['email'].lower())
			root.set_password(request.POST['password'])
			root.save()
			person = root.profile
			person.num_visit=0
			person.pin=pin
			person.save()

			if 'img_profile' in request.FILES:
				person.image = request.FILES['img_profile']

			person.save()
			
			client = dwollav2.Client(key = APP_KEY, secret = APP_SECRET, environment = 'sandbox') # optional - defaults to production

			app_token = client.Auth.client()
			customers = app_token.get('customers', {'limit': 10})
			request_body = {
				'firstName': str(request.POST['name']).capitalize(),
				'lastName': str(request.POST['lastname']).capitalize(),
				'email': str(request.POST['email']).capitalize()
			}

			# Using dwollav2 - https://github.com/Dwolla/dwolla-v2-python (Recommended)
			account_token = client.Token(access_token=app_token.access_token, refresh_token=client.Auth.client())
			customer = account_token.post('customers', request_body)
			
			account = root.account
			account.amount_available=float(2000)
			account.amount_locked=float(0)
			account.amount_invested=float(0) 
			account.customer_dwolla = str(customer.headers['location'])
			account.save()

			response = True

			# ------------------
			subject = "Nago Code"
			text_content = '...'
			html_content = '<h2>Code: </h2>'+pin
			to = request.POST['email'].lower()
			# to = request.POST['email'].lower()
			msg = EmailMultiAlternatives(subject, text_content, EMAIL_FROM, [to])
			msg.attach_alternative(html_content, "text/html")
			msg.send()
			# ------------------

		except Exception as e:
			print e
			if not response:
				print e
				if account is not None:
					account.delete()
				person.delete()
				root.delete()
				response = False

				
	return HttpResponse(json.dumps(response), content_type='application/json')

@csrf_exempt
@method_post
def login(request):
	response = {}
	updateSolicitudes()
	if validate_args(request, 'username', 'password', 'app') and (auth.authenticate(username=request.POST['username'], password=request.POST['password']) is not None):
		person = models.Profile.objects.get(user=User.objects.get(username=request.POST['username']))
		account = person.user.account
		response['id'] = person.id
		response['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
		response['username'] = person.user.username
		response['name'] = person.user.first_name
		response['lastname'] = person.user.last_name
		response['telephone'] = person.phone
		if person.birthdate is not None:
			response['birthdate'] = person.birthdate.strftime('%Y/%m/%d')
		else:
			response['birthdate'] = ""
		response['email'] = person.user.email
		if person.description == None:
			response['description'] = ' '
		else:
			response['description'] = person.description
		
		try:
			response['available'] = float(models.Account.objects.get(user__id=int(person.id)).amount_available)
		except:
			response['available'] = 0			
		response['locked'] = float(account.amount_locked)
		if (person.image): response['img_profile'] = SERVER_URL + person.image.url
		else: response['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"
		response['invest'] = float(account.amount_invested)
		response['available'] = float(account.amount_available)
		response['customer_dwolla'] = account.customer_dwolla
		response['num_visit'] = person.num_visit
		
		person.num_visit += 1
		person.save()

	return HttpResponse(json.dumps(response), content_type='application/json')

@csrf_exempt
@method_post
def editProfile(request):
	response = False
	
	if validate_args(request, 'username', 'name', 'lastname','email', 'app') and len(User.objects.filter(username=request.POST['username'])) > 0:# and (not exist_email_my(request.POST['email'], User.objects.get(username=request.POST['username']).id)):
		response = True
		root = User.objects.get(username=request.POST['username'])
		root.email = request.POST['email']
		root.save()
		person = models.Profile.objects.get(user=root)
		person.user.first_name = request.POST['name']
		person.user.last_name = request.POST['lastname']
		
		# person.birthdate = request.POST['birthdate']

		if 'description' in request.POST:
			person.description = request.POST['description']

		if 'telephone' in request.POST:
			person.phone = request.POST['telephone']

		if 'birthdate' in request.POST and len(request.POST['birthdate']) > 4:
			person.birthdate = request.POST['birthdate']

		person.save()

	return HttpResponse(json.dumps(response), content_type='application/json')

@csrf_exempt
@method_post
def existUsername(request):
	response = False

	if validate_args(request, 'username', 'app') and len(User.objects.filter(username=request.POST['username'])) > 0:
		response = True

	return HttpResponse(json.dumps(response), content_type='applicaction/json')

@csrf_exempt
@method_post
def existEmail(request):
	response = False

	if validate_args(request, 'email', 'app') and len(User.objects.filter(email=request.POST['email'])) > 0:
		response = True

	return HttpResponse(json.dumps(response), content_type='applicaction/json')

@csrf_exempt
@method_post
def sendEmailCode(request):
	response = False

	if validate_args(request, 'email') and exist_email(request.POST['email']):
		print "SendEmail"

		subject = 'Nago reset password'
		text_content = '...'
		html_content = '<h2>Code: </h2>' + str(code_generator(5))
		to = request.POST['email'].lower()
		# to = request.POST['email'].lower()
		msg = EmailMultiAlternatives(subject, text_content, EMAIL_FROM, [to])
		msg.attach_alternative(html_content, "text/html")
		msg.send()
	response = True
	return HttpResponse(json.dumps(response), content_type='applicaction/json')

@csrf_exempt
@method_post
def viewNagoUsers(request):
	response = {}
	response['users'] = []

	if validate_args(request, 'id', 'num_ini', 'num_end', 'app') and exist_id_person(int(request.POST['id'])):
		if len(models.Profile.objects.all().exclude(id=int(request.POST['id']))) <= int(request.POST['num_end']):
			persons = models.Profile.objects.all().exclude(id=int(request.POST['id'])).order_by('id')[int(request.POST['num_ini']):int(request.POST['num_end'])]
		else:
			persons = models.Profile.objects.all().exclude(id=int(request.POST['id'])).order_by('id')[int(request.POST['num_ini']):]

		persons = exclude_friends(int(request.POST['id']), persons)

		for person in persons:
			data = {}
			data['id_person'] = person.id 
			if person.image:
				print person.image
				try:
					data['img_profile'] = SERVER_URL + person.image.url
				except:
					data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"

			data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
			if person.description is None:
				data['description'] = ""
			else:	
				data['description'] = person.description 
			data['is_friend'] = is_friend(int(request.POST['id']), person.id)
			response['users'].append(data)

	return HttpResponse(json.dumps(response), content_type='application/json')

@csrf_exempt
@method_post
def viewProfileSelf(request):
	response = {}
	if validate_args(request, 'id', 'app') and exist_id_person(int(request.POST['id'])):
		person = models.Profile.objects.get(id=int(request.POST['id']))
		response['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
		response['name'] = person.user.first_name
		response['lastname'] = person.user.last_name
		response['telephone'] = person.phone
		if person.birthdate is not None:
			response['birthdate'] = person.birthdate.strftime('%Y/%m/%d')
		else:
			response['birthdate'] = ""
		response['email'] = person.user.email
		if person.description is not None:
			response['description'] = person.description
		else:
			response['description'] = ""
		
	return HttpResponse(json.dumps(response), content_type='application/json')

@csrf_exempt
@method_post
def viewProfileUser(request):
	response = {}

	if validate_args(request, 'id', 'user_id', 'app') and exist_id_person(int(request.POST['user_id'])):
		person = models.Profile.objects.get(id=int(request.POST['user_id']))
		response['user_id'] = person.id
		response['username'] = person.user.username
		response['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
		response['name'] = person.user.first_name
		response['lastname'] = person.user.last_name
		response['telephone'] = person.phone
		response['email'] = person.user.email
		if person.description is not None:
			response['description'] = person.description
		else:
			response['description'] = ""
		response['ranking'] = 0 # validar el ranking
		response['is_friend'] = is_friend(int(request.POST['id']), person.id)

	return HttpResponse(json.dumps(response), 'application/json')

@csrf_exempt
@method_post
def sendInvitationFriend(request):
	response = False

	if validate_args(request, 'id', 'user_invitation_id', 'app') and exist_id_person(int(request.POST['id'])) and exist_id_person(int(request.POST['user_invitation_id'])):
		if len(models.Friendship.objects.filter(friend1=int(request.POST['id']), friend2=int(request.POST['user_invitation_id']))) == 0:
			person = models.Profile.objects.get(id=int(request.POST['id']))
			friend = models.Profile.objects.get(id=int(request.POST['user_invitation_id']))
			friends = models.Friendship(friend1=person.user, friend2=friend.user, state=3)
			friends.save()
			friends = models.Friendship(friend1=friend.user, friend2=person.user, state=3)
			friends.save()
			response = True
		
		elif len(models.Friendship.objects.filter(friend1=int(request.POST['id']), friend2=int(request.POST['user_invitation_id']), state=2)) == 1:
			friends_0 = models.Friendship.objects.get(friend1=int(request.POST['id']), friend2=int(request.POST['user_invitation_id']), state=2)
			friends_0.state = 3
			friends_0.save()

			friends_1 = models.Friendship.objects.get(friend2=int(request.POST['id']), friend1=int(request.POST['user_invitation_id']), state=2)
			friends_1.state = 3
			friends_1.save()
			response = True


	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def invitationViewFriends(request):
	response = {}

	if validate_args(request, 'id', 'num_ini', 'num_end', 'app'):
		if len(models.Friendship.objects.filter(friend1=int(request.POST['id']), state=3)) <= int(request.POST['num_end']):
			friends = models.Friendship.objects.filter(friend1=int(request.POST['id']), state=3)[int(request.POST['num_ini']):int(request.POST['num_end'])]
		else:
			friends = models.Friendship.objects.filter(friend1=int(request.POST['id']), state=3)[int(request.POST['num_ini']):]

		response['users'] = []

		for friend in friends:
			person = models.Profile.objects.get(id=friend.friend2.id)
			data = {}
			data['user_invitation_id'] = person.id
			
			try:
				data['img_profile'] = SERVER_URL + person.image.url
			except:
				data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"

			data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
			data['username'] = person.user.username
			if person.description is None:
				data['description'] = ""
			else:
				data['description'] = person.description

			response['users'].append(data)

	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewMyFriends(request):
	response = {}

	if validate_args(request, 'id', 'num_ini', 'num_end', 'app'):
		if len(models.Friendship.objects.filter(friend1=int(request.POST['id']), state=1)) <= int(request.POST['num_end']):
			friends = models.Friendship.objects.filter(friend1=int(request.POST['id']), state=1)[int(request.POST['num_ini']):int(request.POST['num_end'])]
		else:
			friends = models.Friendship.objects.filter(friend1=int(request.POST['id']), state=1)[int(request.POST['num_ini']):]

		response['users'] = []

		for friend in friends:
			person = models.Profile.objects.get(id=friend.friend2.id)
			data = {}
			data['user_invitation_id'] = person.id
			
			try:
				data['img_profile'] = SERVER_URL + person.image.url
			except:
				data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"

			data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
			data['username'] = person.user.username
			if person.description is not None:
				data['description'] = person.description
			else:
				data['description'] = ""
			response['users'].append(data)

	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewProfileFriend(request):
	response = {}

	if validate_args(request, 'id', 'friend_id', 'app') and len(models.Friendship.objects.filter(friend=int(request.POST['id']), friend2=int(request.POST['friend_id']), state=1)) > 0: 
		friend = models.Profile.objects.get(id=int(request.POST['friend_id']))
		response['friend_id'] = friend.id
		response['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
		response['username'] = friend.user.username
		response['email'] = friend.user.email
		response['description'] = friend.description
		response['ranking'] = 0

	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def responseInvitationFriendAccept(request):
	response = False

	if validate_args(request, 'id', 'user_invitation_id', 'app'):
		friends_0 = models.Friendship.objects.filter(friend1=int(request.POST['id']), friend2=int(request.POST['user_invitation_id']), state=3)
		friends_1 = models.Friendship.objects.filter(friend1=int(request.POST['user_invitation_id']), friend2=int(request.POST['id']), state=3)
		if len(friends_0) > 0 and len(friends_1) > 0:
			try:
				friend_0 = models.Friendship.objects.get(friend1=int(request.POST['id']), friend2=int(request.POST['user_invitation_id']), state=3)
				friend_0.state = 1; 
				friend_0.save()

				friend_1 = models.Friendship.objects.get(friend1=int(request.POST['user_invitation_id']), friend2=int(request.POST['id']), state=3)
				friend_1.state = 1; 
				friend_1.save()

			except Exception as e:
				print('Error: '+str(e))
			else:
				response = True
	
	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def responseInvitationFriendCancel(request):
	response = False

	if validate_args(request, 'id', 'user_invitation_id', 'app'):
		friends_0 = models.Friendship.objects.filter(friend1=int(request.POST['id']), friend2=int(request.POST['user_invitation_id']), state=3)
		friends_1 = models.Friendship.objects.filter(friend1=int(request.POST['user_invitation_id']), friend2=int(request.POST['id']), state=3)
		if len(friends_0) > 0 and len(friends_1) > 0:
			try:
				friend_0 = models.Friendship.objects.get(friend1=int(request.POST['id']), friend2=int(request.POST['user_invitation_id']), state=3)
				friend_0.state = 2 
				friend_0.save()

				friend_1 = models.Friendship.objects.get(friend1=int(request.POST['user_invitation_id']), friend2=int(request.POST['id']), state=3)
				friend_1.state = 2 
				friend_1.save()

			except:
				pass
			else:
				response = True
	
	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def validateCode(request):
	response = False

	if validate_args(request, 'id', 'code', 'app') and exist_id_person(int(request.POST['id'])):
		person = models.Profile.objects.get(id=int(request.POST['id']))
		person.code = code_generator()
		person.save()
		response = True

	return HttpResponse(json.dumps(response), 'contet-type/json')

@csrf_exempt
@method_post
def loanSolicitude(request):
	response = False
	print('deadline: '+str(request.POST['deadline']) )
	if validate_args(request, 'id', 'amount_request', 'interest', 'date_return', 'deadline', 'date_expiration', 'commentary', 'app') and validate_request_loan(request.POST['id']) and have_friends(request.POST['id']):
		print("on solicitude")
		response = True
		request_loans = models.LoanRequest()
		request_loans.amount_request = request.POST['amount_request']
		request_loans.amount_available = 0
		request_loans.interest = float(request.POST['interest'])
		request_loans.date_return = int(request.POST['date_return'].split(' ')[0])
		request_loans.date_expiration = request.POST['date_expiration']
		request_loans.commentary = request.POST['commentary']
		request_loans.deadline = request.POST['deadline']
		request_loans.user = models.User.objects.get(id=int(request.POST['id']))
		request_loans.state = True
		request_loans.save()

		#for friend in models.Friendship.objects.filter(friend2__id=int(request.POST['id']), state=1):
		#	friends_loans = models.Loan(loan_request=request_loans, friendship=friend)
		#	friends_loans.save()
	
	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewHistoryProfile(request):
	response = {}
	response['users'] = []
	
	if validate_args(request, 'id', 'num_ini', 'num_end', 'app'):
		person = models.Profile.objects.get(id=int(request.POST['id']))
		for request_loans in models.LoanRequest.objects.filter(user__id=int(request.POST['id'])).order_by('state'):
			data = {}
			data['id'] = person.id
			data['fullname'] = str(person.user.first_name).capitalize()+' '+str(person.user.last_name).capitalize()
			data['comment'] = str(request_loans.commentary)
			data['date_expiration'] = str(request_loans.date_expiration.year)+'-'+str(request_loans.date_expiration.month)+'-'+str(request_loans.date_expiration.day)
			date_return = addDate(request_loans.date_return, request_loans.date_expiration)
			data['date_return'] = str(date_return.year)+'-'+str(date_return.month)+'-'+str(date_return.day)
			data['date_return_day'] = request_loans.date_return
			data['amount_request'] = request_loans.amount_request
			data['amount_available'] = request_loans.amount_available
			data['amount_loan'] = 0
			data['invertors'] = len(models.Friendships_Loans.objects.filter(fk_request_loans=request_loans, state=True))
			data['id_history'] = request_loans.id
			
			response['users'].append(data)

	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewHistoryDetail(request):
	response = {}
	if validate_args(request, 'id', 'id_history', 'app'):
		try:
			request_loans = models.LoanRequest.objects.get(id=int(request.POST['id_history']))
			person = models.Profile.objects.get(id=int(request.POST['id']))
		except:
			pass
		else:
			response['user_id'] = person.id
			#response['loan_id'] = models.Friendships_Loans.objects.get(fk_friends=friends, fk_request_loans=request_loans).id
			response['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
			response['comment'] = request_loans.commentary
			response['description'] = person.description
			response['date_expiration'] = str(request_loans.date_expiration.year)+'-'+str(request_loans.date_expiration.month)+'-'+str(request_loans.date_expiration.day)
			date_return = addDate(request_loans.date_return, request_loans.date_expiration)
			response['date_return'] = str(date_return.year)+'-'+str(date_return.month)+'-'+str(date_return.day)
			response['date_return_day'] = request_loans.date_return
			response['date_create'] = str(request_loans.date_create.year)+'-'+str(request_loans.date_create.month)+'-'+str(request_loans.date_create.day)
			response['interest'] = request_loans.interest
			response['invertors'] = len(models.Friendships_Loans.objects.filter(fk_request_loans=request_loans, state=True))
			response['amount_request'] = request_loans.amount_request
			response['amount_available'] = request_loans.amount_available
			response['deadline'] = str(request_loans.deadline.year)+'-'+str(request_loans.deadline.month)+'-'+str(request_loans.deadline.day)
	
	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewExpectedProfile(request):
	response = {}
	response['users'] = []
	
	if validate_args(request, 'id', 'num_ini', 'num_end', 'app'):
		for friend in models.Friendship.objects.filter(friend__id=int(request.POST['id'])):
			for friend_loans in models.Friendships_Loans.objects.filter(fk_friends=friend, state=True):
				data = {}
				request_loans = models.LoanRequest.objects.get(id=friend_loans.fk_request_loans.id)
				person = models.Profile.objects.get(id=request_loans.friend.id) 
				data['id'] = person.id
				data['fullname'] = str(person.user.first_name).capitalize()+' '+str(person.user.last_name).capitalize()
				data['comment'] = str(request_loans.commentary)
				data['date_expiration'] = str(request_loans.date_expiration.year)+'-'+str(request_loans.date_expiration.month)+'-'+str(request_loans.date_expiration.day)
				date_return = addDate(request_loans.date_return, request_loans.date_expiration)
				data['date_return'] = str(date_return.year)+'-'+str(date_return.month)+'-'+str(date_return.day)
				data['date_return_day'] = request_loans.date_return
				data['amount_request'] = request_loans.amount_request
				data['amount_available'] = request_loans.amount_available
				data['amount_loan'] = 0
				data['invertors'] = len(models.Friendships_Loans.objects.filter(fk_request_loans=request_loans, state=True))
				data['id_history'] = request_loans.id
				data['deadline'] = str(request_loans.deadline.year)+'-'+str(request_loans.deadline.month)+'-'+str(request_loans.deadline.day)

				response['users'].append(data)
	print(response)
	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewFriendsLoans(request):
	response = {}
	response['users'] = []

	if validate_args(request, 'id', 'num_ini', 'num_end', 'app'):
		for friend in models.Friendship.objects.filter(friend__id=int(request.POST['id']), state=1):
			friends_loans = models.Friendships_Loans.objects.filter(fk_friends=friend, state=False)
			if len(friends_loans) > 0:
				friends_loans = friends_loans[0]
				data = {}
				person = models.Profile.objects.get(id=friend.friend2.id)
				data['id'] = person.id
				try: 
					data['img_profile'] = SERVER_URL + person.image.url
				except: 
					data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"
				data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
				data['comment'] = friends_loans.loan_request.commentary
				data['date_expiration'] = str(friends_loans.loan_request.date_expiration.year)+'-'+str(friends_loans.loan_request.date_expiration.month)+'-'+str(friends_loans.loan_request.date_expiration.day)
				data['date_return'] = friends_loans.loan_request.date_return
				data['amount_request'] = friends_loans.loan_request.amount_request
				data['amount_available'] = friends_loans.loan_request.amount_available
				data['interest'] = friends_loans.loan_request.interest
				response['users'].append(data)


	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewInvesteds(request):
	response = {}
	response['users'] = []

	if validate_args(request, 'id', 'num_ini', 'num_end', 'app'):
		for friend in models.Friendship.objects.filter(friend__id=int(request.POST['id']), state=1):
			friends_loans = models.Friendships_Loans.objects.filter(fk_friends=friend, state=False)
			if len(friends_loans) > 0:
				friends_loans = friends_loans[0]
				data = {}
				person = models.Profile.objects.get(id=friend.friend2.id)
				data['id'] = person.id
				try: 
					data['img_profile'] = SERVER_URL + person.image.url
				except: 
					data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"
				data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
				data['comment'] = friends_loans.loan_request.commentary
				data['date_expiration'] = str(friends_loans.loan_request.date_expiration.year)+'-'+str(friends_loans.loan_request.date_expiration.month)+'-'+str(friends_loans.loan_request.date_expiration.day)
				data['date_return'] = friends_loans.loan_request.date_return
				data['amount_request'] = friends_loans.loan_request.amount_request
				data['amount_available'] = friends_loans.loan_request.amount_available
				data['interest'] = friends_loans.loan_request.interest
				response['users'].append(data)


	return HttpResponse(json.dumps(response), 'content-type/json')


@csrf_exempt
@method_post
def viewLoanFriend(request):
	response = {}

	if validate_args(request, 'id', 'user_id', 'app'):
		person_self = models.Profile.objects.get(id=int(request.POST['id']))
		account = person_self.user.account
		request_loans = models.LoanRequest.objects.get(id=int(request.POST['loan_id']), state=True)
		person = models.Profile.objects.get(id=int(request.POST['user_id']))
		friends = models.Friendship.objects.get(friend1=person_self.user, friend2=person.user, state=1)
		
		response['user_id'] = person.id
		response['loan_id'] = request_loans.id
		response['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
		response['comment'] = request_loans.commentary
		response['description'] = person.description
		response['date_expiration'] = str(request_loans.date_expiration.year)+'-'+str(request_loans.date_expiration.month)+'-'+str(request_loans.date_expiration.day)
		response['date_return'] = request_loans.date_return
		response['date_create'] = str(request_loans.date_create.year)+'-'+str(request_loans.date_create.month)+'-'+str(request_loans.date_create.day)
		response['interest'] = float(request_loans.interest)
		response['invertors'] = len(models.Loan.objects.filter(loan_request=request_loans, state=True))
		response['amount_request'] = float(request_loans.amount_request)
		if account.amount_available >= request_loans.amount_request - request_loans.amount_available:
			response['amount_request_bar'] = int(request_loans.amount_request- request_loans.amount_available)
		else:
			response['amount_request_bar'] = int(account.amount_available)
	
		response['amount_available'] = float(request_loans.amount_available)
		response['deadline'] = str(request_loans.deadline.year)+'-'+str(request_loans.deadline.month)+'-'+str(request_loans.deadline.day)
		print('amount_request_bar: '+str(response['amount_request_bar']))		
	
	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def payLoanFriend(request):
	response = False
	if validate_args(request, 'id', 'loan_id', 'amount_loan', 'amount_interest', 'app'):
		try:
			friends_loans = models.Friendships_Loans.objects.get(id=int(request.POST['loan_id']), state=False)
			friends_loans.state = True
			friends_loans.save()
			loan = models.Loans()
		except:
			pass
		else:
			response = True
			loan.fk_friend_loans = friends_loans
			loan.amount_loan = request.POST['amount_loan']
			loan.amount_interest = request.POST['amount_interest']
			loan.save()

	return HttpResponse(json.dumps(response), 'context-type/json')

@csrf_exempt
@method_post
def viewFriendsLoansPay(request):
	response = {}
	response['users'] = []

	if validate_args(request, 'id', 'num_ini', 'num_end', 'app'):
		
		for friend in models.Friendship.objects.filter(friend__id=int(request.POST['id']), state=1):
			friends_loans = models.Friendships_Loans.objects.filter(fk_friends=friend, state=True)
			if len(friends_loans) > 0:
				friends_loans = friends_loans[0]
				data = {}
				person = models.Profile.objects.get(id=friend.friend2.id)
				laon = models.Loans.objects.get(fk_friend_loans=friends_loans)
				data['id'] = person.id
				try: 
					data['img_profile'] = SERVER_URL + person.image.url
				except: 
					data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"

				data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
				data['comment'] = friends_loans.loan_request.commentary
				data['date_expiration'] = str(friends_loans.loan_request.date_expiration.year)+'-'+str(friends_loans.loan_request.date_expiration.month)+'-'+str(friends_loans.loan_request.date_expiration.day)
				data['date_return'] = str(friends_loans.loan_request.date_return.year)+'-'+str(friends_loans.loan_request.date_return.month)+'-'+str(friends_loans.loan_request.date_return.day)
				data['amount_request'] = friends_loans.loan_request.amount_request
				data['amount_available'] = friends_loans.loan_request.amount_available
				data['amount_loan'] = laon.amount_loan
				data['amount_interest'] = laon.amount_interest
				data['interest'] = friends_loans.loan_request.interest
				response['users'].append(data)


	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def lendingSolicitude(request):
	response = {}
	response['error'] = True

	print('interest: '+str(request.POST['interest']))
	print('amount: '+str(request.POST['amount']))
	
	if validate_args(request, 'id', 'id_loand', 'interest','amount', 'app'):
		request_loan = models.LoanRequest.objects.get(id=int(request.POST['id_loand']))
		friendship = models.Friendship.objects.get(friend2=request_loan.user.id, friend1=int(request.POST['id']))
		friend_loans = models.Loan(loan_request=request_loan, friendship=friendship)
		friend_loans.amount_loan= float(request.POST['amount'])
		friend_loans.amount_interest= float(request.POST['interest'])
		friend_loans.state = True

		friend_loans.save()

		request_loan.amount_available += int(float(request.POST['amount']))
		request_loan.save()

		account = models.Account.objects.get(user__id=request_loan.user.id)
		account.amount_available = float(account.amount_available) - float('{0:.2f}'.format(float(request.POST['amount'])))
		account.amount_invested = float(account.amount_invested) + float('{0:.2f}'.format(float(request.POST['amount'])))
		account.save()

		person_so = models.Profile.objects.get(id=request.POST['id'])
		accout_person = friendship.friend2.account
		accout_person.amount_locked = float(accout_person.amount_locked) + float('{0:.2f}'.format(float(request.POST['amount'])))
		accout_person.save()

		response['amount_available'] = float(account.amount_available)
		response['amount_invested'] = float(account.amount_available)
		response['amount_locked'] = float(account.amount_locked)
		response['error'] = False

	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewAmountMarket(request):
	response = {}
	response['users'] = []

	if validate_args(request, 'id', 'num_ini', 'num_end', 'tipo', 'app') and exist_id_person(int(request.POST['id'])):
		num_ini = int(request.POST['num_ini'])
		num_end = int(request.POST['num_end'])
		
		if int(request.POST['tipo']) == 1:
			tipo = 'amount_request'
			print('mayor amount')
		else:
			tipo = '-amount_request'
			print('menor amount')

		if num_end < len(models.LoanRequest.objects.all()):
			requests_loans = models.LoanRequest.objects.filter(state=True).order_by(tipo)[num_ini:num_end]
		else:
			requests_loans = models.LoanRequest.objects.filter(state=True).order_by(tipo)[num_ini:]
		for request_loan in requests_loans:
			for friend in models.Friendship.objects.filter(friend1=int(request.POST['id']), state=1):
				if (request_loan.user.id == friend.friend2.id):
					person = models.Profile.objects.get(id=friend.friend2.id)
					data = {}
					data['id'] = person.id
					data['loan_id'] = request_loan.id

					try: 
						data['img_profile'] = SERVER_URL + person.image.url
					except: 
						data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"
					data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
					data['comment'] = request_loan.commentary
					data['date_expiration'] = str(request_loan.date_expiration.year)+'-'+str(request_loan.date_expiration.month)+'-'+str(request_loan.date_expiration.day)
					data['date_return'] = request_loan.date_return
					data['amount_request'] = float(request_loan.amount_request)
					data['amount_available'] = float(request_loan.amount_available)
					data['interest'] = float(request_loan.interest)
					
					days = datetime(request_loan.date_expiration.year, request_loan.date_expiration.month, request_loan.date_expiration.day) - datetime.now()
					data['days_finally'] = days.days
					response['users'].append(data)

	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewInterestMarket(request):
	response = {}
	response['users'] = []

	if validate_args(request, 'id', 'num_ini', 'num_end', 'tipo', 'app') and exist_id_person(int(request.POST['id'])):
		num_ini = int(request.POST['num_ini'])
		num_end = int(request.POST['num_end'])
		
		if int(request.POST['tipo']) == 1:
			tipo = 'interest'
			print('mayor interest')
		else:
			tipo = '-interest'
			print('menor interest')

		if num_end < len(models.LoanRequest.objects.all()):
			requests_loans = models.LoanRequest.objects.filter(state=True).order_by(tipo)[num_ini:num_end]
		else:
			requests_loans = models.LoanRequest.objects.filter(state=True).order_by(tipo)[num_ini:]
		
		for request_loan in requests_loans:
			for friend in models.Friendship.objects.filter(friend1=int(request.POST['id']), state=1):
				if (request_loan.user.id == friend.friend2.id):
					person = models.Profile.objects.get(id=friend.friend2.id)
					data = {}
					data['id'] = person.id
					data['loan_id'] = request_loan.id

					try: 
						data['img_profile'] = SERVER_URL + person.image.url
					except: 
						data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"
					data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
					data['comment'] = request_loan.commentary
					data['date_expiration'] = str(request_loan.date_expiration.year)+'-'+str(request_loan.date_expiration.month)+'-'+str(request_loan.date_expiration.day)
					data['date_return'] = request_loan.date_return
					data['amount_request'] = float(request_loan.amount_request)
					data['amount_available'] = float(request_loan.amount_available)
					data['interest'] = float(request_loan.interest)
					
					days = datetime(request_loan.date_expiration.year, request_loan.date_expiration.month, request_loan.date_expiration.day) - datetime.now()
					data['days_finally'] = days.days
					response['users'].append(data)


	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewDeadlineMarket(request):
	response = {}
	response['users'] = []

	if validate_args(request, 'id', 'num_ini', 'num_end', 'tipo', 'app') and exist_id_person(int(request.POST['id'])):
		num_ini = int(request.POST['num_ini'])
		num_end = int(request.POST['num_end'])
		
		if int(request.POST['tipo']) == 1:
			tipo = 'deadline'
			print('mayor deadline')
		else:
			tipo = '-deadline'
			print('menor deadline')

		if num_end < len(models.LoanRequest.objects.all()):
			requests_loans = models.LoanRequest.objects.filter(state=True).order_by(tipo)[num_ini:num_end]
		else:
			requests_loans = models.LoanRequest.objects.filter(state=True).order_by(tipo)[num_ini:]
		
		for request_loan in requests_loans:
			for friend in models.Friendship.objects.filter(friend1=int(request.POST['id']), state=1):
				if (request_loan.user.id == friend.friend2.id):
					person = models.Profile.objects.get(id=friend.friend2.id)
					data = {}
					data['id'] = person.id
					data['loan_id'] = request_loan.id

					try: 
						data['img_profile'] = SERVER_URL + person.image.url
					except: 
						data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"
					data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
					data['comment'] = request_loan.commentary
					data['date_expiration'] = str(request_loan.date_expiration.year)+'-'+str(request_loan.date_expiration.month)+'-'+str(request_loan.date_expiration.day)
					data['date_return'] = request_loan.date_return
					data['amount_request'] = float(request_loan.amount_request)
					data['amount_available'] = float(request_loan.amount_available)
					data['interest'] = float(request_loan.interest)
					
					days = datetime(request_loan.date_expiration.year, request_loan.date_expiration.month, request_loan.date_expiration.day) - datetime.now()
					data['days_finally'] = days.days
					response['users'].append(data)


	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewRequestedAccount(request):
	response = {}
	response['users'] = []

	if validate_args(request, 'id', 'num_ini', 'num_end', 'app') and exist_id_person(int(request.POST['id'])):
		person = models.Profile.objects.get(id=int(request.POST['id']))
		for request_loan in models.LoanRequest.objects.filter(user=person.user).order_by('state'):
			data = {}
			data['id'] = person.id
			try: 
				data['img_profile'] = SERVER_URL + person.image.url
			except: 
				data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"
			data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
			data['comment'] = request_loan.commentary
			data['date_expiration'] = str(request_loan.date_expiration.year)+'-'+str(request_loan.date_expiration.month)+'-'+str(request_loan.date_expiration.day)
			data['date_return'] = request_loan.date_return
			data['amount_request'] = float(request_loan.amount_request)
			data['amount_available'] = float(request_loan.amount_available)
			data['interest'] = float(request_loan.interest)
			data['return_day'] = request_loan.date_return
			
			response['users'].append(data)

	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewInvestedAccount(request):
	response = {}
	response['users'] = []

	if validate_args(request, 'id', 'num_ini', 'num_end', 'app') and exist_id_person(int(request.POST['id'])):
		person_id = models.Profile.objects.get(id=int(request.POST['id']))
		for request_loan in models.LoanRequest.objects.all().exclude(user=person_id.user).order_by('state'):
			for friend in models.Friendship.objects.filter(friend1__id=int(request.POST['id'])):
				if len(models.Loan.objects.filter(friendship=friend, loan_request=request_loan, state=True)) > 0:
					person = models.Profile.objects.get(id=friend.friend2.id)
					data = {}
					data['id'] = person.id
					try: 
						data['img_profile'] = SERVER_URL + person.image.url
					except: 
						data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"
					data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
					data['comment'] = request_loan.commentary
					data['date_expiration'] = str(request_loan.date_expiration.year)+'-'+str(request_loan.date_expiration.month)+'-'+str(request_loan.date_expiration.day)
					data['date_return'] = request_loan.date_return
					data['amount_request'] = float(request_loan.amount_request)
					data['amount_available'] = float(request_loan.amount_available)
					data['return_day'] = request_loan.date_return
					data['interest'] = float(request_loan.interest)
					
					response['users'].append(data)

	return HttpResponse(json.dumps(response), 'content-type/json')

@csrf_exempt
@method_post
def viewRequestdUser(request):
	response = {}
	
	if validate_args(request, 'id', 'id_user', 'app') and exist_id_person(int(request.POST['id'])):
		person = models.Profile.objects.get(id=int(request.POST['id']))
		request_loans = models.LoanRequest.objects.get(user=person.user, state=True)
		
		response['id'] = person.id
		response['fullname'] = str(person.user.first_name).capitalize()+' '+str(person.user.last_name).capitalize()
		response['comment'] = str(request_loans.commentary)
		response['date_expiration'] = str(request_loans.date_expiration.year)+'-'+str(request_loans.date_expiration.month)+'-'+str(request_loans.date_expiration.day)
		date_return = addDate(request_loans.date_return, request_loans.date_expiration)
		response['date_return'] = str(date_return.year)+'-'+str(date_return.month)+'-'+str(date_return.day)
		response['date_return_day'] = request_loans.date_return
		response['amount_request'] = float(request_loans.amount_request)
		response['amount_available'] = float(request_loans.amount_available)
		response['amount_loan'] = 0
		response['interest'] = float(request_loans.interest)
		response['invertors'] = len(models.Loan.objects.filter(loan_request=request_loans, state=True))
		response['id_history'] = request_loans.id
		response['return_day'] = request_loans.date_return
		response['deadline'] = str(request_loans.deadline.year)+'-'+str(request_loans.deadline.month)+'-'+str(request_loans.deadline.day)
		
	return HttpResponse(json.dumps(response), 'content_type/json')

@csrf_exempt
@method_post
def viewInvestedUser(request):
	response = {}

	if validate_args(request, 'id', 'id_user', 'app') and exist_id_person(int(request.POST['id'])):
		person = models.Profile.objects.get(id=int(request.POST['id_user']))
		request_loans = models.LoanRequest.objects.get(user=person.user, state=True)
		
		response['id'] = person.id
		response['fullname'] = str(person.user.first_name).capitalize()+' '+str(person.user.last_name).capitalize()
		response['comment'] = str(request_loans.commentary)
		response['date_expiration'] = str(request_loans.date_expiration.year)+'-'+str(request_loans.date_expiration.month)+'-'+str(request_loans.date_expiration.day)
		date_return = addDate(request_loans.date_return, request_loans.date_expiration)
		response['date_return'] = str(date_return.year)+'-'+str(date_return.month)+'-'+str(date_return.day)
		response['date_return_day'] = request_loans.date_return
		response['amount_request'] = float(request_loans.amount_request)
		response['amount_available'] = float(request_loans.amount_available)
		response['amount_loan'] = 0
		response['interest'] = float(request_loans.interest)
		response['invertors'] = len(models.Loan.objects.filter(loan_request=request_loans, state=True))
		response['id_history'] = request_loans.id
		response['return_day'] = request_loans.date_return
		response['deadline'] = str(request_loans.deadline.year)+'-'+str(request_loans.deadline.month)+'-'+str(request_loans.deadline.day)
		
	return HttpResponse(json.dumps(response), 'content_type/json')

# -------------------------------------------------------------------------

@csrf_exempt
@method_post
def userNagoFilter(request):
	response = {}
	response['users'] = []

	if validate_args(request, 'id', 'username','app') and exist_id_person(int(request.POST['id'])):
		list_person = models.User.objects.filter(username__startswith=str(request.POST['username']).lower())
		persons = filterUser(list_person)
		# persons = models.User.objects.filter(user__username=str(request.POST['username']))
		persons = exclude_friends(int(request.POST['id']), persons)

		for person in persons:
			data = {}
			data['id_person'] = person.id 

			try:
				data['img_profile'] = SERVER_URL + person.image.url
			except:
				data['img_profile'] = SERVER_URL + "/static/image/default_user_icon.png"
			data['fullname'] = str(person.user.first_name).capitalize()+" "+str(person.user.last_name).capitalize()
			if person.description is not None:
				data['description'] = person.description 
			else:
				data['description'] = ""

			data['is_friend'] = is_friend(int(request.POST['id']), person.id)
			response['users'].append(data)

	return HttpResponse(json.dumps(response), content_type='application/json')

@csrf_exempt
@method_post
def validatePin(request):
	response = False
	print(request.POST['pin'])

	if validate_args(request, 'id', 'pin','app') and len(models.Profile.objects.filter(id=int(request.POST['id']), pin=str(request.POST['pin']))) > 0:
		response = True
		print('entro')
		
	return HttpResponse(json.dumps(response), content_type='applicaction/json')
@csrf_exempt
@method_post
def checkInUser(request):
	response = False
	
	if validate_args(request, 'id' ,'customer_dwolla', 'type', 'number_aba', 'amount', 'account_number', 'app') and exist_id_person(int(request.POST['id'])):
		print('customer_dwolla: '+str(request.POST['customer_dwolla']))
		print('number_aba: '+str(request.POST['number_aba']))
		print('amount: '+str(request.POST['amount']))
		print('account_number: '+str(request.POST['account_number']))
		print('type: '+str(request.POST['type']))

		person = models.Profile.objects.get(id=int(request.POST['id']))
		account = person.user.account
		
		try:
			client = dwollav2.Client(key = APP_KEY, secret = APP_SECRET, environment = 'sandbox')
			client_id = account.customer_dwolla.split('/')[len(account.customer_dwolla.split('/')) - 1]
			print(client_id)
			request_body = {
			'routingNumber': str(request.POST['number_aba']),
			'accountNumber': str(request.POST['account_number']),
			'type': str(request.POST['type']),
			'name': str(person.user.first_name).capitalize()+' - '+str(person.user.last_name).capitalize()
			}

			account_token = client.Token(access_token=ACCESS_TOKEN, refresh_token=client.Auth.client())

			
			# Using dwollav2 - https://github.com/Dwolla/dwolla-v2-python (Recommended)
			customer = account_token.post('%s/funding-sources' % request.POST['customer_dwolla'], request_body)
			source = customer.headers['location'] # => 'https://api-uat.dwolla.com/funding-sources/375c6781-2a17-476c-84f7-db7d2f6ffb31'
			
			root = account_token.get('/')
			account_url = str(root.body['_links']['account']['href'])
			# Using dwollav2 - https://github.com/Dwolla/dwolla-v2-python (Recommended)
			funding_sources = account_token.get('%s/funding-sources' % account_url)
			funding_id = str(funding_sources.body['_embedded']['funding-sources'][0]['id'])
			print('id: '+funding_id) # => 'ABC Bank Checking'		

			transfer_request = {
				'_links': {
					'source': {
					'href': 'https://api.dwolla.com/funding-sources/'+str(funding_id)
					},
					'destination': {
					'href': 'https://api.dwolla.com/customers/'+str(client_id)
					}
				},
				'amount': {
					'currency': 'USD',
					'value': str(request.POST['amount'])
				},
				'metadata': {
					'customerId': str(client_id),
					'notes': 'For work completed on Sept. 1, 2015'
				}
			}

			# Using dwollav2 - https://github.com/Dwolla/dwolla-v2-python (Recommended)
			transfer = account_token.post('transfers', transfer_request)
			transfer.headers['location'] # => 'https://api.dwolla.com/transfers/d76265cd-0951-e511-80da-0aa34a9b2388'
		except Exception as e:
			print "--------------------"
			print e
			print "--------------------"
		else:
			response = True
		
	return HttpResponse(json.dumps(response), 'application/json')

@csrf_exempt
@method_post
def checkOutUser(request):
	print('cash out')
	print('customer_dwolla: '+str(request.POST['customer_dwolla']))
	print('number_aba: '+str(request.POST['number_aba']))
	print('amount: '+str(request.POST['amount']))
	print('account_number: '+str(request.POST['account_number']))
	print('type: '+str(request.POST['type']))

	return HttpResponse(json.dumps(False), content_type='application/json')