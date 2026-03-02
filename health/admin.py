from django.contrib import admin

# Manual code

from .models import Appointment, MedicalRecord, Pharmacist, Student, Doctor, UserProfile, Medicine

admin.site.register(Student)
admin.site.register(Doctor)
admin.site.register(Appointment)
admin.site.register(MedicalRecord)
admin.site.register(UserProfile)
admin.site.register(Pharmacist)
admin.site.register(Medicine)
