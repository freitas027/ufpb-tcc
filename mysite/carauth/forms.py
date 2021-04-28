from django import forms
from django.forms import ModelForm
from .models import TagAssignment, Tag, User, UnregistredTag, Arduino, Car, ArduinoAssignment

class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime'

class UserForm(forms.Form):

    #user_name = forms.CharField(label='Nome do Usuário', max_length=100, widget=forms.Select(choices=users))
    user_name = forms.CharField(label='Nome do Usuário', max_length=100)
    document = forms.CharField(label='Documento (Opcional)', max_length=100)
    description = forms.CharField(label='Observações (Opcional)', max_length=1000)


class TagRegistragionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(TagRegistragionForm, self).__init__(*args, **kwargs)
        users = [(user.id, user.name) for user in User.objects.all() if not user.has_tag]
        tags = [(tag.id, str(tag)) for tag in Tag.objects.all() if not tag.is_assigned]
        self.fields['user_name'] = forms.CharField(label='Usuários sem tag registrada', max_length=100, widget=forms.Select(choices=users))
        self.fields['available_tags'] = forms.CharField(label='Tags disponíveis', max_length=100, widget=forms.Select(choices=tags))

class ReaderRemovalForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ReaderRemovalForm, self).__init__(*args, **kwargs)
        items = [(ard_as.id, str(ard_as)) for ard_as in ArduinoAssignment.active_assigments()]
        self.fields['assignments'] = forms.CharField(label='Associações ativas', max_length=250, widget=forms.Select(choices=items))

class TagRemovalForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(TagRemovalForm, self).__init__(*args, **kwargs)
        items = [(tag_as.id, str(tag_as)) for tag_as in TagAssignment.active_assigments()]
        self.fields['assignments'] = forms.CharField(label='Associações ativas', max_length=250, widget=forms.Select(choices=items))
class NewTagForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(NewTagForm, self).__init__(*args, *kwargs)
        items = [(urtag.id, str(urtag)) for urtag in UnregistredTag.objects.all()]
        self.fields['unregistred_tags'] = forms.CharField(label='Tags desconhecidas: ', max_length=100, widget=forms.Select(choices=items))

class NewArduinoAssignment(forms.Form):
    def __init__(self, *args, **kwargs):
        super(NewArduinoAssignment, self).__init__(*args, **kwargs)
        ards = [(ard.id, str(ard)) for ard in Arduino.objects.all() if not ard.is_assigned]
        self.fields['available_ard'] = forms.CharField(label='Leitores Disponíveis: ', max_length=100, widget=forms.Select(choices=ards))
        cars = [(car.id, str(car)) for car in Car.objects.all() if not car.has_arduino]
        self.fields['available_car'] = forms.CharField(label='Carros Disponíveis: ', max_length=100, widget=forms.Select(choices=cars))

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['license_plate', 'description']
        labels = {
            'license_plate': 'Número da placa',
            'description': 'Descrição (Opcional)',
        }


