from django.db import models
from django.utils import timezone
import datetime
import pytz
# Create your models here.

class User(models.Model):
    name = models.CharField(max_length=100)
    document = models.CharField(max_length=100, blank=True)
    annotations = models.TextField(blank=True)

    def __str__(self):
        return self.name
    @property
    def has_tag(self):
        return len(TagAssignment.objects.filter(user=self, begin__lte=timezone.now(),
         end__gte=timezone.now())) > 0

class Tag(models.Model):
    status = models.BooleanField()
    uid = models.CharField(max_length=20, default='00')

    @property
    def is_assigned(self):
        return len(TagAssignment.objects.filter(tag=self, begin__lte=timezone.now(),
         end__gte=timezone.now())) > 0

    def __str__(self):
        return f'ID: {self.id}; UID: {self.uid}'

class TagAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    begin = models.DateTimeField()
    end = models.DateTimeField(default=datetime.datetime(9999, 12, 31, 0, 0, 0, 0, pytz.UTC))
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    def __str__(self):
        return 'Tag {} -> {}'.format(self.tag.id, self.user)

    def is_valid(self):
        return self.begin <= timezone.now() and (self.end >= timezone.now())

    @staticmethod
    def active_assigments():
        return TagAssignment.objects.filter(begin__lte=timezone.now(),
         end__gte=timezone.now())

class Arduino(models.Model):
    arduino_mac = models.CharField(max_length=25)

    @property
    def is_assigned(self):
        return len(ArduinoAssignment.objects.filter(arduino=self, begin__lte=timezone.now(),
         end__gte=timezone.now())) > 0

    def get_valid_assignment(self):
        ard_query = ArduinoAssignment.objects.filter(arduino=self, begin__lte=timezone.now(),
         end__gte=timezone.now())
        if len(ard_query) > 0:
            return ard_query[0]
        else:
            return None

    def __str__(self):
        return f'MAC: {self.arduino_mac}'

class Login(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    time = models.DateTimeField()
    successful = models.BooleanField()
    arduino = models.ForeignKey(Arduino, on_delete=models.CASCADE)

    def get_tag(self):
        try:
            return Tag.objects.get(uid=self.tag_uid)
        except:
            return None

class LocationHistory(models.Model):
    login = models.ForeignKey(Login, on_delete=models.CASCADE, blank=True, null=True)
    arduino = models.ForeignKey(Arduino, on_delete=models.CASCADE)
    location = models.CharField(max_length=50)
    datetime_field = models.DateTimeField()

class UnregistredTag(models.Model):
    uid = models.CharField(max_length=50)
    time = models.DateTimeField()

    def __str__(self):
        return f'UID: {self.uid} @ {self.time}'

class Car(models.Model):
    license_plate = models.CharField(max_length=20)
    description = models.TextField()

    @property
    def has_arduino(self):
        return len(ArduinoAssignment.objects.filter(car=self, begin__lte=timezone.now(),
         end__gte=timezone.now())) > 0

    def __str__(self):
        too_long = len(self.description) > 30
        if too_long:
            return f'Placa: {self.license_plate}. Desc: {self.description[0:30]}...'
        else:
            return f'Placa: {self.license_plate}. Desc: {self.description}'



class ArduinoAssignment(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    arduino = models.ForeignKey(Arduino, on_delete=models.CASCADE)
    begin = models.DateTimeField()
    end = models.DateTimeField(default=datetime.datetime(9999, 12, 31, 0, 0, 0, 0, pytz.UTC))

    @staticmethod
    def active_assigments():
        return ArduinoAssignment.objects.filter(begin__lte=timezone.now(),
         end__gte=timezone.now())

    def __str__(self):
        return f'Leitor {self.arduino.id} -> {self.car.license_plate}'