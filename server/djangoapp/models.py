from django.db import models
from django.utils.timezone import now


class CarMake(models.Model):
  name = models.CharField(null=False, max_length=80, default='car make')
  description = models.CharField(max_length=1000)
# - Any other fields you would like to include in car make model
  
  def __str__(self):
    return "Car {} - {}".format(self.id, self.name)
    

# <HINT> Create a plain Python class `CarDealer` to hold dealer data
# class CarDealer:
#   pass


class CarDealer(models.Model):
  name = models.CharField(null=False, max_length=100, )
  
  def __str__(self):
    return "Dealer: {}".format(self.name)


# <HINT> Create a Car Model model `class CarModel(models.Model):`:
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
  type = models.CharField(null=False, max_length=100, )
  year = models.DateField(null=True)
  make = models.ForeignKey(CarMake, on_delete=models.CASCADE)
  dealer = models.ForeignKey(CarDealer, on_delete=models.CASCADE)
  
  def __str__(self):
    return "Car model: {} - {} (by {})".format(self.name, self.make.name, self.dealer.name)


# <HINT> Create a plain Python class `DealerReview` to hold review data
# class DealerReview:
#   pass

class DealerReview(models.Model):
  content = models.TextField()
  dealer = models.ForeignKey(CarDealer, on_delete=models.CASCADE)
  date_created_at = models.DateField(default=now)
  rating = models.FloatField(default=5.0)
  
  def __str__(self):
    return "Dealer review: {} (by {})".format(self.content, self.dealer.name)

