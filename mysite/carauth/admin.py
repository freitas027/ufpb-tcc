from django.contrib import admin

from .models import Tag, User, TagAssignment, Login, LocationHistory, UnregistredTag, Arduino, Car, ArduinoAssignment
# Register your models here.


admin.site.register(Tag)
admin.site.register(User)
admin.site.register(TagAssignment)
admin.site.register(Login)
admin.site.register(LocationHistory)
admin.site.register(UnregistredTag)
admin.site.register(Arduino)
admin.site.register(Car)
admin.site.register(ArduinoAssignment)
