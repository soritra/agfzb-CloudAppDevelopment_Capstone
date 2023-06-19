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
# from django.views import View
from django.http import JsonResponse
from django.views.generic import ListView
from datetime import datetime, date

from .models import CarMake, CarModel, DealerReview
from .restapis import analyze_review_sentiments, get_dealers_from_cf, get_dealers_by_state, get_dealer_by_id_from_cf, get_dealer_reviews_from_cf, get_next_review_id, post_request

dotenv_path = join(dirname(dirname(__file__)), '.env/dev')
load_dotenv(dotenv_path)

IBM_FUNCTION_URL = str(getenv('IBM_FUNCTION_URL'))
IBM_FUNCTION_URL2 = str(getenv('IBM_FUNCTION_URL2'))
IBM_FUNCTION_URL3 = str(getenv('IBM_FUNCTION_URL3'))

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
            url = "{}/dealerships/get-dealership".format(IBM_FUNCTION_URL3)
            # url = "{}/actions/dealerships/get-dealership".format(IBM_FUNCTION_URL)
            # https://eu-de.functions.appdomain.cloud/api/v1/web/bf93106d-ebc3-44c8-a699-fab865125ad6/dealerships/get-dealership.json
            # Get dealers from the URL
            dealerships = get_dealers_from_cf(url)
            # Concat all dealer's short name
            dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
            # Return a list of dealer short name
            # return HttpResponse(dealer_names)
#            carmodels = CarModel.objects.all().order_by('-type')
#            context['carmodels'] = carmodels
            context['dealership_list'] = dealerships
        except:
            print("Network exception dship occurred")
        return render(request, 'djangoapp/index.html', context)


# display the list of dealers by state
def get_dealerships_by_state(request):
    if request.method == "GET":
        url = "{}/dealerships/get-dealership".format(IBM_FUNCTION_URL3)
        state = request.GET.get('state')
        st = request.GET.get('st')
        # Get dealers from the URL
        if state:
            dealerships = get_dealers_by_state(url, state=state)
            return JsonResponse(dealerships, safe=False, json_dumps_params={'indent': 2}, status=200)
        elif st:
            dealerships = get_dealers_by_state(url, st=st)
            print("dshp", dealerships)
            return JsonResponse(dealerships, safe=False, json_dumps_params={'indent': 2}, status=200)
        else:
            return JsonResponse({
                "success": False,
                "message": "Parameter 'st' or 'state' required!"
            }, safe=False, json_dumps_params={'indent': 2}, status=500)


# render the reviews of a dealer
def get_dealer_details(request):
    context = {}
    dealer_id = request.GET.get('dealerId')
    if dealer_id is None:
        dealer_id = request.GET.get('dealer_id')
    if (dealer_id):
        context['dealer_id'] = dealer_id
        try:
            reviews = []
            url = "{}/dealerships/get-review".format(IBM_FUNCTION_URL3)
            # url = "{}/actions/dealerships/get-review".format(IBM_FUNCTION_URL)
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
            print("Network exception occurred when retrieving dealer details!")
    return render(request, 'djangoapp/dealer_details.html', context)
    

# view to submit a review
def add_review(request, dealer_id):
    context = {
        'dealer_id': dealer_id
    }
    if request.method == 'GET':
        # try:
        url = "{}/dealerships/get-dealership".format(IBM_FUNCTION_URL3)
        dealer = get_dealer_by_id_from_cf(url, dealer_id)
        context['dealer_name'] = dealer.full_name if not dealer is None else ''
        cars = CarModel.objects.filter(Q(dealer__contains=dealer_id)).order_by('name')
        # print("cars", [(c.name, c.make.name, c.year) for c in cars])
        context['cars'] = cars
        # rertieve next review id
        url = "{}/reviews/_all_docs?include_docs=false".format(IBM_FUNCTION_URL2)
        next_id = get_next_review_id(url)
        context['next_id'] = next_id
        # except:
        #     print("Network exception encountered when adding a review!")
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
            url = "{}/dealerships/post-review".format(IBM_FUNCTION_URL3)
            req = post_request(url, review, dealer_id=dealer_id)
            # print(json.loads(req.text))
            # return HttpResponseRedirect(reverse(viewname='djangoapp:add_review', args=(dealer_id,)))
        return redirect(reverse('djangoapp:dealer_details') + "?dealerId={}".format(dealer_id))
        # return HttpResponseRedirect(reverse(viewname='djangoapp:dealer_details'))
        # return HttpResponseRedirect(reverse(viewname='djangoapp:dealer_details', args=(dealer_id,)))


#  pre-define a list of car makes to be inserted in the database
# car_makes = [
#     CarMake(id=1, name='Mercedes-Benz', description='German car - Daimler group'),
#     CarMake(id=2, name='VW', description='German car - VolksWagen group'),
#     CarMake(id=3, name='Audi', description='German car - VolksWagen group'),
#     CarMake(id=4, name='BMW', description='German car - BMW group'),
#     CarMake(id=5, name='Ford', description='US car - Ford group')
# ]

# # car makes class-based view
# class CarMakesView(ListView):
#     model = CarMake
#     # queryset
#     queryset = CarMake.objects.all()
#     if not queryset.exists():
#         # insert multiple records
#         CarMake.objects.bulk_create(car_makes)
    
    
#     # retrieve all car records
#     def get_queryset(self):
#         return CarMake.objects.all()


# # pre-define a list of car models to be inserted in the database
# car_models = [
#     CarModel(id=1, name='A5', make=car_makes[2], type='coupe', year=2007, dealer=(2,8,11,17,24,31,33,36,41,44,49)),
#     CarModel(id=2, name='Golf 7', make=car_makes[1], type='hatchback', year=2012, dealer=(3,10,12,15,23,28,35,39,42,44,48)),
#     CarModel(id=3, name='CLS', make=car_makes[0], type='coupe', year=2014, dealer=(4,7,10,19,21,27,37,40,42,46,47,49)),
#     CarModel(id=4, name='X6', make=car_makes[3], type='suv', year=2017, dealer=(5,9,11,18,20,25,34,38,39,41,45,48,49)),
#     CarModel(id=5, name='Mustang', make=car_makes[4], type='coupe', year=2016, dealer=(7,8,12,17,18,29,32,36,37,42,45,46,47))
# ]

# # Car models class-based view
# class CarModelsView(ListView):
#     model = CarModel
#     # queryset
#     queryset = CarModel.objects.all()
#     carmake_queryset = CarMake.objects.all()
#     if not queryset.exists() and carmake_queryset.exists():
#         # insert multiple records 
#         CarModel.objects.bulk_create(car_models)
    
    
#     # retrieve all car records
#     def get_queryset(self):
#         return CarModel.objects.all()

