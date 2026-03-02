# Manual code

from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('download-report/<int:id>/', views.download_medical_report, name='download_report'),
    path('doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('pharmacist/', views.pharmacist_dashboard, name='pharmacist_dashboard'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('logout/', views.logout_view, name='logout'),
    path('update-status/<int:appointment_id>/<str:status>/',
     views.update_appointment_status,
     name='update_status'),
    path('dispense/<int:record_id>/', views.dispense_medicine, name='dispense'),
    path('inventory/', views.view_inventory, name='inventory'),
    path('pharmacist-profile/', views.pharmacist_profile, name='pharmacist_profile'),
    path('student-profile/', views.student_profile, name='student_profile'),
    path('doctor-profile/', views.doctor_profile, name='doctor_profile'),
    path('medical-records/', views.medical_records, name='medical_records'),
    path('doctor/add_record/<int:appointment_id>/',
     views.add_medical_record,
     name='add_medical_record'),
    path('doctor/medical-records/',
      views.doctor_medical_records,
      name='doctor_medical_records'
   ),
]