import datetime
from django import http
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from dashboard.models import studentGroup, FileDetail
from django.contrib.auth.models import User
from authentication.models import UserProfile
import json
import os
import re
from django.conf import settings
import secrets
import string
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponse, Http404, FileResponse
from django.shortcuts import get_object_or_404
import uuid
from django.core.cache import cache


# utility function to generate unique file IDs
def generate_file_id():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))

@login_required(login_url='login')
def index(request):
    return redirect('dashboard')


@login_required(login_url='login')
def dashboard(request):
    if request.user.userprofile.role == 'teacher':
        return render(request, 'teacher_dashboard.html', {'name': request.user.first_name, 'username': request.user.username})
    elif request.user.userprofile.role == 'student':
        return render(request, 'student_dashboard.html', {'name': request.user.first_name, 'username': request.user.username})
    elif request.user.userprofile.role == 'admin':
        return render(request, 'administrator.html', {'username': request.user.username})
    else:
        return http.HttpResponseForbidden("You are not allowed to access this page.")

@login_required(login_url='login')
def upload_file(request):
    if request.method == 'POST' and request.user.userprofile.role == 'teacher':
        uploaded_file = request.FILES['file']
        tempname = uploaded_file.name

        # Validate file type and size (server-side)
        if not uploaded_file.name.lower().endswith('.pdf'):
            return JsonResponse({'success': False, 'error': 'Only PDF files are allowed.'})
        if uploaded_file.size > 50 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File size exceeds 50 MB limit.'})
        if not re.match(r'^[\w\-\. ]+\.pdf$', uploaded_file.name, re.I):
            return JsonResponse({'success': False, 'error': 'Invalid file name.'})
        
        # Generate unique file ID and new file name
        file_id = generate_file_id()
        ext = uploaded_file.name.split('.')[-1]
        new_file_name = f"{file_id}.{ext}"

        # Save file with new name using FileField
        uploaded_file.name = new_file_name
        file = FileDetail.objects.create(
            file_id=file_id,
            file=uploaded_file,
            file_name=tempname,
            file_size=uploaded_file.size,
            uploaded_by=request.user
        )

        return JsonResponse({
            'success': True,
            'fileId': file.file_id,
            'fileName': file.file_name,
            'fileSize': file.file_size,
            'uploadDate': file.file_upload_date.strftime('%Y-%m-%d %H:%M:%S'),
            'expiryDate': file.file_expiry_date.strftime('%Y-%m-%d %H:%M:%S') if file.file_expiry_date else None,
            'sharingPolicy': file.sharing_policy,
            'accessType': file.access_type,
            'sharedGroup': file.shared_group.name if file.shared_group else None,
            'link': f"/pdf/view/{file.file_id}/",  # Changed to viewer URL
        })
    else:
        return http.HttpResponseForbidden("You are not allowed to upload files.")

@login_required(login_url='login')
def group_create(request):
    if request.method == 'POST' and request.user.userprofile.role == 'teacher':
        data = json.loads(request.body)
        group_name = data.get('group_name')
        student_usernames = data.get('usernames', [])

        # create object with usernames available and sort out name thoose are invalid
        valid_students = []
        invalid_students = []
        for username in student_usernames:
            try:
                user = User.objects.get(username=username)
                valid_students.append(user)
            except User.DoesNotExist:
                invalid_students.append(username)
                continue
        
        group = studentGroup.objects.create(name=group_name, created_by=request.user, no_of_students=len(valid_students))
        group.students.set(valid_students)
        group.save()

        # send json response
        return JsonResponse({
            'group_name': group.name,
            'valid_students': [user.username for user in valid_students],
            'invalid_students': invalid_students,
            'no_of_students': group.no_of_students,
            'created_at': group.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    else:
        return http.HttpResponseForbidden("You are not allowed to create groups.")


@login_required(login_url='login')
def fetch_tables(request):
    if request.method == 'POST' and request.user.userprofile.role == 'teacher':
        groups = studentGroup.objects.filter(created_by=request.user).order_by('-created_at')
        files = FileDetail.objects.filter(uploaded_by=request.user).order_by('-file_upload_date')
        group_data = []
        for group in groups:
            group_data.append({
            'groupName': group.name,
            'students': group.no_of_students,
            'createdOn': group.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        file_data = []
        for file in files:
            file_data.append({
                'fileId': file.file_id,
                'fileName': file.file_name,
                'fileSize': file.file_size,
                'uploadDate': file.file_upload_date.strftime('%Y-%m-%d %H:%M:%S'),
                'expiryDate': file.file_expiry_date.strftime('%Y-%m-%d %H:%M:%S') if file.file_expiry_date else None,
                'sharingPolicy': file.sharing_policy,
                'accessType': file.access_type,
                'sharedGroup': file.shared_group.name if file.shared_group else None,
                'link': f"/pdf/view/{file.file_id}/",  # Changed to viewer URL
            })
        return JsonResponse({'groups': group_data, 'files': file_data})
    elif request.method == 'POST' and request.user.userprofile.role == 'student':
        groups = studentGroup.objects.filter(students=request.user).order_by('-created_at')
        files = FileDetail.objects.filter(Q(shared_group__students=request.user) | Q(sharing_policy='public')).order_by('-file_upload_date')
        group_data = []
        for group in groups:
            group_data.append({
            'groupName': group.name,
            'students': group.no_of_students,
            'createdBy': group.created_by.username,
            'createdOn': group.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        file_data = []
        for file in files:
            if(file.file_expiry_date and file.file_expiry_date < timezone.now()):
                continue
            file_data.append({
                'fileId': file.file_id,
                'fileName': file.file_name,
                'fileSize': file.file_size,
                'uploadDate': file.file_upload_date.strftime('%Y-%m-%d %H:%M:%S'),
                'expiryDate': file.file_expiry_date.strftime('%Y-%m-%d %H:%M:%S') if file.file_expiry_date else None,
                'sharingPolicy': file.sharing_policy,
                'accessType': file.access_type,
                'uploadedBy': file.uploaded_by.username,
                'link': f"/pdf/view/{file.file_id}/",  # Changed to viewer URL
            })
        return JsonResponse({'groups': group_data, 'files': file_data})
    else:
        return http.HttpResponseForbidden("You are not allowed to fetch groups.")
    

@login_required(login_url='login')
def update_access(request):
    if request.method == 'PATCH' and request.user.userprofile.role == 'teacher':
        data = json.loads(request.body)
        file_id = data.get('fileId')
        sharing_policy = data.get('sharingPolicy')
        access_type = data.get('accessType')
        shared_group = data.get('sharedGroup')
        expiry_date = data.get('expiryDate')
        
        try:
            file_detail = FileDetail.objects.get(file_id=file_id, uploaded_by=request.user)
            file_detail.sharing_policy = sharing_policy
            file_detail.access_type = access_type.lower()

            if shared_group:
                file_detail.shared_group = studentGroup.objects.get(name=shared_group)
            else:
                file_detail.shared_group = None

            if expiry_date:
                # Parse the expiry date string and make it timezone aware
                expiry_dt = datetime.datetime.strptime(expiry_date, "%Y-%m-%dT%H:%M")
                expiry_dt_aware = timezone.make_aware(expiry_dt)
                file_detail.file_expiry_date = expiry_dt_aware
            else:
                file_detail.file_expiry_date = None
            
            file_detail.save()

            return JsonResponse({
                'success': True,
                'message': 'File access updated successfully.'
            })
        except FileDetail.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'File not found.'}, status=404)
    else:
        return http.HttpResponseForbidden("You are not allowed to update file access.")

@login_required(login_url='login')
def delete_file(request):
    if request.method == 'DELETE' and request.user.userprofile.role == 'teacher':
        data = json.loads(request.body)
        file_id = data.get('fileId')
        try:
            file_detail = FileDetail.objects.get(file_id=file_id, uploaded_by=request.user)
            file_path = file_detail.file.path
            file_detail.delete()
            if os.path.exists(file_path):
                os.remove(file_path)
            return JsonResponse({'success': True, 'message': 'File deleted successfully.'})
        except FileDetail.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'File not found.'}, status=404)
    else:
        return http.HttpResponseForbidden("You are not allowed to delete files.")
    
@login_required(login_url='login')
def delete_group(request):
    if request.method == 'DELETE' and request.user.userprofile.role == 'teacher':
        data = json.loads(request.body)
        group_name = data.get('groupName')
        try:
            group = studentGroup.objects.get(name=group_name, created_by=request.user)
            group.delete()
            return JsonResponse({'success': True, 'message': 'Group deleted successfully.'})
        except studentGroup.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Group not found.'}, status=404)
    else:
        return http.HttpResponseForbidden("You are not allowed to delete groups.")

@login_required(login_url='login')
def pdf_viewer(request, file_id):
    """Render the PDF viewer template with a temporary token"""
    try:
        file_detail = get_object_or_404(FileDetail, file_id=file_id)
        
        if not has_file_access(request.user, file_detail):
            raise Http404("File not found or access denied")

        if file_detail.file_expiry_date and file_detail.file_expiry_date < timezone.now():
            raise Http404("File access expired")

        # Generate temporary token (expires in 30 minutes)
        token = str(uuid.uuid4())
        cache_key = f"pdf_token_{token}"
        cache.set(cache_key, {
            'file_id': file_id,
            'user_id': request.user.id,
            'created_at': timezone.now().isoformat()
        }, timeout=1800)  # 30 minutes expiry
        
        context = {
            'file_id': file_id,
            'file_name': file_detail.file_name,
            'is_download': file_detail.access_type == 'download',
            'token': token,
        }
        return render(request, 'pdf_viewer.html', context)
        
    except FileDetail.DoesNotExist:
        raise Http404("File not found")

@login_required(login_url='login')
def serve_pdf(request, token):
    """Serve PDF using temporary token"""
    cache_key = f"pdf_token_{token}"
    token_data = cache.get(cache_key)
    
    if not token_data:
        raise Http404("Invalid or expired token")
    
    if token_data['user_id'] != request.user.id:
        raise Http404("Unauthorized access")
    
    try:
        file_detail = get_object_or_404(FileDetail, file_id=token_data['file_id'])
        
        # Double-check permissions
        if not has_file_access(request.user, file_detail):
            raise Http404("Access denied")
        
        # Get the actual file path
        file_path = file_detail.file.path
        
        if not os.path.exists(file_path):
            raise Http404("File not found on disk")
        
        # Check if it's a download request (only if access_type allows)
        is_download = request.GET.get('download') == '1'
        if is_download and file_detail.access_type != 'download':
            raise Http404("Download not permitted")
        
        # Serve the file
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf',
            as_attachment=is_download
        )
        
        if is_download:
            response['Content-Disposition'] = f'attachment; filename="{file_detail.file_name}"'
        else:
            response['Content-Disposition'] = f'inline; filename="{file_detail.file_name}"'
            response['Accept-Ranges'] = 'bytes'
        
        return response
        
    except FileDetail.DoesNotExist:
        raise Http404("File not found")

def has_file_access(user, file_detail):
    """Check if user has permission to access the file"""
    # If user is the uploader (teacher)
    if file_detail.uploaded_by == user:
        return True
    
    # If file is public
    if file_detail.sharing_policy == 'public':
        return True

    # If file is shared with user's groups (students)
    if file_detail.sharing_policy == 'shared' and file_detail.shared_group:
        # shared_group is a studentGroup object (OneToOneField)
        return file_detail.shared_group.students.filter(id=user.id).exists()
    
    return False

@login_required(login_url='login')
def search_user(request):
    if request.method == 'GET' and request.user.userprofile.role == 'admin':
        username = request.GET.get('username', '').strip()
        if username:
            user = User.objects.filter(username=username).first()
            if user:
                return JsonResponse({'success': True, 'username': user.username, 'name': user.first_name, 'role': user.userprofile.role})
            else:
                return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
@login_required(login_url='login')
def update_role(request):
    if request.method == 'POST' and request.user.userprofile.role == 'admin':
        data = json.loads(request.body)
        username = data.get('username', '').strip()

        user = User.objects.filter(username=username).first()
        if user:
            user.userprofile.role = 'teacher'
            user.userprofile.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'User not found'}, status=404)