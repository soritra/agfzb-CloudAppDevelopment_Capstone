from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

from .models import CarMake, CarModel
from .restapis import get_dealers_from_cf, get_dealer_by_id_from_cf, get_review_by_dealer_from_cf, analyze_review_sentiments

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create an `about` view to render a static about page
def about(request):
    context = {}
    return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    return render(request, 'djangoapp/contact.html', context)

  
# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return redirect('djangoapp:index')
    else:
        return redirect('djangoapp:index')


# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')


# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)


# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request, state_name=None):
    context = {}
    dealerships = get_dealers_from_cf()
    carmodels = CarModel.objects.all().order_by('-type')
    context['carmodels'] = carmodels
    context['dealership_list'] = dealerships
    return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    context = {}
    if (dealer_id):
        dealer = get_dealer_by_id_from_cf(dealer_id)
        # print(dealer)
        reviews = get_review_by_dealer_from_cf(dealer_id)
        # print(reviews)
        if (reviews):
            # context['sentiments'] = []
            for review in reviews:
                dt = str(review['purchase_date']).split('/')[2]
                age = int(dt) - int(review['car_year'])
                pfx = "" if review['purchase'] else "not "
                txt = "{} {}, {} years old car, {}, {}purchased".format(review['car_make'], review['car_model'], age, review['review'], pfx)
                # print(dt, txt)
                sentiment = analyze_review_sentiments(txt)
                # print(sentiment)
                review['sentiment'] = sentiment
        context['reviews'] = reviews
    # print(context)
    return render(request, 'djangoapp/dealer_details.html', context)
    

# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    pass

