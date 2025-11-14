import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns 
import pandas as pd 
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponse
from io import BytesIO
import base64
from datetime import datetime, timedelta
from study.models import Subject, StudySession


def login_view(request):
    if request.method == 'POST' :
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Incorect username or password!')
    return render(request, 'registration/login.html')


def register_view(request):
    if request.method == 'POST' :
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('usernameme')
            messages.success(request,'Account created successfully.login now.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')

def dashboard(request):
    user = request.user
    subjects = Subject.objects.filter(user=user)

    if request.method == 'POST': #and 'add_subect' in request.POST:
        subject_id = None
        date_str = None
        hours = None
        if 'add_subject' in request.POST:
            name = request.POST.get('subject_name', '').strip()
            if name:
                Subject.objects.create(user=user, name=name)
        if 'add_session' in request.POST:
            subject_id = request.POST.get('subject')
   # if request.method == 'POST' and 'add_session' in request.POST:
        #subject_id = request.POST.get('subject')
            date_str = request.POST.get('date')
            hours =float(request.POST.get('hours'))

        if subject_id and date_str and hours:
            try:
                subject= Subject.objects.get(id = subject_id, user=request.user)
                StudySession.objects.create(subject=subject, date=date_str, hours=float(hours))
            except:
                pass
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=6)
    sessions = StudySession.objects.filter(subject__user=user, date__gte=start_date, date__lte=end_date).order_by('date')

    data = []
    for s in sessions:
        if s.date and s.hours is not None:
            data.append({
                'date': s.date.strftime('%Y-%m-%d'),
                'hours': float(s.hours),
                'subject': s.subject.name
            })
    df = pd.DataFrame(data)

    #polo_url = None

    context = {
            'subjects' : subjects,
            'plot_url' : None
        }

    if not df.empty:
        plt.figure(figsize=(10, 5))
        sns.barplot(data=df, x='date', y='hours', hue='subject', palette='viridis')
        plt.title('Study trend of the last seven days:') 
        plt.xlabel('date')
        plt.ylabel('study hours')
        plt.xticks(rotation=45)
        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plot_url = base64.b64encode(image_png).decode('utf-8')
        plt.close()


        context['plot_url'] = plot_url
        
    return render(request, 'study/dashboard.html', context)



