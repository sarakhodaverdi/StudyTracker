
import matplotlib
import os
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns 
import pandas as pd 
import numpy as np
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from io import BytesIO
import base64
from datetime import datetime, timedelta
from .models import Subject, StudySession

# 1. Login View (آدرس: '')
def login_view(request):
    # اگر کاربر از قبل لاگین هست، مستقیم بره داشبورد و ارور نده
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")
            return redirect('login') 
            
   
    return render(request, 'registration/login.html')

# 2. Register View (آدرس: 'register/')
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# 3. Logout View (آدرس: 'logout/')
def logout_view(request):
    logout(request)
    return redirect('login') # برمی‌گرده به آدرس اصلی که لاگینه

# 4. Dashboard View (آدرس: 'dashboard/')
@login_required
def dashboard(request):
    user = request.user
    subjects = Subject.objects.filter(user=user)
    today_date = datetime.today().date()

    if request.method == 'POST':
        if 'add_subject' in request.POST:
            name = request.POST.get('subject_name', '').strip()
            if name:
                if Subject.objects.filter(user=user, name__iexact=name).exists():
                    messages.error(request, f'"{name}" is already added!')
                else:
                    Subject.objects.create(user=user, name=name)
                    messages.success(request, f'Subject "{name}" added!')
        
        elif 'add_session' in request.POST:
            subject_id = request.POST.get('subject') 
            date_str = request.POST.get('date')
            hours = request.POST.get('hours')
            if subject_id and date_str and hours:
                try:
                    subject = Subject.objects.get(id=subject_id, user=user)
                    StudySession.objects.create(subject=subject, date=date_str, hours=float(hours))
                    messages.success(request, 'Session logged!')
                except Exception as e:
                    messages.error(request, f'Error: {e}')
        return redirect('dashboard')

    # بخش نمودارها
    start_date = today_date - timedelta(days=6)
    sessions = StudySession.objects.filter(
        subject__user=user, 
        date__gte=start_date, 
        date__lte=today_date
    ).order_by('date')

    data = []
    for s in sessions:
        data.append({
            'date': s.date.strftime('%Y-%m-%d'),
            'hours': float(s.hours),
            'subject': s.subject.name
        })
    
    df = pd.DataFrame(data)
    plot_url = None
    trend_url = None
    stats = {'avg': 0, 'max': 0, 'total': 0}
    subject_stats = []

    if not df.empty:
        df = df.groupby(['date', 'subject'], as_index=False)['hours'].sum()
        daily_total = df.groupby('date')['hours'].sum()
        stats['avg'] = round(daily_total.mean(), 1)
        stats['max'] = daily_total.max()
        stats['total'] = df['hours'].sum()

        for sub_name in df['subject'].unique():
            sub_df = df[df['subject'] == sub_name]
            subject_stats.append({
                'name': sub_name,
                'avg': round(sub_df['hours'].mean(), 1),
                'total': sub_df['hours'].sum()
            })

        # Plot 1: Stacked Bar
        pivot_df = df.pivot(index='date', columns='subject', values='hours').fillna(0)
        vibrant_colors = ["#F472B6", "#A78BFA", "#34D399", "#FBBF24", "#60A5FA", "#FB7185", "#A3E635"]
        plt.figure(figsize=(10, 6))
        ax = pivot_df.plot(kind='bar', stacked=True, color=vibrant_colors[:len(pivot_df.columns)], ax=plt.gca(), edgecolor='white')
        for c in ax.containers:
            labels = [f'{v:.1f}h' if v > 0.2 else '' for v in c.datavalues]
            ax.bar_label(c, labels=labels, label_type='center', color='white', fontsize=9, fontweight='bold')
        plt.title('Daily Study Breakdown', fontweight='bold')
        plt.xticks(rotation=45)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plot_url = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        # Plot 2: Trend Line
        plt.figure(figsize=(10, 5))
        sns.lineplot(data=df, x='date', y='hours', hue='subject', marker='o', palette=vibrant_colors[:len(df['subject'].unique())])
        plt.xticks(rotation=45)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        trend_url = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close('all')

    context = {
        'subjects': subjects,
        'plot_url': plot_url,
        'trend_url': trend_url,
        'stats': stats,
        'subject_stats': subject_stats,
        'today': today_date.strftime('%Y-%m-%d')
    }
    return render(request, 'study/dashboard.html', context)


