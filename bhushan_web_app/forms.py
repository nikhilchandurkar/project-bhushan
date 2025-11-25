from django import forms
from .models import Product, Category, Address
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field


class ProductForm(forms.ModelForm):
    """Product creation/update form"""
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'stock']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),

        }


class OTPRequestForm(forms.Form):
    """Mobile number entry for OTP"""
    mobile = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10-digit mobile number',
            'pattern': '[0-9]{10}',
        })
    )

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if not mobile.isdigit() or len(mobile) != 10:
            raise forms.ValidationError('Enter a valid 10-digit mobile number')
        return mobile


class OTPVerifyForm(forms.Form):
    """OTP verification form"""
    otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '6-digit OTP',
            'pattern': '[0-9]{6}',
            'autocomplete': 'off',
        })
    )




    def clean_otp(self):
        otp = self.cleaned_data.get('otp')
        if not otp.isdigit() or len(otp) != 6:
            raise forms.ValidationError('Enter a valid 6-digit OTP')
        return otp




class CartAddForm(forms.Form):
    """Add to cart form"""
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )




class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your Name',
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'your.email@example.com',
            'class': 'form-control'
        })
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': '+91 98765 43210',
            'class': 'form-control'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Subject',
            'class': 'form-control'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Your message here...',
            'rows': 5,
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', css_class='mb-3'),
            Field('email', css_class='mb-3'),
            Field('phone', css_class='mb-3'),
            Field('subject', css_class='mb-3'),
            Field('message', css_class='mb-3'),
        )
