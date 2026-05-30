from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.contrib.auth.decorators import login_required 
from django.contrib.auth import logout as auth_logout
import numpy as np
import joblib
from .forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm



def home(request):
    return render(request, 'users/home.html')

@login_required(login_url='users-register')


def index(request):
    return render(request, 'app/index.html')

class RegisterView(View):
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'users/register.html'

    def dispatch(self, request, *args, **kwargs):
        # will redirect to the home page if a user tries to access the register page while logged in
        if request.user.is_authenticated:
            return redirect(to='/')

        # else process dispatch as it otherwise normally would
        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')

            return redirect(to='login')

        return render(request, self.template_name, {'form': form})


# Class based view that extends from the built in login view to add a remember me functionality

class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True

        # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
        return super(CustomLoginView, self).form_valid(form)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('users-home')


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'users/change_password.html'
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy('users-home')


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile is updated successfully')
            return redirect(to='users-profile')
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(request, 'users/profile.html', {'user_form': user_form, 'profile_form': profile_form})

import google.generativeai as genai
from django.shortcuts import render
import re
import time

from google.api_core.exceptions import ResourceExhausted
from django.core.cache import cache
from .models import PasswordAnalysis

# 🔑 Configure API
genai.configure(api_key="AIzaSyDfDApqX4J-lyXTe_aY-EBwOdtO7BN9VFg")
model = genai.GenerativeModel("gemini-2.5-flash")


# 🧠 Extract score
def extract_score(text):
    match = re.search(r'\b(\d{1,3})\b', text)
    if match:
        return min(int(match.group(1)), 100)
    return 50


# 🟢 Input Page
def detect(request):
    return render(request, "app/detect.html")


# 🟢 Output Page
def detect_output(request):
    if request.method == "POST":
        password = request.POST.get("password")

        # 🚫 Prevent spam (per IP)
        user_ip = request.META.get('REMOTE_ADDR')
        if cache.get(user_ip):
            return render(request, "app/detect_out.html", {
                "password": password,
                "score": 0,
                "result": "⏳ Please wait a few seconds before trying again."
            })

        cache.set(user_ip, True, timeout=15)

        prompt = f"""
        Analyze this password: {password}

        Give:
        Score (0-100)
        Explanation
        Risks
        Suggestions
        """

        try:
            response = model.generate_content(prompt)

        except ResourceExhausted:
            time.sleep(15)
            try:
                response = model.generate_content(prompt)
            except Exception:
                return render(request, "app/detect_out.html", {
                    "password": password,
                    "score": 0,
                    "result": "⚠️ Server busy. Try again later."
                })

        except Exception:
            return render(request, "app/detect_out.html", {
                "password": password,
                "score": 0,
                "result": "⚠️ Error occurred."
            })

        output = response.text
        score = extract_score(output)

        # 💾 Save to DB
        PasswordAnalysis.objects.create(
            password=password,
            score=score,
            description=output
        )

        return render(request, "app/detect_out.html", {
            "password": password,
            "result": output,
            "score": score
        })

    return render(request, "app/detect.html")


def detect_db(request):
    data = PasswordAnalysis.objects.all().order_by('-created_at')

    return render(request, "app/detect_db.html", {
        "data": data
    })



from .models import Profile
def profile_list(request):
    # Fetch all profile objects from the database
    profiles = Profile.objects.all()
    
    # Pass the profiles data to the template
    return render(request, 'app/profile_list.html', {'profiles': profiles})


def logout_view(request):  
    auth_logout(request)
    return redirect('/')


