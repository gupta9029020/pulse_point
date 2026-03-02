from django.db import models

# Manual code

from django.contrib.auth.models import User


class Student(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20)
    course = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    profile_photo = models.ImageField(upload_to='student_profiles/', null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    gender = models.CharField(max_length=10, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.username


class Doctor(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    doctor_id = models.CharField(max_length=20)
    specialization = models.CharField(max_length=100)
    qualification = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True)
    profile_photo = models.ImageField(upload_to='doctor_profiles/', null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    gender = models.CharField(max_length=10, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
    

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Completed', 'Completed'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    student_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.doctor} ({self.date})"
    

class MedicalRecord(models.Model):

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    diagnosis = models.TextField()
    notes = models.TextField(blank=True)
    prescription = models.TextField()
    prescribed_quantity = models.IntegerField(default=1)
    dispensed = models.BooleanField(default=False)
    not_available = models.BooleanField(default=False)
    issued_at = models.DateTimeField(auto_now_add=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    pharmacist = models.ForeignKey('Pharmacist', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Record for {self.appointment}"
    

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
        ('pharmacist', 'Pharmacist'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.user.username
    

class Pharmacist(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pharmacist_id = models.CharField(max_length=20)
    phone = models.CharField(max_length=15)
    license_number = models.CharField(max_length=50)
    qualification = models.CharField(max_length=100)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    gender = models.CharField(max_length=10, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.username


class Medicine(models.Model):

    name = models.CharField(max_length=100)
    stock = models.IntegerField()

    def __str__(self):
        return self.name