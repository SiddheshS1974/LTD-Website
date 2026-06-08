from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from students.models import Student
from .serializers import StudentSerializer, CustomUserSerializer, ValidHGICodeSerializer, ProtectedFileSerializer, RMDProfileSerializer
from .models import CustomUser, PendingUser, ValidHGICode, ProtectedFile, RMDProfile
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.conf import settings
import uuid
import re
import io
import json

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
        update_last_login(None, user)
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'is_staff': user.is_staff,
            'role': user.role,
            'is_rmd_member': user.is_rmd_member,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
        })
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def rmd_list(request):
    rmds = CustomUser.objects.filter(Q(is_rmd=True) | Q(is_staff=True) | Q(role='Admin'))
    data = []
    for rmd in rmds:
        name = f"{rmd.first_name} {rmd.last_name}".strip() or rmd.username
        data.append({'id': rmd.id, 'name': name, 'email': rmd.email})
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

    # Check if HGI code exists in the list of valid codes
    if ValidHGICode.objects.exists() and not ValidHGICode.objects.filter(code=hgi_code).exists():
        return Response({'error': 'This HGI code is not recognised. Please check your code and try again.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if HGI code is already in use by a pending user
    if PendingUser.objects.filter(hgi_code=hgi_code).exists():
        return Response({'error': 'This HGI code is already associated with a pending request.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if HGI code is already in use by an existing user
    if CustomUser.objects.filter(hgi_code=hgi_code).exists():
        return Response({'error': 'This HGI code is already in use. Please check your HGI code and try again.'}, status=status.HTTP_400_BAD_REQUEST)

    # Route to the upline RMD if they have direct access enabled.
    # Try HGI code match first, then fall back to name match against RMDProfile.
    rmd = None
    try:
        valid_code = ValidHGICode.objects.get(code=hgi_code)

        upline_code = valid_code.upline_rmd_hgi_code.strip()
        if upline_code:
            rmd_profile = RMDProfile.objects.filter(
                hgi_code=upline_code,
                user__isnull=False,
                user__can_receive_requests=True,
            ).exclude(user__email='').select_related('user').first()
            if rmd_profile:
                rmd = rmd_profile.user

        if not rmd:
            upline_name = valid_code.upline_rmd_name.strip().lower()
            if upline_name:
                for profile in RMDProfile.objects.filter(
                    user__isnull=False,
                    user__can_receive_requests=True,
                ).exclude(user__email='').select_related('user'):
                    profile_name = f"{profile.first_name} {profile.last_name}".strip().lower()
                    if profile_name == upline_name:
                        rmd = profile.user
                        break

    except ValidHGICode.DoesNotExist:
        pass

    if not rmd:
        admins = list(CustomUser.objects.filter(is_staff=True).exclude(email=''))
        if not admins:
            return Response({'error': 'No admin account found to process this request. Please contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        rmd = admins[0]
        recipient_emails = [a.email for a in admins]
    else:
        recipient_emails = [rmd.email]

    token = str(uuid.uuid4())
    approve_url = f"{settings.BACKEND_URL}/api/v1/approve/{token}/"
    deny_url = f"{settings.BACKEND_URL}/api/v1/deny/{token}/"

    # Send email FIRST — only create the pending record if it succeeds
    try:
        send_mail(
            subject="New Member Approval Request",
            message=f"A new member has requested to join.\n\nName: {first_name} {last_name}\nEmail: {email}\nHGI Code: {hgi_code}\n\nClick Approve or Deny below:\n\nApprove: {approve_url}\nDeny: {deny_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
        )
    except Exception as e:
        print(f"Email error: {e}")
        return Response({'error': 'Failed to send approval email. Please try again or contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    PendingUser.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        hgi_code=hgi_code,
        upline_rmd=rmd,
        token=token
    )

    return Response({'message': 'Request sent to RMD for approval'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def approve_request(request, token):
    try:
        pending_user = PendingUser.objects.get(token=token)
    except PendingUser.DoesNotExist:
        return redirect(f"{settings.FRONTEND_URL}/denied")

    # Mark as approved so deny link becomes invalid
    pending_user.is_approved = True
    pending_user.save()

    setup_url = f"{settings.FRONTEND_URL}/setup-account/{token}"
    send_mail(
        subject="Your account has been approved!",
        message=f"Hi {pending_user.first_name},\n\nYour account has been approved! Click the link below to create your username and password:\n\n{setup_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[pending_user.email],
    )

    return redirect(f"{settings.FRONTEND_URL}/approved")



@api_view(['GET'])
def deny_request(request, token):
    try:
        pending_user = PendingUser.objects.get(token=token, is_approved=False)
    except PendingUser.DoesNotExist:
        return redirect(f"{settings.FRONTEND_URL}/approved")

    send_mail(
        subject="Your account request has been denied",
        message=f"Hi {pending_user.first_name},\n\nUnfortunately your account request has been denied. Please contact your RMD for more information.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[pending_user.email],
    )

    pending_user.delete()

    return redirect(f"{settings.FRONTEND_URL}/denied")

@api_view(['GET'])
def verify_token(request, token):
    try:
        pending_user = PendingUser.objects.get(token=token)
        return Response({'valid': True, 'email': pending_user.email})
    except PendingUser.DoesNotExist:
        return Response({'valid': False})

@api_view(['GET'])
def check_username(request):
    username = request.query_params.get('username', '').strip()
    if not username:
        return Response({'available': False})
    taken = CustomUser.objects.filter(username__iexact=username).exists()
    return Response({'available': not taken})


@api_view(['POST'])
def setup_account(request):
    token = request.data.get('token')
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    try:
        pending_user = PendingUser.objects.get(token=token)
    except PendingUser.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return Response({'error': 'Username must be 3–20 characters: letters, numbers, and underscores only.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 8 or not re.search(r'[a-zA-Z]', password) or not re.search(r'[0-9]', password):
        return Response({'error': 'Password must be at least 8 characters and include at least one letter and one number.'}, status=status.HTTP_400_BAD_REQUEST)

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

    # Link to RMDProfile if their HGI code matches an unclaimed profile
    try:
        rmd_profile = RMDProfile.objects.get(hgi_code=pending_user.hgi_code, user__isnull=True)
        user.is_rmd_member = True
        user.save()
        rmd_profile.user = user
        rmd_profile.save()
    except RMDProfile.DoesNotExist:
        pass

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

    reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"
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


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def user_list(request):
    if not (request.user.is_staff or request.user.role == 'Admin'):
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    users = CustomUser.objects.all().order_by('date_joined')
    serializer = CustomUserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_user(request, pk):
    if not (request.user.is_staff or request.user.role == 'Admin'):
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        user = CustomUser.objects.get(pk=pk)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    if user == request.user:
        return Response({'error': 'Cannot delete your own account.'}, status=status.HTTP_400_BAD_REQUEST)
    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def rmd_profiles_list(request):
    if not (request.user.is_staff or request.user.role == 'Admin'):
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        profiles = RMDProfile.objects.all().select_related('user').order_by('last_name', 'first_name')
        serializer = RMDProfileSerializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()
    hgi_code = request.data.get('hgi_code', '').strip()

    if not all([first_name, last_name, hgi_code]):
        return Response({'error': 'First name, last name, and HGI code are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if RMDProfile.objects.filter(hgi_code=hgi_code).exists():
        return Response({'error': 'An RMD with this HGI code already exists in the list.'}, status=status.HTTP_400_BAD_REQUEST)

    # If a CustomUser with this HGI code already exists, link them immediately
    user = CustomUser.objects.filter(hgi_code=hgi_code).first()
    if user:
        user.is_rmd_member = True
        user.save()

    profile = RMDProfile.objects.create(
        first_name=first_name,
        last_name=last_name,
        hgi_code=hgi_code,
        user=user,
    )
    serializer = RMDProfileSerializer(profile)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def rmd_profile_detail(request, pk):
    if not (request.user.is_staff or request.user.role == 'Admin'):
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        profile = RMDProfile.objects.get(pk=pk)
    except RMDProfile.DoesNotExist:
        return Response({'error': 'RMD profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    # Unlink the associated user's is_rmd_member flag before deleting
    if profile.user:
        profile.user.is_rmd_member = False
        profile.user.save()
    profile.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def toggle_active(request, pk):
    if not (request.user.is_staff or request.user.role == 'Admin'):
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        user = CustomUser.objects.get(pk=pk)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    if user == request.user:
        return Response({'error': 'Cannot deactivate your own account.'}, status=status.HTTP_400_BAD_REQUEST)
    user.is_active = not user.is_active
    user.save()
    return Response({'is_active': user.is_active}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def toggle_requests(request, pk):
    if not (request.user.is_staff or request.user.role == 'Admin'):
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        user = CustomUser.objects.get(pk=pk)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    user.can_receive_requests = not user.can_receive_requests
    user.save()
    return Response({'can_receive_requests': user.can_receive_requests}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def change_user_role(request, pk):
    if not (request.user.is_staff or request.user.role == 'Admin'):
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        user = CustomUser.objects.get(pk=pk)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    role = request.data.get('role')
    valid_roles = [r[0] for r in CustomUser.ROLE_CHOICES]
    if role not in valid_roles:
        return Response({'error': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)
    user.role = role
    user.is_rmd = role == 'RMD'
    user.is_staff = role == 'Admin'
    user.save()
    return Response({'message': 'Role updated.'}, status=status.HTTP_200_OK)


_HGI_PAGE_SIZE = 100

@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def hgi_codes_list(request):
    if not (request.user.is_staff or request.user.role == 'Admin'):
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'GET':
        search = request.query_params.get('search', '').strip()
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError:
            page = 1
        qs = ValidHGICode.objects.order_by('code')
        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        total = qs.count()
        num_pages = max(1, (total + _HGI_PAGE_SIZE - 1) // _HGI_PAGE_SIZE)
        page = min(page, num_pages)
        start = (page - 1) * _HGI_PAGE_SIZE
        serializer = ValidHGICodeSerializer(qs[start:start + _HGI_PAGE_SIZE], many=True)
        claimed_count = ValidHGICode.objects.filter(
            code__in=CustomUser.objects.exclude(hgi_code__isnull=True).exclude(hgi_code='').values('hgi_code')
        ).count()
        return Response({
            'count': total,
            'page': page,
            'num_pages': num_pages,
            'claimed_count': claimed_count,
            'results': serializer.data,
        }, status=status.HTTP_200_OK)
    serializer = ValidHGICodeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def rmd_member_list(request):
    if not request.user.is_rmd_member and not (request.user.is_staff or request.user.role == 'Admin'):
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    members = CustomUser.objects.filter(upline_rmd=request.user).order_by('date_joined')
    serializer = CustomUserSerializer(members, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def file_list(request):
    files = ProtectedFile.objects.all().order_by('title')
    serializer = ProtectedFileSerializer(files, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


_GOOGLE_EXPORT_MAP = {
    'application/vnd.google-apps.presentation': 'application/pdf',
    'application/vnd.google-apps.document': 'application/pdf',
    'application/vnd.google-apps.spreadsheet': 'application/pdf',
}

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def file_proxy(request, pk):
    try:
        protected_file = ProtectedFile.objects.get(pk=pk)
    except ProtectedFile.DoesNotExist:
        return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)

    sa_json = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_JSON', '')
    if not sa_json:
        return Response({'error': 'File service not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload

        creds = service_account.Credentials.from_service_account_info(
            json.loads(sa_json),
            scopes=['https://www.googleapis.com/auth/drive.readonly'],
        )
        service = build('drive', 'v3', credentials=creds)

        file_meta = service.files().get(
            fileId=protected_file.drive_file_id, fields='mimeType,name'
        ).execute()
        mime_type = file_meta['mimeType']

        buffer = io.BytesIO()
        if mime_type in _GOOGLE_EXPORT_MAP:
            export_mime = _GOOGLE_EXPORT_MAP[mime_type]
            req = service.files().export_media(
                fileId=protected_file.drive_file_id, mimeType=export_mime
            )
            response_mime = export_mime
        else:
            req = service.files().get_media(fileId=protected_file.drive_file_id)
            response_mime = mime_type

        downloader = MediaIoBaseDownload(buffer, req)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        buffer.seek(0)
        http_response = HttpResponse(buffer.read(), content_type=response_mime)
        http_response['Content-Disposition'] = f'inline; filename="{protected_file.title}"'
        return http_response

    except Exception as e:
        print(f"Drive proxy error: {e}")
        return Response({'error': 'Failed to retrieve file.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def hgi_code_detail(request, pk):
    if not (request.user.is_staff or request.user.role == 'Admin'):
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        code = ValidHGICode.objects.get(pk=pk)
    except ValidHGICode.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        code.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = ValidHGICodeSerializer(code, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)