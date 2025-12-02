from django import forms
from .models import Product, Category, Address, User
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Row, Column, HTML
from crispy_forms.bootstrap import FormActions


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


class AddressForm(forms.ModelForm):
    """Address creation/update form"""
    class Meta:
        model = Address
        fields = [
            'address_type', 'full_name', 'mobile', 'pincode',
            'address_line1', 'address_line2', 'landmark',
            'city', 'state', 'country', 'is_default'
        ]
        widgets = {
            'address_type': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House No., Building Name'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Road name, Area, Colony'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Landmark (Optional)'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'value': 'India'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Field('address_type', css_class='mb-3'),
                Row(
                    Column(Field('full_name', css_class='mb-3'), css_class='col-md-6'),
                    Column(Field('mobile', css_class='mb-3'), css_class='col-md-6'),
                ),
                Row(
                    Column(Field('pincode', css_class='mb-3'), css_class='col-md-6'),
                    Column(Field('landmark', css_class='mb-3'), css_class='col-md-6'),
                ),
                Field('address_line1', css_class='mb-3'),
                Field('address_line2', css_class='mb-3'),
                Row(
                    Column(Field('city', css_class='mb-3'), css_class='col-md-6'),
                    Column(Field('state', css_class='mb-3'), css_class='col-md-6'),
                ),
                Field('country', css_class='mb-3'),
                Div(
                    Field('is_default', css_class='form-check-input me-2'),
                    HTML('<label class="form-check-label">Set as default address</label>'),
                    css_class='form-check mb-3'
                ),
                FormActions(
                    Submit('submit', 'Save Address', css_class='btn btn-primary'),
                    HTML('<a href="{% url "shop:user-profile" %}" class="btn btn-secondary ms-2">Cancel</a>'),
                ),
                css_class='card-body'
            )
        )

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile and (not mobile.isdigit() or len(mobile) != 10):
            raise forms.ValidationError('Enter a valid 10-digit mobile number')
        return mobile

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode and (not pincode.isdigit() or len(pincode) != 6):
            raise forms.ValidationError('Enter a valid 6-digit pincode')
        return pincode


class UserProfileForm(forms.ModelForm):
    """User profile update form"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'date_of_birth', 'gender']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                HTML('<h5 class="mb-3">Personal Information</h5>'),
                Row(
                    Column(Field('first_name', css_class='mb-3'), css_class='col-md-6'),
                    Column(Field('last_name', css_class='mb-3'), css_class='col-md-6'),
                ),
                Field('email', css_class='mb-3'),
                Row(
                    Column(Field('date_of_birth', css_class='mb-3'), css_class='col-md-6'),
                    Column(Field('gender', css_class='mb-3'), css_class='col-md-6'),
                ),
                FormActions(
                    Submit('submit', 'Update Profile', css_class='btn btn-primary'),
                ),
                css_class='card-body'
            )
        )


class ProfileCompletionForm(forms.ModelForm):
    """Profile completion form for new users"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'date_of_birth', 'gender']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address', 'required': True}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                HTML('<div class="text-center mb-4"><h3>Complete Your Profile</h3><p class="text-muted">Please provide your details to continue</p></div>'),
                Row(
                    Column(Field('first_name', css_class='mb-3'), css_class='col-md-6'),
                    Column(Field('last_name', css_class='mb-3'), css_class='col-md-6'),
                ),
                Field('email', css_class='mb-3'),
                Row(
                    Column(Field('date_of_birth', css_class='mb-3'), css_class='col-md-6'),
                    Column(Field('gender', css_class='mb-3'), css_class='col-md-6'),
                ),
                FormActions(
                    Submit('submit', 'Complete Profile', css_class='btn btn-primary btn-lg w-100'),
                ),
                css_class='card-body p-4'
            )
        )