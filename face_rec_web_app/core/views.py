from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
from .camera import VideoCamera
from .models import Person, FaceImage
from django.core.files.base import ContentFile
import base64

camera = None

def get_camera():
    global camera
    if camera is None:
        camera = VideoCamera()
    return camera

def release_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None

def home(request):
    release_camera() # Ensure camera is off so browser can use it if needed later
    return render(request, 'core/home.html')

def register_view(request):
    release_camera() # Release server camera so browser can use webcam
    
    if request.method == 'POST':
        name = request.POST.get('name')
        class_name = request.POST.get('class_name')
        age = request.POST.get('age')
        department = request.POST.get('department')
        image_data = request.POST.get('image_data')
        image_file = request.FILES.get('image')

        if name and (image_data or image_file):
            person, created = Person.objects.get_or_create(name=name)
            person.class_name = class_name
            person.age = age if age else None
            person.department = department
            person.save()
            
            if image_data:
                # Handle Base64 captured image
                format, imgstr = image_data.split(';base64,') 
                ext = format.split('/')[-1] 
                data = ContentFile(base64.b64decode(imgstr), name=f'{name}_capture.{ext}')
                face_image = FaceImage(person=person, image=data)
            else:
                # Handle standard file upload
                face_image = FaceImage(person=person, image=image_file)
            
            face_image.save()
            return redirect('register') # Redirect to same page (refresh)

    return render(request, 'core/register.html')

from django.http import JsonResponse
def get_recognized_faces(request):
    cam = get_camera()
    return JsonResponse({'faces': cam.current_recognized_faces})

def scan_view(request):
    # Camera will be initialized by video_feed when the image tag loads
    return render(request, 'core/scan.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def video_feed(request):
    return StreamingHttpResponse(gen(get_camera()),
                    content_type='multipart/x-mixed-replace; boundary=frame')

def gallery_view(request):
    release_camera()
    images = FaceImage.objects.all().order_by('-person__created_at')
    return render(request, 'core/gallery.html', {'images': images})

def delete_face(request, face_id):
    if request.method == 'POST':
        try:
            face = FaceImage.objects.get(id=face_id)
            # Delete the file from filesystem
            if face.image:
                face.image.delete(save=False)
            # Delete the database record
            face.delete()
        except FaceImage.DoesNotExist:
            pass
    return redirect('gallery')

def edit_face(request, face_id):
    try:
        face = FaceImage.objects.get(id=face_id)
        person = face.person
    except FaceImage.DoesNotExist:
        return redirect('gallery')

    if request.method == 'POST':
        name = request.POST.get('name')
        class_name = request.POST.get('class_name')
        age = request.POST.get('age')
        department = request.POST.get('department')
        image_data = request.POST.get('image_data')
        image_file = request.FILES.get('image')

        if name:
            person.name = name
            person.class_name = class_name
            person.age = age if age else None
            person.department = department
            person.save()

            if image_data or image_file:
                # If updating image, we need to re-generate encoding
                # We can do this by setting encoding to None and saving, 
                # relying on the model's save method logic.
                
                if image_data:
                    # Handle Base64 captured image
                    format, imgstr = image_data.split(';base64,') 
                    ext = format.split('/')[-1] 
                    data = ContentFile(base64.b64decode(imgstr), name=f'{name}_capture.{ext}')
                    
                    # Delete old image file
                    if face.image:
                        face.image.delete(save=False)
                        
                    face.image = data
                else:
                    # Handle standard file upload
                    # Delete old image file
                    if face.image:
                        face.image.delete(save=False)
                        
                    face.image = image_file
                
                face.encoding = None # Force re-encoding
                face.save()
            
            return redirect('gallery')

    return render(request, 'core/edit_face.html', {'face': face, 'person': person})
