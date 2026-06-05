from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('',                      views.payment_list,        name='payment_list'),
    path('create/',               views.payment_create,      name='payment_create'),
    path('<int:pk>/',             views.payment_detail,      name='payment_detail'),
    path('<int:pk>/edit/',        views.payment_edit,        name='payment_edit'),
    path('<int:pk>/delete/',      views.payment_delete,      name='payment_confirm_delete'),
    path('<int:pk>/receipt/',     views.payment_receipt_pdf, name='payment_receipt_pdf'),
    path('ajax/course-price/',    views.get_course_price,    name='get_course_price'),
]
