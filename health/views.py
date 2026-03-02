from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .models import UserProfile, Appointment, MedicalRecord, Student, Doctor, Pharmacist, Medicine
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from django.conf import settings
import os


def login_view(request):
    # If already logged in
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')  # Django admin panel
        elif hasattr(request.user,'student'):
            return redirect('student_dashboard')
        elif hasattr(request.user,'doctor'):
            return redirect('doctor_dashboard')
        elif hasattr(request.user,'pharmacist'):
            return redirect('pharmacist_dashboard')
        else:
            return redirect('/')

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request,username=username,password=password)

        if user is not None:
            login(request,user)

            if user.is_superuser:
                return redirect('/admin/')
            elif hasattr(user,'student'):
                return redirect('student_dashboard')
            elif hasattr(user,'doctor'):
                return redirect('doctor_dashboard')
            elif hasattr(user,'pharmacist'):
                return redirect('pharmacist_dashboard')
            else:
                return redirect('/')
        else:
            messages.error(request,"Invalid username or password")

    return render(request,"login.html")


def doctor_dashboard(request):
    doctor = get_object_or_404(Doctor, user=request.user)

    search = request.GET.get('search','')
    date_from = request.GET.get('date_from','')
    date_to = request.GET.get('date_to','')

    # BASE QUERY (LATEST FIRST)
    appointments = Appointment.objects.filter(doctor=doctor).order_by('-created_at')

    # SEARCH
    if search:
        appointments = appointments.filter(
            Q(student__user__username__icontains=search) |
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search) |
            Q(status__icontains=search)
        )

    # DATE FILTER (RAISED DATE)
    if date_from:
        appointments = appointments.filter(created_at__date__gte=date_from)
    if date_to:
        appointments = appointments.filter(created_at__date__lte=date_to)

    return render(request,'doctor_dashboard.html',{
        'appointments':appointments,
        'search':search,
        'date_from':date_from,
        'date_to':date_to
    })


def update_appointment_status(request, appointment_id, status):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.status = status

    # Save Approved Time
    if status == "Approved":
        appointment.approved_at = timezone.now()
    # Save Completed Time
    elif status == "Completed":
        appointment.completed_at = timezone.now()

    appointment.save()
    return redirect('doctor_dashboard')


def admin_dashboard(request):
    appointments = Appointment.objects.all()

    return render(request, 'admin_dashboard.html', {
        'appointments': appointments
    })


def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)

    search = request.GET.get('search','')
    date_from = request.GET.get('date_from','')
    date_to = request.GET.get('date_to','')

    # BASE QUERY (LATEST FIRST)
    appointments = Appointment.objects.filter(student=student).order_by('-created_at')

    # SEARCH
    if search:
        appointments = appointments.filter(
            Q(doctor__user__username__icontains=search) |
            Q(doctor__user__first_name__icontains=search) |
            Q(doctor__user__last_name__icontains=search) |
            Q(status__icontains=search)
        )

    # DATE FILTER (RAISED DATE)
    if date_from:
        appointments = appointments.filter(created_at__date__gte=date_from)
    if date_to:
        appointments = appointments.filter(created_at__date__lte=date_to)

    return render(request,'student_dashboard.html',{
        'appointments':appointments,
        'search':search,
        'date_from':date_from,
        'date_to':date_to
    })


def pharmacist_dashboard(request):
    pharmacist = get_object_or_404(Pharmacist, user=request.user)

    search = request.GET.get('search','')
    date_from = request.GET.get('date_from','')
    date_to = request.GET.get('date_to','')

    # BASE QUERY (LATEST FIRST)
    records = MedicalRecord.objects.all().order_by('-issued_at')

    # SEARCH
    if search:
        records = records.filter(
            Q(appointment__student__user__username__icontains=search) |
            Q(appointment__student__user__first_name__icontains=search) |
            Q(appointment__student__user__last_name__icontains=search) |
            Q(appointment__doctor__user__username__icontains=search) |
            Q(appointment__doctor__user__first_name__icontains=search) |
            Q(appointment__doctor__user__last_name__icontains=search) |
            Q(prescription__icontains=search)
        )

    # DATE FILTER (PRESCRIPTION ISSUE DATE)
    if date_from:
        records = records.filter(issued_at__date__gte=date_from)
    if date_to:
        records = records.filter(issued_at__date__lte=date_to)

    return render(request,'pharmacist_dashboard.html',{
        'records':records,
        'search':search,
        'date_from':date_from,
        'date_to':date_to
    })


def book_appointment(request):
    doctors = Doctor.objects.all()

    if request.method == 'POST':
        doctor_id = request.POST['doctor']
        date = request.POST['date']
        time = request.POST['time']
        note = request.POST.get('note','')

        doctor = Doctor.objects.get(id=doctor_id)
        student = Student.objects.get(user=request.user)

        Appointment.objects.create(
            student=student,
            doctor=doctor,
            date=date,
            time=time,
            student_note=note
        )

        return redirect('student_dashboard')

    return render(request, 'book_appointment.html', {
        'doctors': doctors
    })


def logout_view(request):
    logout(request)
    return redirect('/')


def dispense_medicine(request, record_id):
    record = MedicalRecord.objects.get(id=record_id)
    medicines = Medicine.objects.all()
    error = ""

    if request.method == 'POST':
        med_id = request.POST['medicine']
        qty = int(request.POST['quantity'])
        medicine = Medicine.objects.get(id=med_id)

        #  Medicine not available
        if medicine.stock == 0:
            record.not_available = True
            record.save()
            return redirect('pharmacist_dashboard')

        #  Insufficient stock
        elif medicine.stock < qty:
            record.not_available = True
            record.save()
            return redirect('pharmacist_dashboard')

        #  Medicine available
        else:
            medicine.stock -= qty
            medicine.save()

            pharmacist = Pharmacist.objects.get(user=request.user)
            record.dispensed = True
            record.not_available = False
            record.dispensed_at = timezone.now()
            record.pharmacist = pharmacist
            record.save()

            return redirect('pharmacist_dashboard')

    return render(request,'dispense.html',{'record':record,'medicines':medicines})


def view_inventory(request):
    query = request.GET.get('q','')
    sort = request.GET.get('sort')

    medicines = Medicine.objects.all()

    # Search
    if query:
        medicines = medicines.filter(name__icontains=query)

    # Sorting
    if sort == 'name_asc':
        medicines = medicines.order_by('name')
    elif sort == 'name_desc':
        medicines = medicines.order_by('-name')
    elif sort == 'stock_asc':
        medicines = medicines.order_by('stock')
    elif sort == 'stock_desc':
        medicines = medicines.order_by('-stock')

    return render(request,'inventory.html',{
        'medicines':medicines,
        'query':query,
        'sort':sort
    })


def pharmacist_profile(request):

    pharmacist = Pharmacist.objects.get(user=request.user)

    return render(request,'pharmacist_profile.html',{
        'pharmacist':pharmacist
    })


def student_profile(request):

    student = Student.objects.get(user=request.user)

    return render(request,'student_profile.html',{
        'student': student
    })


def doctor_profile(request):

    doctor = Doctor.objects.get(user=request.user)

    return render(request,'doctor_profile.html',{
        'doctor': doctor
    })


def medical_records(request):
    student = Student.objects.get(user=request.user)

    search = request.GET.get('search','')
    date_from = request.GET.get('date_from','')
    date_to = request.GET.get('date_to','')

    # BASE QUERY (LATEST FIRST)
    records = MedicalRecord.objects.filter(
        appointment__student=student
    ).order_by('-issued_at')

    # SEARCH
    if search:
        records = records.filter(
            Q(appointment__doctor__user__username__icontains=search) |
            Q(appointment__doctor__user__first_name__icontains=search) |
            Q(appointment__doctor__user__last_name__icontains=search) |
            Q(pharmacist__user__username__icontains=search) |
            Q(prescription__icontains=search) |
            Q(diagnosis__icontains=search)
        )

    # DATE FILTER (ISSUED DATE)
    if date_from:
        records = records.filter(issued_at__date__gte=date_from)
    if date_to:
        records = records.filter(issued_at__date__lte=date_to)

    return render(request,'medical_records.html',{
        'records':records,
        'search':search,
        'date_from':date_from,
        'date_to':date_to
    })


def add_medical_record(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":

        diagnosis = request.POST.get("diagnosis")
        medicine = request.POST.get("medicine")
        quantity = request.POST.get("quantity")
        notes = request.POST.get("notes")

        MedicalRecord.objects.create(
            appointment=appointment,
            diagnosis=diagnosis,
            prescription=medicine,
            prescribed_quantity=quantity,
            notes=notes
        )

        appointment.status = "Completed"
        appointment.completed_at = timezone.now()
        appointment.save(update_fields=["status", "completed_at"])

        return redirect("doctor_dashboard")

    return render(request, "add_medical_record.html", {
        "appointment": appointment
    })


def doctor_medical_records(request):
    doctor = Doctor.objects.get(user=request.user)

    search = request.GET.get('search','')
    date_from = request.GET.get('date_from','')
    date_to = request.GET.get('date_to','')

    # BASE QUERY (LATEST FIRST)
    records = MedicalRecord.objects.filter(
        appointment__doctor=doctor
    ).order_by('-issued_at')

    # SEARCH
    if search:
        records = records.filter(
            Q(appointment__student__user__username__icontains=search) |
            Q(appointment__student__user__first_name__icontains=search) |
            Q(appointment__student__user__last_name__icontains=search) |
            Q(prescription__icontains=search) |
            Q(diagnosis__icontains=search)
        )

    # DATE FILTER (PRESCRIPTION ISSUE DATE)
    if date_from:
        records = records.filter(issued_at__date__gte=date_from)
    if date_to:
        records = records.filter(issued_at__date__lte=date_to)

    return render(request,'doctor_medical_records.html',{
        'records':records,
        'search':search,
        'date_from':date_from,
        'date_to':date_to
    })


def error_404(request, exception):
    return render(request, '404.html', status=404)


def download_medical_report(request, id):
    record = MedicalRecord.objects.get(id=id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="medical_report.pdf"'
    p = canvas.Canvas(response, pagesize=A4)

    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    styleN.fontName = 'Helvetica'
    styleN.fontSize = 12
    styleN.wordWrap = 'CJK'

    # ===== PAGE BORDER =====
    p.rect(30, 30, 535, 780)

    # ===== HEADER =====
    logo_path = os.path.join(settings.MEDIA_ROOT, "logo/college_logo.png")
    try:
        p.drawImage(logo_path, 55, 715, width=110, height=110, preserveAspectRatio=True)
    except:
        pass

    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(300, 785, "SANGAM UNIVERSITY")
    p.setFont("Helvetica-Bold", 13)
    p.drawCentredString(300, 770, "BHILWARA - 311001")
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(300, 745, "MEDICAL TEST REPORT")

    p.line(210, 740, 390, 740)
    p.line(40, 730, 550, 730)
    p.line(40, 726, 550, 726)

    # ===== REPORT ID =====
    p.setFont("Helvetica", 11)
    p.drawRightString(540, 705, f"Report ID: MR-{record.id:04d}")

    # ===== STUDENT DETAILS =====
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, 660, "Basic Details")

    student_table = [
        ["Student Name", record.appointment.student.user.get_full_name()],
        ["Doctor Name", record.appointment.doctor.user.get_full_name()],
        ["Date", record.issued_at.strftime('%d %B %Y')]
    ]

    table = Table(student_table, colWidths=[170, 330])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, HexColor("#888888")),
        ('BACKGROUND', (0, 0), (0, -1), HexColor("#EEEEEE")),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))

    table_width, table_height = table.wrap(480, 200)
    table.drawOn(p, 40, 650 - table_height)

    # ===== MEDICAL DETAILS =====
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, 550, "Medical Details")

    medical_table = [
        ["Diagnosis", Paragraph(record.diagnosis, styleN)],
        ["Medicine", Paragraph(record.prescription, styleN)],
        ["Quantity", str(record.prescribed_quantity) + " units"],
        ["Doctor Notes", Paragraph(record.notes, styleN)]
    ]

    table2 = Table(medical_table, colWidths=[170, 330])
    table2.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, HexColor("#888888")),
        ('BACKGROUND', (0, 0), (0, -1), HexColor("#EEEEEE")),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))

    table2_width, table2_height = table2.wrap(480, 200)
    table2.drawOn(p, 40, 595 - table_height - table2_height)

    # ===== SIGNATURE =====
    p.line(380, 170, 530, 170)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(410, 150, "Doctor Signature")

    # ===== FOOTER =====
    p.setFont("Helvetica", 10)
    p.drawCentredString(300, 70, "Generated by College Health Management System")
    p.drawCentredString(300, 55, "This is a computer generated report")

    p.showPage()
    p.save()
    return response