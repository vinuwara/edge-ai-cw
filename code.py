import cv2
import os
import time  # Import time module for adding delays
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Load pre-trained face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def detect_faces_and_send_email():
    # Initialize Pi camera
    cap = cv2.VideoCapture(0)

    # Create a directory to store detected faces
    os.makedirs("detected_faces", exist_ok=True)
    counter = 0

    while counter < 3:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Convert frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces in the grayscale frame
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around detected faces and save the full image
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            # Save the whole image when a face is detected
            filename = os.path.join("detected_faces", f"face_{counter}.jpg")
            cv2.imwrite(filename, frame)
            counter += 1

        # Display the resulting frame
        cv2.imshow('Face Detection', frame)

        # Delay for 2 seconds
        time.sleep(2)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the capture
    cap.release()
    cv2.destroyAllWindows()

    # Send email with the detected face images as attachments
    sender_email = "atomicxtomato@gmail.com"  # Replace with your email
    receiver_email = "ridmikahasaranga@gmail.com"  # Replace with recipient email
    password = "tolv erww qtzy jgwr"  # Replace with your email password

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Detected Faces"

    body = "Faces detected in the attached images."
    message.attach(MIMEText(body, "plain"))

    # Attach detected face images
    for filename in os.listdir("detected_faces"):
        attachment = os.path.join("detected_faces", filename)
        with open(attachment, "rb") as f:
            image = MIMEImage(f.read(), name=os.path.basename(attachment))
        message.attach(image)

    # Connect to SMTP server and send email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

    print("Email sent")

detect_faces_and_send_email()
