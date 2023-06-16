import logging
import json
from os import getenv
from os.path import dirname, join
from dotenv import load_dotenv
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from datetime import datetime, date

from .models import CarMake, CarModel, DealerReview
from .restapis import analyze_review_sentiments, get_dealers_from_cf, get_dealer_by_id_from_cf, get_dealer_reviews_from_cf, get_next_review_id, post_request

dotenv_path = join(dirname(dirname(__file__)), '.env.dev')
load_dotenv(dotenv_path)

IBM_FUNCTION_URL = str(getenv('IBM_FUNCTION_URL'))
IBM_FUNCTION_URL2 = str(getenv('IBM_FUNCTION_URL2'))

# Get an instance of a logger
logger = logging.getLogger(__name__)


# render a static about page
def about(request):
    context = {}
    return render(request, 'djangoapp/about.html', context)


# return a static contact page
def contact(request):
    context = {}
    return render(request, 'djangoapp/contact.html', context)

  
# handle sign in request
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


# handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')


# handle sign up request
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


# render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        try:
            url = "{}/actions/dealerships/get-dealership".format(IBM_FUNCTION_URL)
            # Get dealers from the URL
            dealerships = get_dealers_from_cf(url)
            # Concat all dealer's short name
            dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
            # Return a list of dealer short name
            # return HttpResponse(dealer_names)
            carmodels = CarModel.objects.all().order_by('-type')
            context['carmodels'] = carmodels
            context['dealership_list'] = dealerships
        except:
            print("Network exception occurred")
        return render(request, 'djangoapp/index.html', context)


# render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    context = {
        'dealer_id': dealer_id
    }
    if (dealer_id):
        try:
            reviews = []
            url = "{}/actions/dealerships/get-review".format(IBM_FUNCTION_URL)
            reviews_list = get_dealer_reviews_from_cf(url, dealer_id)
            current_year = date.today().year
            if (reviews_list):
                for review in reviews_list:
                    # dt = str(review['purchase_date']).split('/')[2]
                    age = int(current_year) - int(review['car_year'])
                    pfx = "" if review['purchase'] else "not "
                    txt = "{} {}, {} years old car, {}, {}purchased".format(review['car_make'], review['car_model'], age, review['review'], pfx)
                    sentiment = analyze_review_sentiments(txt)
                    # print(sentiment)
                    id = review["id"] if "id" in review else (review["id2"] if "id2" in review else None)
                    review_obj = DealerReview(id=id, name=review["name"], dealership=review["dealership"],
                                        purchase=review["purchase"], purchase_date=review["purchase_date"],
                                        car_make=review["car_make"], car_model=review["car_model"],
                                        car_year=review["car_year"], review=review["review"],
                                        sentiment=sentiment)
                    reviews.append(review_obj)
            context['reviews'] = reviews
        except:
            print("Network exception occurred")
    return render(request, 'djangoapp/dealer_details.html', context)
    

# view to submit a review
def add_review(request, dealer_id):
    context = {
        'dealer_id': dealer_id
    }
    if request.method == 'GET':
        try:
            url = "{}/actions/dealerships/get-dealership".format(IBM_FUNCTION_URL)
            dealer = get_dealer_by_id_from_cf(url, dealer_id)
            context['dealer_name'] = dealer.full_name
            cars = CarModel.objects.filter(Q(dealer__contains=dealer_id)).order_by('name')
            # print("cars", [(c.name, c.make.name, c.year) for c in cars])
            context['cars'] = cars
            # rertieve next review id
            url = "{}/reviews/_all_docs?include_docs=false".format(IBM_FUNCTION_URL2)
            next_id = get_next_review_id(url)
            context['next_id'] = next_id
        except:
            print("Network exception occurred!")
        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == 'POST':
        user = request.user
        if user and user.is_authenticated:
            # print(request.POST)
            # return render(request, 'djangoapp/add_review.html', context)
            car = CarModel.objects.get(id=int(request.POST["car"]))
            review = {}
            review["time"] = datetime.utcnow().isoformat()
            review["name"] = "{} {}".format(user.first_name, user.last_name)
            review["dealership"] = dealer_id
            review["dealer_id"] = dealer_id
            review["id"] = request.POST["next_id"]
            review["review"] = request.POST["content"]
            review["purchase"] = True if "purchase_check" in request.POST and request.POST["purchase_check"] == 'on' else False
            review["purchase_date"] = request.POST["purchase_date"] if review["purchase"] else ""
            review["car_make"] = car.make.name
            review["car_model"] = car.name
            review["car_year"] = car.year
            # print(review)
            url = "{}/actions/dealerships/post-review".format(IBM_FUNCTION_URL)
            req = post_request(url, review, dealer_id=dealer_id)
            # print(json.loads(req.text))
            # return HttpResponseRedirect(reverse(viewname='djangoapp:add_review', args=(dealer_id,)))
            # return redirect("djangoapp:dealer_details")
        return HttpResponseRedirect(reverse(viewname='djangoapp:dealer_details', args=(dealer_id,)))


# render the index page with a list of dealerships
def get_dealerships2(request, state_name=None):
    context = {}
    dealerships = get_dealers_from_cf()
    carmodels = CarModel.objects.all().order_by('-type')
    context['carmodels'] = carmodels
    context['dealership_list'] = dealerships
    return render(request, 'djangoapp/index.html', context)

