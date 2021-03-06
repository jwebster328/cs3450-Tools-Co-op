import csv, io
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import datetime
from datetime import timedelta

from .models import Tool, CustomerInfo, Message


def index(request):  # Main page
    context = {}
    return render(request, 'Toolshop/index.html', context)


def projects_page(request):
    context = {}
    return render(request, 'Toolshop/projects.html', context)


def tools_page(request):
    tools_list = Tool.objects.order_by('category')
    context = {
        'tools_list': tools_list
    }
    return render(request, 'Toolshop/tools.html', context)


def contact_page(request):
    context = {}
    return render(request, 'Toolshop/contact.html', context)


def login_page(request):
    context = {}
    return render(request, 'Toolshop/login.html', context)


@login_required
def account_page(request):
    user = request.user
    tools_list = Tool.objects.filter(who_checked_out__contains=user.username)
    for tool in tools_list:
        # Temporarily change the variable to represent the day the tool is due.
        tool.date_checked_out = tool.date_checked_out + timedelta(days=7)
        # Do NOT save the new data with Tool.save()
    context = {
        'user': user,
        'tools_list': tools_list
    }
    return render(request, 'Toolshop/account.html', context)


@login_required
def reservation_page(request):
    tools_list = Tool.objects.order_by('category')
    context = {
        'tools_list': tools_list
    }
    return render(request, 'Toolshop/reservation.html', context)


@login_required
def reservation_page_specific(request, contains):  # This page has the results trimmed down by a search query
    if request.POST.get('query') is not None:
        contains = request.POST.get('query')
    tools_list = Tool.objects.filter(name__contains=contains).order_by('category')
    context = {
        'tools_list': tools_list
    }
    return render(request, 'Toolshop/reservation.html', context)

@login_required
def make_reservation(request, id):
    tool = get_object_or_404(Tool, pk=id)
    tool.is_checked_out = True
    tool.times_checked_out += 1
    tool.date_checked_out = timezone.now()
    tool.who_checked_out = request.user.username
    current_user = get_object_or_404(CustomerInfo, user=request.user)
    current_user.num_currently_checked_out += 1
    tool.save()
    current_user.save()
    context = {}
    return render(request, 'Toolshop/redirect.html', context)


def update_user_info(request):
    user = request.user
    first_name = request.POST.get('firstName')
    last_name = request.POST.get('lastName')
    address = request.POST.get('address')
    email_address = request.POST.get('email')
    password_1 = request.POST.get('psw')
    password_2 = request.POST.get('psw-repeat')

    if password_1 != password_2:
        return HttpResponseRedirect(reverse('Toolshop:updateError'))
    elif first_name is None or last_name is None or address is None or email_address is None or password_1 is None:
        return HttpResponseRedirect(reverse('Toolshop:updateError'))
    elif first_name == "" or last_name == "" or address == "" or email_address == "" or password_1 == "":
        return HttpResponseRedirect(reverse('Toolshop:updateError'))
    elif len(first_name) > 30 or len(last_name) > 30 or len(email_address) > 50:
        return HttpResponseRedirect(reverse('Toolshop:updateError'))
    elif len(password_1) < 8 or len(password_1) > 30:
        return HttpResponseRedirect(reverse('Toolshop:updateError'))

    user.first_name = first_name
    user.last_name = last_name
    user.email = email_address
    user.address = address
    user.set_password(password_1)

    user.save()
    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('Toolshop:redirect'))


def submit_message(request):
    first_name = request.POST.get('firstname')
    last_name = request.POST.get('lastname')
    email_address = request.POST.get('emailAddress')
    subject = request.POST.get('subject')
    message = request.POST.get('textBody')

    if first_name is None or last_name is None or email_address is None or subject is None or message is None:
        return HttpResponseRedirect(reverse('Toolshop:error'))
    elif first_name == "" or last_name == "" or email_address == "" or subject == "" or message == "":
        return HttpResponseRedirect(reverse('Toolshop:error'))
    elif len(first_name) > 30 or len(last_name) > 30 or len(email_address) > 50:
        return HttpResponseRedirect(reverse('Toolshop:error'))
    elif len(subject) > 100 or len(message) > 1000:
        return HttpResponseRedirect(reverse('Toolshop:error'))

    new_message = Message(first_name=first_name, last_name=last_name,
                          email=email_address, subject=subject,
                          message=message)
    new_message.save()
    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('Toolshop:redirect'))


def submission_error(request):
    context = {}
    return render(request, 'Toolshop/submission_error.html', context)


def update_error(request):
    context = {}
    return render(request, 'Toolshop/update_error.html', context)


def redirection_page(request):
    context = {

    }
    return render(request, 'Toolshop/redirect.html', context)


@permission_required('admin.can_add_log_entry')
def database_upload(request):
    template = "Toolshop/database_upload.html"
    prompt = {
        'order': 'Order of CSV should be category, name, value, quantity, on-hand, checked-out'
    }
    if request.method == "GET":
        return render(request, template, prompt)
    csv_file = request.FILES['file']
    if not csv_file.name.endswith('.csv'):
        messages.error(request, "This is not a CSV file")
    data_set = csv_file.read().decode('UTF-8')
    io_string = io.StringIO(data_set)
    next(io_string)
    for column in csv.reader(io_string, delimiter=','):
        print(int(column[3]))
        for i in range(int(column[3])):
            print("creating " + column[1])
            created = Tool(
                category=column[0],
                name=column[1],
                cost=column[2],
                times_checked_out=0
            )
            created.save()
    context = {

    }
    return render(request, template, context)

