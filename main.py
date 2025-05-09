import cv2
import pytesseract
import pyttsx3
import numpy as np

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Specify the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize webcam
cap = cv2.VideoCapture(0)  # 0 represents the default webcam

# Check if the webcam is opened correctly
if not cap.isOpened():
    print("Error: Could not open webcam.")
    engine.say("Error: Could not open webcam.")
    engine.runAndWait()
    exit()

# Load object detection model
thres = 0.45  # Threshold to detect object
classNames = []
classFile = 'coco.names'
with open(classFile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')
configPath = 'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'
weightsPath = 'frozen_inference_graph.pb'
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        engine.say("Error: Could not read frame.")
        engine.runAndWait()
        break

    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply Adaptive Thresholding for better text extraction
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Perform OCR with bounding boxes
    custom_config = r'--oem 3 --psm 6 -l eng'
    data = pytesseract.image_to_data(thresh, config=custom_config, output_type=pytesseract.Output.DICT)

    detected_text = ""

    for i in range(len(data['text'])):
        conf = int(data['conf'][i])
        text = data['text'][i].strip()

        if text and conf > 70:  # Ignore low-confidence words
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            detected_text += text + " "

    if not detected_text:  # If no text is detected
        detected_text = "No text is present"


    # Perform object detection
    classIds, confs, bbox = net.detect(frame, confThreshold=thres)
    detected_objects = {}

    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            detected_objects[className] = detected_objects.get(className, 0) + 1
            cv2.rectangle(frame, (box[0], box[1]), (box[0] + box[2], box[1] + box[3]), (0, 255, 0), 2)
            cv2.putText(frame, f"{className} {round(confidence * 100, 2)}%", (box[0], box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Live OCR & Object Detection", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):
        print("Detected Text:", detected_text)
        engine.say(detected_text)
        engine.runAndWait()

    elif key == ord('l') and detected_objects:
        object_names = [f"{count} {obj}" for obj, count in detected_objects.items()]
        object_names_str = ', '.join(object_names)
        obj_result = f"Detected objects are: {object_names_str}"
        print(obj_result)
        engine.say(obj_result)
        engine.runAndWait()

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
