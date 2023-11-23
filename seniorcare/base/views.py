from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django. contrib import messages
from .models import senior_list, SMSMessage
from .forms import register_form
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponse
import csv

from django.conf import settings
from django.http import JsonResponse
from twilio.rest import Client

from django.contrib import messages
from django.utils import timezone

import json
import base64
import numpy as np
import cv2
import os
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import face_recognition
import dlib


from django.http import HttpResponseRedirect, FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

from django.template.loader import get_template
from xhtml2pdf import pisa

# Create your views here.

def index(request):
    return render(request, 'index.html'  )

def index(request):
    page = 'index'

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User does not exist')
            return render(request, 'index.html', {'page': page})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(update_page)
        else:
            messages.error(request, 'Invalid Password')
            
    context = {'page': page}
    return render(request, 'index.html', context)

def home_page(request):
    return render(request, 'home_page.html'  )

def register_page(request):
    return render(request, 'register_page.html')

def main_page(request):
    return render(request, 'main.html')

def register_page(request):
    form = register_form()
    if request.method == 'POST':
        form = register_form(request.POST, request.FILES)  
        if form.is_valid():
            seniors = form.save()
            return redirect('preview', id=seniors.id)
    context = {'form': form}
    return render(request, 'register_page.html', context)

def update_page(request):
    seniors = senior_list.objects.all().order_by('last_name')
    return render(request, 'update_page.html', {'seniors': seniors})

def update_viewinfo_page(request, id):
    seniors = senior_list.objects.get(id=id)
    return render(request, 'update_viewinfo_page.html', {'seniors': seniors})

def edit(request, id):
    seniors = senior_list.objects.get(id=id)
    return render(request, 'edit.html', {'seniors': seniors})




def update(request, id):

    seniors = senior_list.objects.get(id=id)
    if request.method == 'POST':
        form = register_form(request.POST, request.FILES, instance=seniors)
        if form.is_valid():
            if 'senior_image' in request.FILES:
                if seniors.senior_image:
                    os.remove(seniors.senior_image.url)
                seniors.senior_image = request.FILES['senior_image']
        seniors.last_name = request.POST.get('Lastname')
        seniors.first_name = request.POST.get('Firstname')
        seniors.middle_name = request.POST.get('Middlename')
        seniors.suffix = request.POST.get('Suffix')
        seniors.age = request.POST.get('Age')
        seniors.sex = request.POST.get('sex')
        seniors.address = request.POST.get('Adress')
        seniors.phone_number = request.POST.get('phone_number')
        seniors.save()
    context = {'seniors': seniors}
    return render ( request, 'update_viewinfo_page.html', context)
    


#oks na to delete function
def delete(request, id):
    seniors = senior_list.objects.get(id=id)
    seniors.delete()
    return redirect(update_page)


def search(request):
    if 'q' in request.GET:
        q= request.GET['q']
        #seniors= senior_list.objects.filter(last_name__icontains=q)
        multiple_q=Q(Q(last_name__icontains=q) | Q(first_name__icontains=q))
        seniors = senior_list.objects.filter(multiple_q)
    else:
        seniors=senior_list.objects.all()
    context={'seniors': seniors}
    return render(request, 'update_page.html', context)

def search1(request):
    if 'q' in request.GET:
        q= request.GET['q']
        #seniors= senior_list.objects.filter(last_name__icontains=q)
        multiple_q=Q(Q(last_name__icontains=q) | Q(first_name__icontains=q))
        seniors = senior_list.objects.filter(multiple_q)
    else:
        seniors=senior_list.objects.all()
    context={'seniors': seniors}
    return render(request, 'claim_page.html', context)

def claim_page(request):
    seniors = senior_list.objects.all().order_by('last_name')
    return render(request, 'claim_page.html', {'seniors': seniors})

def claim_detail_page(request, id):
    seniors = senior_list.objects.get(id=id)
    return render(request, 'claim_detail_page.html', {'seniors': seniors})

def claimed_success(request, id):
    seniors = senior_list.objects.get(id=id)
    return render(request, 'claimed_success.html', {'seniors': seniors})


def claimed_succesfully(request, id):
    seniors = get_object_or_404(senior_list, pk=id)
    seniors.is_claimed = True
    seniors.claimed_date = timezone.now()
    seniors.save()

    context = {
        'last_name': seniors.last_name,
        'first_name': seniors.first_name,
        'middle_name': seniors.middle_name,
        'OSCA_ID': seniors.OSCA_ID,
        'claimed_date': seniors.claimed_date,
    }
    return render(request, 'claimed_success.html', context)


def claim_verify_page(request):
    claimed_seniors = senior_list.objects.filter(is_claimed=True).order_by('last_name')
    unclaimed_seniors = senior_list.objects.filter(is_claimed=False).order_by('last_name')
    seniors = list(claimed_seniors) + list(unclaimed_seniors)

    return render(request, 'claim_verify_page.html', {'seniors': seniors})

def claim_summary_page(request):
    claimed_seniors = senior_list.objects.filter(is_claimed=True)
    unclaimed_seniors = senior_list.objects.filter(is_claimed=False)

    claimed_count = claimed_seniors.count()
    unclaimed_count = unclaimed_seniors.count()
    overall_count = claimed_count + unclaimed_count

    return render(request, 'claim_summary_page.html', {
        'claimed_count': claimed_count,
        'unclaimed_count': unclaimed_count,
        'overall_count': overall_count,
    })


def download_summary(request):
    seniors = senior_list.objects.all().order_by('last_name')


    content={'seniors':seniors}
    template_path = 'report.html'
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(content)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    senior_list.objects.update(is_claimed=False)
    return response

    

def sms(request):
    messages = SMSMessage.objects.all()
    context={'messages':messages}

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        body_message = request.POST.get('body_message')

        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        twilio_phone_number = settings.TWILIO_PHONE_NUMBER

        client = Client(account_sid, auth_token)

        try:
            message = client.messages.create(
                body=body_message,
                from_=twilio_phone_number,
                to=phone_number
            )

            current_date = timezone.now()

            SMSMessage.objects.create(
                from_number=settings.TWILIO_PHONE_NUMBER,
                body=body_message,
                timestamp=current_date
            )

            response_data = {
                'status': 'success',
                'message': f'Message sent successfully! SID: {message.sid}'
            }
        except Exception as e:
            response_data = {
                'status': 'error',
                'message': f'Failed to send message. Error: {str(e)}'
            }

        return JsonResponse(response_data)

    return render(request, 'sms.html', context )

def clear_messages(request):
    if request.method == 'POST':
        SMSMessage.objects.all().delete()
    return render(request, 'sms.html')

def delete_individual_message(request, message_id):
    message = SMSMessage.objects.get(id=message_id)
    message.delete()
    return redirect(sms)
    

def preview(request, id):
    seniors = senior_list.objects.get(id=id)
    return render(request, 'preview.html', {'seniors': seniors})

def camera(request):
    return render(request, 'capture_image.html')

@csrf_exempt
def capture_image(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            image_data = data.get('image_data', '')

            image_data = base64.b64decode(image_data.split(',')[1])
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            timestamp = datetime.now().strftime("%Y%m%d%")
            filename = f"captured_image_{timestamp}.png"
            filepath = os.path.join(settings.MEDIA_ROOT, filename)
            cv2.imwrite(filepath, img)
            
            return JsonResponse({'image_path': filepath})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)



@csrf_exempt
def facial_recognition(request, id):
    seniors = senior_list.objects.get(id=id)

    if request.method == 'POST':
        captured_image_data_url = request.POST.get('captured_image', '')
        
        _, captured_image_base64 = captured_image_data_url.split(',')
        captured_image = np.frombuffer(base64.b64decode(captured_image_base64), np.uint8)

        captured_image_np = cv2.imdecode(captured_image, -1)

        if captured_image_np is None:
            return JsonResponse({'error': 'Unable to load the image.'})

        known_face_encoding = get_known_face_encoding(seniors.senior_image.path)

        face_locations = face_recognition.face_locations(captured_image_np)
        captured_face_encodings = face_recognition.face_encodings(captured_image_np, face_locations)

        for captured_face_encoding in captured_face_encodings:
            match = compare_faces(known_face_encoding, captured_face_encoding)

            if match:
                seniors.is_claimed = True
                seniors.claimed_date = timezone.now()
                seniors.save()

                return JsonResponse({'match': True})
    
    return JsonResponse({'match': False})

def get_known_face_encoding(image_path):

    known_image = face_recognition.load_image_file(image_path)

    known_face_encoding = face_recognition.face_encodings(known_image)

    if known_face_encoding:
        return known_face_encoding[0] 
    else:
        return None

def compare_faces(known_encoding, captured_encoding):
    threshold = 0.5
    distance = face_recognition.face_distance([known_encoding], captured_encoding)

    return distance <= threshold


def camera_page(request, id):
    seniors = senior_list.objects.get(id=id)
    return render(request, 'camera.html', {'seniors': seniors})

def match(request, id):
    seniors = senior_list.objects.get(id=id)
    return render(request, 'match.html', {'seniors': seniors})

def check_osca_id(request):
    osca_id = request.GET.get('osca_id', '')
    is_taken = senior_list.objects.filter(OSCA_ID=osca_id).exists()
    return JsonResponse({'is_taken': is_taken})