from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from .models import PatientProfile, DoctorProfile, User
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

@csrf_protect
def simple_register(request):
    """Simple registration view for easy user signup"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', 'PATIENT')
        
        # Basic validation
        errors = []
        
        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        
        if not first_name or not last_name:
            errors.append('First name and last name are required.')
        
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already exists.')
        
        if not phone:
            errors.append('Phone number is required.')
        
        if not password1:
            errors.append('Password is required.')
        elif len(password1) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        if password1 != password2:
            errors.append('Passwords do not match.')
        
        # Role-specific validation
        if role == 'DOCTOR':
            specialization = request.POST.get('specialization', '').strip()
            license_number = request.POST.get('license_number', '').strip()
            experience = request.POST.get('experience', '').strip()
            
            if not specialization:
                errors.append('Medical specialization is required for doctors.')
            if not license_number:
                errors.append('Medical license number is required for doctors.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'registration/simple_register.html', {
                'today': timezone.now()
            })
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            
            if role == 'DOCTOR':
                # Create doctor profile
                DoctorProfile.objects.create(
                    user=user,
                    specialization=request.POST.get('specialization', ''),
                    license_number=request.POST.get('license_number', ''),
                    experience=request.POST.get('experience', 0),
                    phone=phone,
                    is_verified=False  # Admin will verify
                )
                messages.success(request, 
                    f'Dr. {first_name} {last_name}, your account has been created! '
                    'Please wait for admin verification before accessing doctor features.'
                )
            else:
                # Create patient profile
                PatientProfile.objects.create(
                    user=user,
                    phone=phone,
                    date_of_birth=request.POST.get('date_of_birth', None),
                    gender=request.POST.get('gender', ''),
                    blood_group=request.POST.get('blood_group', ''),
                    emergency_contact_name='',
                    emergency_contact_phone='',
                    medical_history='',
                    allergies=''
                )
                messages.success(request, 
                    f'Welcome {first_name}! Your account has been created successfully. '
                    'You can now book appointments and manage your health records.'
                )
            
            # Auto-login user
            login(request, user)
            
            # Redirect to appropriate dashboard
            if role == 'DOCTOR':
                return redirect('appointments:doctor_dashboard')
            else:
                return redirect('dashboard:home')
                
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'registration/simple_register.html', {
                'today': timezone.now()
            })
    
    return render(request, 'registration/simple_register.html', {
        'today': timezone.now()
    })

@login_required
def quick_profile_setup(request):
    """Quick profile setup after registration"""
    user = request.user
    
    if request.method == 'POST':
        if user.role == 'DOCTOR':
            profile = user.doctorprofile
            profile.phone = request.POST.get('phone', profile.phone)
            profile.specialization = request.POST.get('specialization', profile.specialization)
            profile.experience = request.POST.get('experience', profile.experience)
            profile.save()
            
            messages.success(request, 'Your doctor profile has been updated!')
            return redirect('appointments:doctor_dashboard')
            
        elif user.role == 'PATIENT':
            profile = user.patientprofile
            profile.phone = request.POST.get('phone', profile.phone)
            profile.date_of_birth = request.POST.get('date_of_birth', profile.date_of_birth)
            profile.gender = request.POST.get('gender', profile.gender)
            profile.blood_group = request.POST.get('blood_group', profile.blood_group)
            profile.emergency_contact_name = request.POST.get('emergency_contact_name', profile.emergency_contact_name)
            profile.emergency_contact_phone = request.POST.get('emergency_contact_phone', profile.emergency_contact_phone)
            profile.save()
            
            messages.success(request, 'Your patient profile has been updated!')
            return redirect('dashboard:home')
    
    return render(request, 'registration/quick_profile_setup.html')
