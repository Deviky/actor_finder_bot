import uuid
import face_recognition
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image
import os
from sqlighter import DataBase
from ObjectStorage import ObjectStorage

def findMostSimilarFace(category, imageFileUploaded):
    dbService = DataBase()
    objectStorage = ObjectStorage()
    cropped_folder = 'cropped_photos'

    if not os.path.exists(cropped_folder):
        os.makedirs(cropped_folder)

    try:
        unknown_image = face_recognition.load_image_file(imageFileUploaded)
        unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

        max_similarity = -1
        most_similar_file = None
        most_similar_face_location = None
        most_similar_actor_name = None

        margin = 100
        ids = dbService.getAllIds(category)

        for id in ids:
            print(id)
            currentRow = dbService.getById(category, id)
            image = objectStorage.getImg(str(currentRow[2]), category)
            if image is None:
                continue
            face_encodings = face_recognition.face_encodings(image)
            face_locations = face_recognition.face_locations(image)
            for encoding, face_location in zip(face_encodings, face_locations):
                similarity = cosine_similarity([unknown_encoding], [encoding])[0][0]

                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_file = str(currentRow[2])
                    most_similar_face_location = face_location
                    most_similar_actor_name = str(currentRow[1])

        if most_similar_file and most_similar_face_location:
            image = objectStorage.getImg(most_similar_file, category)
            top, right, bottom, left = most_similar_face_location

            top = max(0, top - margin)
            right = min(image.shape[1], right + margin)
            bottom = min(image.shape[0], bottom + margin)
            left = max(0, left - margin)

            face_image = image[top:bottom, left:right]
            pil_image = Image.fromarray(face_image)
            unique_filename = str(uuid.uuid4()) + ".jpg"
            cropped_filename = os.path.join(cropped_folder, unique_filename)
            pil_image.save(cropped_filename)
            return [cropped_filename, most_similar_actor_name]
        else:
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
