import tkinter as tk
from tkinter import ttk
import cv2
import PIL.Image, PIL.ImageTk  # Required for displaying camera feed in Tkinter
import os
import time
import smtplib
import requests
import threading
import speech_recognition as srec
import pyttsx3
import winsound
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Load pre-trained face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Speech recognition setups
rec = srec.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def validate_password(max_attempts=3):
    psswd = '123' or '1 2 3' or ' 1 2 3 '
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
    detected_images = []
    while True:  # Continuous loop for face detection and email sending
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
                        img_path = os.path.join(output_folder, f"face_{frame_count}_{i}.jpg")
                        cv2.imwrite(img_path, face_img)
                        detected_images.append(img_path)

                    cv2.imwrite(os.path.join(output_folder, f"frame_{frame_count}.jpg"), frame)

                    frame_count += 1

            prev_frame = gray.copy()

            time.sleep(1)  # Add a delay of 1 second between capturing frames

        cap.release()
        cv2.destroyAllWindows()

        # Send images to the FastAPI endpoint for face recognition
        url = "http://192.168.1.61:8000/prediction"  # Replace with your FastAPI endpoint URL
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
                return detected_images

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
            return detected_images

class SecuritySystemUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Security System")
        self.geometry("800x600")

        self.create_widgets()
        self.start_camera()  # Start capturing camera feed

    def create_widgets(self):
        # Navigation bar
        nav_bar = tk.Frame(self)
        nav_bar.pack(side=tk.TOP, fill=tk.X)

        home_button = ttk.Button(nav_bar, text="Start", command=self.show_home)
        home_button.pack(side=tk.LEFT, padx=10)

        # Main content area
        self.main_content = tk.Frame(self)
        self.main_content.pack(fill=tk.BOTH, expand=True)

        # Terminal output
        self.terminal_output = tk.Text(self.main_content, height=10, width=80, state=tk.DISABLED)
        self.terminal_output.pack(pady=20)

        # Camera feed display
        self.camera_label = tk.Label(self.main_content)
        self.camera_label.pack(pady=10)

        # Status indicator
        self.status_label = tk.Label(self, text="System Disarmed", fg="green")
        self.status_label.pack(side=tk.BOTTOM, pady=10)

        # Create a frame to display images
        self.image_frame = tk.Frame(self.main_content)
        self.image_frame.pack(pady=10)

        # Load and display initial placeholder images
        self.placeholder_images = []
        for i in range(4):  # Assuming you want to display four images
            placeholder_img = tk.PhotoImage(width=200, height=200)  # Placeholder image size
            placeholder_label = tk.Label(self.image_frame, image=placeholder_img)
            placeholder_label.grid(row=0, column=i, padx=10)
            self.placeholder_images.append(placeholder_img)

        # Create a label for the home screen (replace with your content)
        self.home_label = tk.Label(self.main_content, text="Home Screen")
        self.home_label.pack(pady=20)

    def start_camera(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.show_camera_feed()

    def show_camera_feed(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = PIL.Image.fromarray(frame)
            imgtk = PIL.ImageTk.PhotoImage(image=image)
            self.camera_label.imgtk = imgtk
            self.camera_label.config(image=imgtk)
        self.camera_label.after(10, self.show_camera_feed)  # Refresh every 10 milliseconds

    def show_home(self):
        self.hide_all()
        self.home_label.pack(pady=20)

        # Run face detection and email sending in a separate thread
        threading.Thread(target=self.run_face_detection_and_email).start()

    def hide_all(self):
        self.home_label.pack_forget()

    def run_face_detection_and_email(self):
        # Redirect stdout to the Text widget for terminal output
        import sys
        sys.stdout = TextRedirector(self.terminal_output, "stdout")

        # Call the face detection and email sending function in a loop
        while True:
            detected_images = detect_faces_and_send_email()

            # Update the displayed images with the newly detected images
            self.update_images(detected_images)

    def update_images(self, detected_images):
        # Update the placeholder images with the detected images
        for i, img_path in enumerate(detected_images):
            if i < len(self.placeholder_images):
                img = tk.PhotoImage(file=img_path)
                self.placeholder_images[i].configure(image=img)
                self.placeholder_images[i].image = img

class TextRedirector(object):
    def __init__(self, text_widget, tag="stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, str):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, str, (self.tag,))
        self.text_widget.config(state=tk.DISABLED)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

if __name__ == "__main__":
    app = SecuritySystemUI()
    app.mainloop()
