import datetime
# from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.timezone import now
from multiselectfield import MultiSelectField


class CarMake(models.Model):
  name = models.CharField(null=False, max_length=80, default='car make')
  description = models.CharField(max_length=1000)
  
  def __str__(self):
    return "{} - {}".format(self.id, self.name)
    

# class `CarDealer` to hold dealer data
class CarDealer:
  def __init__(self, address, city, full_name, id, lat, long, short_name, st, zip):
    # Dealer address
    self.address = address
    # Dealer city
    self.city = city
    # Dealer Full Name
    self.full_name = full_name
    # Dealer id
    self.id = id
    # Location lat
    self.lat = lat
    # Location long
    self.long = long
    # Dealer short name
    self.short_name = short_name
    # Dealer state
    self.st = st
    # Dealer zip
    self.zip = zip
  
  def __str__(self):
    return "Dealer name: " + self.full_name


def year_choices():
  return [(x, x) for x in range(1980, current_year())]


def current_year():
  return datetime.date.today().year


# Car Model model:
# - Many-To-One relationship to Car Make model (One Car Make has many Car Models, using ForeignKey field)
# - Name
# - Dealer id, used to refer a dealer created in cloudant database
# - Type (CharField with a choices argument to provide limited choices such as Sedan, SUV, WAGON, etc.)
# - Year (DateField)
# - Any other fields you would like to include in car model
# - __str__ method to print a car make object
class CarModel(models.Model):
  name = models.CharField(null=False, max_length=100, default='car model')
  SEDAN, HATCHBACK, MPV, SUV, CROSSOVER, COUPE, CONVERTIBLE = 'sedan', 'hatchback', 'mpv', 'suv', 'crossover', 'coupe', 'convertible'  
  TYPE_CHOICES = (
    (COUPE, 'Coupe'),
    (CONVERTIBLE, 'Convertible'),
    (CROSSOVER, 'Crossover'),
    (HATCHBACK, 'Hatchback'),
    (MPV, 'Multi Purpose Vehicle (MPV)'),
    (SEDAN, 'Sedan'),
    (SUV, 'Sports Utility Vehicle (SUV)')
  )
  type = models.CharField(
    null=False,
    max_length=30,
    choices=TYPE_CHOICES,
    default=SEDAN
  )
  # year = models.DateField(null=True)
  year = models.PositiveIntegerField(
    choices=year_choices(),
    default=current_year()
  )
  make = models.ForeignKey(CarMake, on_delete=models.CASCADE)
  DEALER_CHOICES = ((i, i) for i in range(1,51))
  dealer = MultiSelectField(
    null=True,
    choices=DEALER_CHOICES
  )
  
  def __str__(self):
    return "{} {} - {}".format(self.make.name, self.name, self.get_type_display())


# class `DealerReview` to hold review data
class DealerReview:
  def __init__(self, id, name, dealership, purchase, purchase_date, car_make, car_model, car_year, review, sentiment):
    # Dealer id
    self.id = id
    # Dealer name
    self.name = name
    # Dealership
    self.dealership = dealership
    # Dealer purchase
    self.purchase = purchase
    # purchase date
    self.purchase_date = purchase_date
    # car make
    self.car_make = car_make
    # car model
    self.car_model = car_model
    # car year
    self.car_year = car_year
    # Dealer review
    self.review = review
    # Dealer sentiment
    self.sentiment = sentiment

  def __str__(self):
    return "Dealer name: " + self.full_name


# Hold IBM active token value and expiration
class ExternalToken(models.Model):
  id = models.IntegerField(primary_key=True)
  value = models.TextField()
  # expiration time in milliseconds
  expiration = models.IntegerField()
  # expiration = models.CharField(null=False, default=1, max_length=15)

