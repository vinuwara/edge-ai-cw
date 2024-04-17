import cv2
import os
import time
import smtplib
import requests
import speech_recognition as srec
import pyttsx3
import winsound
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMText
from email.mime.image import MIMEImage

# Load pre-trained face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Speech recognition setup
rec = srec.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def validate_password(max_attempts=3):
    psswd = '123' or '1 2 3'
    attempts = 0
    password_recognized = False
    while attempts < max_attempts:
        try:
            # Play sound cue for listening start
            speak('please say the password to disarm')
            with srec.Microphone() as source:
                rec.adjust_for_ambient_noise(source, duration=1)
                audio = rec.listen(source)

                spoken_text = rec.recognize_google(audio)
                spoken_text = spoken_text.lower()

                print("Spoken Text:", spoken_text)

                if spoken_text == psswd:
                    print('Password is correct.')
                    speak('Password is correct.')
                    password_recognized = True
                    break
                else:
                    attempts += 1
                    print('Invalid password. Attempts left:', max_attempts - attempts)
                    speak('Invalid password.')

        except srec.RequestError as e:
            print("Could not request results; {0}".format(e))
        except srec.UnknownValueError:
            print("Unable to recognize speech.")
        except Exception as e:
            print("Error occurred:", e)

        # Play sound cue for listening end
        winsound.Beep(2000, 500)  # You can adjust the frequency and duration of the beep

    if password_recognized:
        return True
    else:
        return False

def detect_faces_and_send_email():
    # Perform face detection
    output_folder = "detected_faces"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Capture frames
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FPS, 30)  # Set the frame rate to 30 frames per second

    start_time = time.time()  # Record the start time
    frame_count = 0
    prev_frame = None
    while frame_count < 5:  # Capture frames until five images have been processed
        ret, frame = cap.read()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if prev_frame is not None:
            difference = cv2.absdiff(prev_frame, gray)
            _, difference = cv2.threshold(difference, 30, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(difference, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) > 0:
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))

                for i, (x, y, w, h) in enumerate(faces):
                    face_img = frame[y:y + h, x:x + w]
                    cv2.imwrite(os.path.join(output_folder, f"face_{frame_count}_{i}.jpg"), face_img)

                cv2.imwrite(os.path.join(output_folder, f"frame_{frame_count}.jpg"), frame)

                frame_count += 1

                cv2.imshow('Face Detection', frame)

        prev_frame = gray.copy()

        cv2.waitKey(1)

    cap.release()
    cv2.destroyAllWindows()

    # Send images to the FastAPI endpoint for face recognition
    url = "http://192.168.1.3:8000/face_recognition"  # Replace with your API URL
    files = [("file", open(os.path.join(output_folder, "frame_4.jpg"), "rb"))]  # Send the first frame for recognition
    response = requests.post(url, files=files)
    print(response.json())
    if 'Yes' in response.json():
        print("Person is recognized")
        speak("Person is recognized")
    else:
        print("Person is not recognized")
        speak("Person is not recognized")

        # Run voice test if face is not recognized
        print("Running voice test...")
        if validate_password():
            print("Voice test passed. Not sending email.")
            speak("Voice test passed. Not sending email.")
            return

        # Send email with the detected face images as attachments
        sender_email = "atomicxtomato@gmail.com"  # Replace with your email
        receiver_email = "ronathjayasuriya@gmail.com"  # Replace with recipient email
        password = "tolv erww qtzy jgwr"  # Replace with your email password

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "Detected Faces"

        body = "Faces detected in the attached images."
        message.attach(MIMEText(body, "plain"))

        # Attach the images
        for filename in os.listdir(output_folder):
            if filename.endswith(".jpg"):
                with open(os.path.join(output_folder, filename), "rb") as attachment:
                    part = MIMEImage(attachment.read(), name=os.path.basename(filename))
                    message.attach(part)

        # Connect to SMTP server and send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())

        print("Email sent")
        speak("Email sent")

# Call the function to detect faces and send email
detect_faces_and_send_email()
