import cv2
import face_recognition
import numpy as np
import pickle
from .models import FaceImage

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_details = {}
        self.current_recognized_faces = []
        self.load_known_faces()

    def __del__(self):
        self.release()

    def release(self):
        if hasattr(self, 'video') and self.video.isOpened():
            self.video.release()

    def load_known_faces(self):
        """Loads face encodings from the database."""
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_details = {} # Map name -> details dict
        
        faces = FaceImage.objects.exclude(encoding=None)
        for face in faces:
            if face.encoding:
                encoding = pickle.loads(face.encoding)
                self.known_face_encodings.append(encoding)
                self.known_face_names.append(face.person.name)
                
                # Store details
                self.known_face_details[face.person.name] = {
                    'name': face.person.name,
                    'class_name': face.person.class_name,
                    'age': face.person.age,
                    'department': face.person.department,
                    'time': 'Now' # Placeholder, can be updated with timestamp
                }
        print(f"Loaded {len(self.known_face_encodings)} known faces.")

    def get_frame(self):
        success, image = self.video.read()
        if not success:
            return None

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)
        
        # Convert the image from BGR color (which OpenCV uses) to RGB color
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all the faces and face encodings in the current frame of video
        # 'hog' is much faster but less accurate. Use 'cnn' for high-accuracy (but slower) results.
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        self.current_recognized_faces = [] # Reset for current frame

        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
            name = "Unknown"
            person_details = None

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    
                    if name in self.known_face_details:
                            person_details = self.known_face_details[name]
                            self.current_recognized_faces.append(person_details)

            face_names.append(name)

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)

            # Draw a label with a name below the face
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(image, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
