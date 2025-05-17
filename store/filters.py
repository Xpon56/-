import django_filters as filters
from django import forms
from django.db.models import Q
from .models import Product, Category, Brand, ProductAttribute

class ProductFilter(filters.FilterSet):
    price = filters.RangeFilter(
        field_name='price',
        label="Цена",
        widget=filters.widgets.RangeWidget(
            attrs={
                'class': 'form-control',
                'placeholder': 'От - До',
                'type': 'number',
                'step': '0.01'
            }
        )
    )
    
    category = filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Категории"
    )

    search = filters.CharFilter(
        method='filter_search',
        label='Поиск',
        widget=forms.TextInput(attrs={'placeholder': 'Поиск товаров...'})
    )

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(brand__name__icontains=value)
        )

    class Meta:
        model = Product
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамические атрибуты
        attributes = ProductAttribute.objects.all()
        for attr in attributes:
            if attr.filter_type == 'range':
                self.filters[f'attr_{attr.slug}'] = filters.RangeFilter(
                    field_name=f'attributes__value',
                    label=attr.name,
                    widget=filters.widgets.RangeWidget(attrs={'step': '0.1'})
                )
            elif attr.filter_type == 'checkbox':
                self.filters[f'attr_{attr.slug}'] = filters.MultipleChoiceFilter(
                    field_name=f'attributes__value',
                    choices=[(v.value, v.value) for v in attr.values.all()],
                    label=attr.name,
                    widget=forms.CheckboxSelectMultiple
                )
            elif attr.filter_type == 'bool':
                self.filters[f'attr_{attr.slug}'] = filters.BooleanFilter(
                    field_name=f'attributes__value',
                    label=attr.name,
                    widget=forms.CheckboxInput
                )