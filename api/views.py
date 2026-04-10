from django.shortcuts import render
from django.http import JsonResponse
from students.models import Student
from .serializers import StudentSerializer
from .models import CustomUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.conf import settings
import uuid
from .models import CustomUser, PendingUser
from django.shortcuts import redirect

@api_view(['GET','POST'])
def studentsView(request):
    if request.method == 'GET':
        students = Student.objects.all()
        serializer = StudentSerializer(students, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def studentDetailView(request, pk):
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = StudentSerializer(student)
        return Response(serializer.data, status = status.HTTP_200_OK)




@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    try:
        user_obj = CustomUser.objects.get(username__iexact=username)
        user = authenticate(username=user_obj.username, password=password)
    except CustomUser.DoesNotExist:
        user = None

    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def rmd_list(request):
    rmds = CustomUser.objects.filter(is_rmd=True)
    data = [{'id': rmd.id, 'name': f"{rmd.first_name} {rmd.last_name}", 'email': rmd.email} for rmd in rmds]
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
def register_request(request):
    first_name = request.data.get('firstName')
    last_name = request.data.get('lastName')
    email = request.data.get('email')
    hgi_code = request.data.get('hgiCode')
    upline_rmd_id = request.data.get('uplineRMD')

    # Check if a pending request already exists for this email
    if PendingUser.objects.filter(email__iexact=email).exists():
        return Response({'error': 'You already have a pending request. Please wait for your RMD to approve it.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if a user with this email already has an account
    if CustomUser.objects.filter(email__iexact=email).exists():
        return Response({'error': 'An account with this email already exists. Please log in.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if HGI code is already in use by a pending user
    if PendingUser.objects.filter(hgi_code=hgi_code).exists():
        return Response({'error': 'This HGI code is already associated with a pending request.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if HGI code is already in use by an existing user
    if CustomUser.objects.filter(hgi_code=hgi_code).exists():
        return Response({'error': 'This HGI code is already in use. Please check your HGI code and try again.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        rmd = CustomUser.objects.get(id=int(upline_rmd_id))
    except (CustomUser.DoesNotExist, ValueError, TypeError):
        return Response({'error': 'RMD not found'}, status=status.HTTP_400_BAD_REQUEST)

    token = str(uuid.uuid4())

    pending_user = PendingUser.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        hgi_code=hgi_code,
        upline_rmd=rmd,
        token=token
    )

    approve_url = f"http://localhost:8000/api/v1/approve/{token}/"
    deny_url = f"http://localhost:8000/api/v1/deny/{token}/"

    send_mail(
        subject="New Member Approval Request",
        message=f"A new member has requested to join.\n\nName: {first_name} {last_name}\nEmail: {email}\nHGI Code: {hgi_code}\n\nClick Approve or Deny below:\n\nApprove: {approve_url}\nDeny: {deny_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[rmd.email],
    )

    return Response({'message': 'Request sent to RMD for approval'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def approve_request(request, token):
    try:
        pending_user = PendingUser.objects.get(token=token)
    except PendingUser.DoesNotExist:
        return redirect("http://localhost:5173/denied")

    # Mark as approved so deny link becomes invalid
    pending_user.is_approved = True
    pending_user.save()

    setup_url = f"http://localhost:5173/setup-account/{token}"
    send_mail(
        subject="Your account has been approved!",
        message=f"Hi {pending_user.first_name},\n\nYour account has been approved! Click the link below to create your username and password:\n\n{setup_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[pending_user.email],
    )

    return redirect("http://localhost:5173/approved")



@api_view(['GET'])
def deny_request(request, token):
    try:
        pending_user = PendingUser.objects.get(token=token, is_approved=False)
    except PendingUser.DoesNotExist:
        return redirect("http://localhost:5173/approved")

    send_mail(
        subject="Your account request has been denied",
        message=f"Hi {pending_user.first_name},\n\nUnfortunately your account request has been denied. Please contact your RMD for more information.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[pending_user.email],
    )

    pending_user.delete()

    return redirect("http://localhost:5173/denied")

@api_view(['GET'])
def verify_token(request, token):
    try:
        pending_user = PendingUser.objects.get(token=token)
        return Response({'valid': True, 'email': pending_user.email})
    except PendingUser.DoesNotExist:
        return Response({'valid': False})

@api_view(['POST'])
def setup_account(request):
    token = request.data.get('token')
    username = request.data.get('username')
    password = request.data.get('password')

    try:
        pending_user = PendingUser.objects.get(token=token)
    except PendingUser.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if username already exists
    if CustomUser.objects.filter(username__iexact=username).exists():
        return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
    
    if CustomUser.objects.filter(email__iexact=pending_user.email).exists():
        return Response({'error': 'An account with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    # Create the actual user
    user = CustomUser.objects.create_user(
        username=username,
        password=password,
        email=pending_user.email,
        first_name=pending_user.first_name,
        last_name=pending_user.last_name,
        hgi_code=pending_user.hgi_code,
        upline_rmd=pending_user.upline_rmd,
        role='New Member'
    )

    # Delete the pending user now that account is created
    pending_user.delete()

    return Response({'message': 'Account created successfully'}, status=status.HTTP_200_OK)
@api_view(['POST'])
def forgot_password(request):
    email = request.data.get('email')

    try:
        user = CustomUser.objects.get(email__iexact=email)
    except CustomUser.DoesNotExist:
        return Response({'error': 'No account found with this email.'}, status=status.HTTP_400_BAD_REQUEST)

    token = str(uuid.uuid4())
    user.password_reset_token = token
    user.save()

    reset_url = f"http://localhost:5173/reset-password/{token}"
    send_mail(
        subject="Password Reset Request",
        message=f"Hi {user.first_name},\n\nClick the link below to reset your password:\n\n{reset_url}\n\nIf you did not request this, please ignore this email.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

    return Response({'message': 'Password reset email sent!'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def verify_reset_token(request, token):
    try:
        user = CustomUser.objects.get(password_reset_token=token)
        return Response({'valid': True})
    except CustomUser.DoesNotExist:
        return Response({'valid': False})


@api_view(['POST'])
def reset_password(request):
    token = request.data.get('token')
    password = request.data.get('password')

    try:
        user = CustomUser.objects.get(password_reset_token=token)
    except CustomUser.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(password)
    user.password_reset_token = None
    user.save()

    return Response({'message': 'Password reset successfully!'}, status=status.HTTP_200_OK)