from django.db import models
import face_recognition
import numpy as np
import pickle

class Person(models.Model):
    name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=50, blank=True)
    age = models.IntegerField(null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class FaceImage(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='faces/')
    encoding = models.BinaryField(null=True, blank=True) # Store numpy array as bytes

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.encoding:
            self.generate_encoding()

    def generate_encoding(self):
        try:
            # Load image using face_recognition
            image = face_recognition.load_image_file(self.image.path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                # Store the first encoding found
                self.encoding = pickle.dumps(encodings[0])
                self.save(update_fields=['encoding'])
        except Exception as e:
            print(f"Error generating encoding for {self.image.path}: {e}")
