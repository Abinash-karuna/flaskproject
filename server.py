from flask import Flask, request, jsonify
import cv2
import pytesseract
import numpy as np
import pyttsx3
import time

app = Flask(__name__)

# Initialize Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'/app/.apt/usr/bin/tesseract'  # Render path for Tesseract

# Load Object Detection Model
thres = 0.45  # Threshold to detect objects
classNames = []
with open("coco.names", 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')
configPath = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "frozen_inference_graph.pb"

net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Initialize Text-to-Speech
engine = pyttsx3.init()


@app.route('/upload', methods=['POST'])
def upload_image():
    image_data = request.data
    np_arr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    filename = f"received_{int(time.time())}.jpg"
    cv2.imwrite(filename, img)
    print(f"Image received and saved as {filename}")

    # Perform Object Detection
    detected_objects = detect_objects(img)

    # Perform Text Recognition (OCR)
    detected_text = detect_text(img)

    # Convert results to JSON and return
    result = {
        "detected_text": detected_text,
        "detected_objects": detected_objects
    }

    return jsonify(result), 200


def detect_objects(img):
    classIds, confs, bbox = net.detect(img, confThreshold=thres)
    detected_objects = {}

    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            detected_objects[className] = detected_objects.get(className, 0) + 1
            cv2.rectangle(img, (box[0], box[1]), (box[0] + box[2], box[1] + box[3]), (0, 255, 0), 2)
            cv2.putText(img, f"{className} {round(confidence * 100, 2)}%", (box[0], box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return detected_objects


def detect_text(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    custom_config = r'--oem 3 --psm 6 -l eng'
    data = pytesseract.image_to_data(thresh, config=custom_config, output_type=pytesseract.Output.DICT)

    detected_text = ""
    for i in range(len(data['text'])):
        if int(data['conf'][i]) > 70:
            detected_text += data['text'][i] + " "

    return detected_text if detected_text else "No text detected"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
