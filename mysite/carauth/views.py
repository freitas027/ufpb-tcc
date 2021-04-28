from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import Login, TagAssignment, Tag, User, LocationHistory, UnregistredTag, Arduino, ArduinoAssignment, Car
import datetime
from django.core.paginator import Paginator
import pytz
from .forms import UserForm, TagRegistragionForm, TagRemovalForm, NewTagForm, NewArduinoAssignment, CarForm, ReaderRemovalForm
from django.contrib.auth.decorators import login_required
import logging
import traceback

# Create your views here.

# TODO delete all objects from database

# TODO create a list of tag number with query for login :(Tag.object.get(uid=login.tag_uid))

@login_required
def index(request):
    login_list = Login.objects.all().order_by('-time')

    ard_assign = []
    tag_assign = []
    link_list = []
    for login in login_list:

        try:
            tag_assign.append(TagAssignment.objects.get(tag=login.tag,
            begin__lte=login.time, end__gte=login.time))
        except:
            tag_assign.append(None)
        try:
            ard_assign.append(ArduinoAssignment.objects.get(arduino=login.arduino,
            begin__lte=login.time, end__gte=login.time))
        except:
            ard_assign.append(None)


        link ='/path/{}/'.format(login.id)
        link_list.append(link)

    # ah stands for authentication history
    return render(request, 'carauth/index.html', {'ah': zip(login_list, ard_assign, tag_assign, link_list)})
@login_required
def view_tag_assignments(request, page):
    p = Paginator(TagAssignment.objects.all(), 2)
    return render(request, 'carauth/tag_assignments.html', {'tagass': p.page(page).object_list, 'page': page, 'page_range': p.page_range})

@csrf_exempt
def post_test(request):
    tag_uid = request.POST['tag']

    #time = datetime(*[int(i) for i in request.POST['time'].split('-')], pytz.UTC)


    location = request.POST['location']

    mac_id = request.POST['mac'].replace('_', ':')

    try:
        tag_instance = Tag.objects.get(uid=tag_uid)
        success = len(TagAssignment.objects.filter(tag__uid=tag_uid, begin__lte=timezone.now(),
            end__gte=timezone.now())) > 0 and tag_instance.status == True
    except:
        success = False



    query_tag = Tag.objects.filter(uid=tag_uid)
    if len(query_tag) == 0:
        tag = Tag()
        tag.status = True
        tag.uid = tag_uid
        tag.save()
    else:
        tag = query_tag[0]

    arduino = get_object_or_404(Arduino, arduino_mac=mac_id)

    l = Login()
    l.tag = tag
    l.time = timezone.now()
    l.location = location
    l.arduino = arduino
    l.successful = success
    l.save()

    if success:
        return HttpResponse(f'alw:{l.id}')
    else:
        return HttpResponse(f'dnd:{l.id}')

@csrf_exempt
def post_location(request):
    if request.method == 'POST':
        try:
            try:
                login_id = request.POST['id']
                if 'pos' in request.POST:
                    location = request.POST['pos'].replace('_', ',')
                datetime_str = request.POST['time']
                mac = request.POST['mac'].replace('_', ':')
            except Exception as e:
                raise Http404('Invalid post request: {}\n\n{}'.format(request.body, traceback.format_exc()))
            try:
                login = get_object_or_404(Login, id=int(login_id))
            except:
                login = None

            lh = LocationHistory()
            lh.login = login
            lh.location = location
            lh.datetime_field = datetime.datetime.strptime(datetime_str, '%Y-%m-%d-%H-%M-%S')
            arduino = get_object_or_404(Arduino, arduino_mac=mac)
            lh.arduino = arduino
            #lh.datetime_field = timezone.now()
            lh.save()
            return HttpResponse('ok')
        except Exception as e:
            return HttpResponse(str(e))
    else:
        raise Http404('Invalid')

@login_required
def add_user(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = UserForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            user = User()
            user.name = form.data['user_name']
            user.document = form.data['document']
            user.annotations = form.data['description']
            user.save()
            return HttpResponseRedirect('/index/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = UserForm()

    return render(request, 'carauth/form.html', {'form': form})

@login_required
def assign_tag(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = TagRegistragionForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            tagas = TagAssignment()
            tagas.user = User.objects.get(id=form.cleaned_data['user_name'])
            tagas.tag = Tag.objects.get(id=form.cleaned_data['available_tags'])
            tagas.begin = timezone.now()

            tagas.save()

            return HttpResponseRedirect('/index/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = TagRegistragionForm()
    action = '/register/'
    return render(request, 'carauth/form.html', {'form': form, 'action':action})

@login_required
def remove_assign(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = TagRemovalForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            tagas = TagAssignment.objects.get(id=form.cleaned_data['assignments'])

            tagas.end = timezone.now()

            tagas.save()

            return HttpResponseRedirect('/index/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = TagRemovalForm()
    action = '/remove-assignment/'
    return render(request, 'carauth/form.html', {'form': form, 'action':action})

@login_required
def remove_reader_assignment(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ReaderRemovalForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            ard_as = ArduinoAssignment.objects.get(id=form.cleaned_data['assignments'])

            ard_as.end = timezone.now()

            ard_as.save()

            return HttpResponseRedirect('/index/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ReaderRemovalForm()
    action = '/remove-reader-assignment/'
    return render(request, 'carauth/form.html', {'form': form, 'action':action})

def hello(request):
    return HttpResponse('Hello!$', content_type='')

@csrf_exempt
def get_time(request, mac):
    arduinos = Arduino.objects.filter(arduino_mac=mac)
    if len(arduinos) == 0:
        arduino = Arduino()
        arduino.arduino_mac = mac
        arduino.save()
    if request.method == 'GET':
        return HttpResponse(timezone.now().strftime('%Y-%m-%d-%H-%M-%S'))

@login_required
def new_ard_assign(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = NewArduinoAssignment(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:

            ard_id = form.cleaned_data['available_ard']
            car_id = form.cleaned_data['available_car']
            ard = Arduino.objects.get(id=ard_id)
            car = Car.objects.get(id=car_id)
            ard_ass = ArduinoAssignment()
            ard_ass.car = car
            ard_ass.arduino = ard
            ard_ass.begin = timezone.now()
            ard_ass.save()


            return HttpResponseRedirect('/index/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = NewArduinoAssignment()
    action = '/new-ard-assign/'
    return render(request, 'carauth/form.html', {'form': form, 'action':action})

@login_required
def new_car(request):
    if request.method == 'POST':
        form = CarForm(request.POST)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect('/index/')
    else:
        form = CarForm()
    action = '/new-car/'
    return render(request, 'carauth/form.html', {'form': form, 'action':action})

def get_login_gapi_path(request, login_id):
    location_history = LocationHistory.objects.filter(login__id=login_id).order_by('datetime_field')
    args = 'path=color:0x0000ff|weight:5|' + '|'.join([lh.location for lh in location_history])
    if len(location_history) > 0:
        args = 'markers=color:green%7Clabel:A%7C{}&'.format(location_history.first().location) + args
    if len(location_history) > 1:
        args = 'markers=color:red%7Clabel:B%7C{}&'.format(location_history.last().location) + args
    link ='https://maps.googleapis.com/maps/api/staticmap?size=500x500&{}&key=AIzaSyDq-1ugkbdIZvedpje9rxHojr3Do0VpokU'.format(args)
    return redirect(link)