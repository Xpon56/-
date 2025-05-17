from django import forms
from .models import ContactRequest, CartItem,  CustomUser
from django.contrib.auth.forms import AuthenticationForm
from .models import ProductRating, ProductAttribute, ProductAttributeValue
from .models import Product

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш email'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Тема сообщения'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ваше сообщение...'
            }),
        }

class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            })
        }

class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })
    )
    agreement = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Я согласен на обработку персональных данных'
    )
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Хэширование пароля
        if commit:
            user.save()
        return user

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone']
        labels = {
            'username': 'Логин',
            'email': 'Электронная почта',
            'phone': 'Номер телефона'
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Придумайте логин'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@mail.ru'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '79991234567',  # Убрать инлайновые стили
            }),
        }

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Логин или Email',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Логин',
            'email': 'Электронная почта',
            'phone': 'Телефон'
        }

class RatingForm(forms.ModelForm):
    class Meta:
        model = ProductRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=ProductRating.RATING_CHOICES, attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DynamicFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
        
        if category:
            attributes = ProductAttribute.objects.filter(category=category)
            for attr in attributes:
                if attr.filter_type == 'range':
                    self.fields[attr.slug] = forms.CharField(
                        widget=forms.TextInput(attrs={'class': 'range-picker'})
                    )
                elif attr.filter_type == 'checkbox':
                    choices = [(v, v) for v in ProductAttributeValue.objects.filter(
                        attribute=attr).values_list('value', flat=True).distinct()]
                    self.fields[attr.slug] = forms.MultipleChoiceField(
                        choices=choices,
                        widget=forms.CheckboxSelectMultiple,
                        required=False
                    )

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название товара'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'brand': forms.Select(attrs={
                'class': 'form-select'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Цена в рублях'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': '0-100%'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Подробное описание товара...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Автоматически заполнится при сохранении'
            })
        }
        labels = {
            'slug': 'URL-адрес товара (необязательно)'
        }