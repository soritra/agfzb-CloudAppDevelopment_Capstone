from django.contrib import admin
from .models import CarMake, CarModel, ExternalToken


# Register your models here.

# CarModelInline class

# CarModelAdmin class

# CarMakeAdmin class with CarModelInline

# Register models here
admin.site.register(ExternalToken)
admin.site.register(CarMake)
admin.site.register(CarModel)

