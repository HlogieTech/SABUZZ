from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Post, Profile, Comment, Subscriber

# -----------------------------
# Signup (legacy) - kept if you use it
# -----------------------------
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")


# -----------------------------
# Login form (wrapper for AuthenticationForm)
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
# Profile form
# -----------------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["role", "profile_image", "is_subscribed", "subscription_date"]


# -----------------------------
# Post form (for creating/editing local posts)
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
# Registration with "apply for journalist" option
# -----------------------------
ACCOUNT_CHOICES = [
    ("user", "Normal User"),
    ("journalist", "Apply for Journalist"),
]


class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"}))
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
