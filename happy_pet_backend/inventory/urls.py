# inventory/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('import-product/', views.import_dropship_product, name='import_product'),
    path('products/', views.public_product_list, name='public_products'),
    path('checkout/', views.process_checkout, name='checkout'),
]