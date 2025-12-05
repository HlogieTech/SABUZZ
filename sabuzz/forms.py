from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Post, Profile, Comment, Subscriber

# -----------------------------
# Signup (legacy) - optional
# -----------------------------
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")


# -----------------------------
# Login form wrapper
# -----------------------------
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Username"})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )


# -----------------------------
# Profile form (base)
# -----------------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["profile_image", "bio","full_name", "organisation", "admin_title", "staff_id", "press_id"]

    widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 dark:border-gray-600 rounded p-2 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-yellow-400'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 dark:border-gray-600 rounded p-2 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-yellow-400',
                'rows': 4,
            }),
            'profile_image': forms.ClearableFileInput(attrs={
                'class': 'border border-gray-300 rounded p-1 text-gray-900 dark:text-white'
            }),
            'admin_title': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 dark:border-gray-600 rounded p-2 text-gray-900 dark:text-white'
            }),
            'staff_id': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 dark:border-gray-600 rounded p-2 text-gray-900 dark:text-white'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 dark:border-gray-600 rounded p-2 text-gray-900 dark:text-white'
            }),
            'press_id': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 dark:border-gray-600 rounded p-2 text-gray-900 dark:text-white'
            }),
        }

# -----------------------------
# Post form
# -----------------------------
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content", "category", "image", "status"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5, "placeholder": "Write your article here..."}),
            "title": forms.TextInput(attrs={"placeholder": "Post title"}),
        }


# -----------------------------
# Comment form
# -----------------------------
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3, "placeholder": "Add your comment here..."}),
        }


# -----------------------------
# Subscriber form
# -----------------------------
class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "Enter your email"}),
        }


# -----------------------------
# Registration form with journalist option
# -----------------------------
ACCOUNT_CHOICES = [
    ("user", "Normal User"),
    ("journalist", "Apply for Journalist"),
]

class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "Email"})
    )
    account_type = forms.ChoiceField(
        choices=ACCOUNT_CHOICES,
        widget=forms.RadioSelect,
        label="Account Type"
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "If applying, briefly explain why"}),
        required=False,
        label="Why do you want to be a journalist?"
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "account_type", "reason"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


# -----------------------------
# User profile form
# -----------------------------
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'profile_image', 'bio', 'is_subscribed']


# -----------------------------
# Journalist profile form
# -----------------------------
class JournalistProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'profile_image', 'bio', 'organisation', 'press_id', 'is_verified']


# -----------------------------
# Admin profile form
# -----------------------------
class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'profile_image', 'bio', 'admin_title', 'staff_id', 'is_verified']
