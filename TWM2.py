from scipy.spatial import distance
from imutils import face_utils
from pygame import mixer
import imutils
import dlib
import cv2
import serial
import time

# Initialize serial communication with Arduino
ser = serial.Serial('COM3', 9600)
time.sleep(1)  # Wait for Arduino to initialize

# Initialize Pygame mixer for audio alerts
mixer.init()
mixer.music.load("music.wav")

# Function to calculate eye aspect ratio (EAR)
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# Dynamic thresholding parameters
min_thresh = 0.20  # Minimum threshold for small eyes
max_thresh = 0.30  # Maximum threshold for large eyes

# Normalize EAR by dividing by average eye size
avg_eye_size = 60  # Adjust this value based on your camera resolution and typical eye sizes
norm_factor = 1.0  # You may adjust this factor based on empirical observations

# Initial threshold
thresh = min_thresh

# Load face detector and shape predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Define indexes for left and right eyes in the face landmark detection
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# Open video capture device
cap = cv2.VideoCapture(0)

flag = 0  # Counter for consecutive frames below threshold
detection_enabled = False  # Flag to enable/disable drowsiness detection
led_on_time = 0  # Time when LED was turned on
frame_check = 20

# Main loop for video capture and processing
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        break
    
    # Preprocess the frame
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the grayscale frame
    subjects = detector(gray, 0)

    # Visualize detected faces
    for subject in subjects:
        (x, y, w, h) = face_utils.rect_to_bb(subject)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Process the first detected face if any
    if subjects:
        # Predict facial landmarks for the current face
        subject = subjects[0]
        shape = predictor(gray, subject)
        shape = face_utils.shape_to_np(shape)
        
        # Visualize detected landmarks
        for (x, y) in shape:
            cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)

        # Extract left and right eye regions
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]

        # Calculate EAR for left and right eyes
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)

        # Calculate average EAR
        ear = (leftEAR + rightEAR) / 2.0   

        # Calculate eye size for dynamic thresholding
        left_eye_size = distance.euclidean(shape[36], shape[39])
        right_eye_size = distance.euclidean(shape[42], shape[45])
        eye_size = (left_eye_size + right_eye_size) / 2.0
        
        # Normalize EAR by dividing by eye size
        norm_ear = (leftEAR + rightEAR) / 2.0 / (eye_size / avg_eye_size * norm_factor)
        
        # Dynamic thresholding based on eye size
        thresh = min_thresh + (max_thresh - min_thresh) * (1 - (eye_size / avg_eye_size))

        if detection_enabled:  # Only run detection if enabled
            if norm_ear < thresh:
                flag += 1
                print(flag)
                if flag >= frame_check:
                    # Sound alarm and activate LED
                    cv2.putText(frame, "*ALERT!*", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(frame, "*ALERT!*", (10, 325),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    try:
                        mixer.music.play()
                        led_on_time = time.time()  # Record time when LED turns on
                        ser.write(b'd')  # Command Arduino to turn on LED
                    except Exception as e:
                        print("Error playing sound:", e)
            else:
                flag = 0

    # Turn off LED after 10 seconds of alarm
    if time.time() - led_on_time >= 10:
        ser.write(b'o')  # Command Arduino to turn off LED
        
    # Display the frame
    cv2.imshow("Frame", frame)

    # Check for user input to toggle detection
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("s"):  # Toggle detection with 's' key
        detection_enabled = not detection_enabled

# Release video capture and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
ser.close()  # Close serial connection with Arduino
