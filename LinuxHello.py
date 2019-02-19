import os
import sys
import time
import face_recognition
from cv2 import *
from pyautogui import press, typewrite

me_dir = sys.argv[1]

my_encodings = []

print("my pics: ")
piclist = os.listdir(me_dir)
for pic in piclist:
    pic_loc = me_dir + "/" + pic
    print("\t", pic)
    image = face_recognition.load_image_file(pic_loc)
    try:
        encoding = face_recognition.face_encodings(image)[0]
        my_encodings.append(encoding)
    except IndexError:
        print("Did't find face in picture: ", pic)
        continue

tmp_filename = "tmp.jpg"

found_me = False

while not found_me:
    s, img = VideoCapture(0).read()
    while not s:
        s, img = VideoCapture(0).read()
    imwrite(tmp_filename, img)
    
    unknown_image = face_recognition.load_image_file(tmp_filename)
    try:
        unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
        results = face_recognition.compare_faces(my_encodings, unknown_encoding)
        if not True in results:
            print("That's not me")
        else:
            print("That's me")
            break
    except IndexError:
        print("There isn't a face in the picture")

    os.remove("tmp.jpg")


# type password and hit enter

typewrite("MySuperSecretP455w0rd", interval=0.05)
press("enter")
