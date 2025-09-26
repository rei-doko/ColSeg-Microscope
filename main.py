# Imports dependencies and libraries
from flask import Flask, render_template, Response, jsonify, request
import flaskwebgui
import math
import cv2
import numpy as np
import colorsys
import threading
import time
import csv
import os
from datetime import datetime

app = Flask(__name__)
gui = flaskwebgui.FlaskUI(app=app, server="flask", width=800, height=600)
raw_camera = cv2.VideoCapture(0)

target_roi_coords = None
background_roi_coords = None

# @app.route('/') creates a directory for JQuery
# Serves main HTML page
@app.route('/')
def index():
    return render_template('index.html')

# Reads camera frames and converts to bytes
def generate_frames():
    while True:
    # Reads camera frames
        success, raw_camera_frame = raw_camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpeg', raw_camera_frame)
            raw_camera_frame = buffer.tobytes()
        yield(b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + raw_camera_frame + b'\r\n')
        
# Handles raw camera output [Complete]
@app.route('/camera')
def camera():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

# Converts wavelength to RGB values [Complete]
def wavelength_to_rgb(wavelength):
    gamma = 0.8
    intensity_max = 255

    if (wavelength >= 380) and (wavelength < 440):
        R = -(wavelength - 440) / (440 - 380)
        G = 0.0
        B = 1.0
    elif (wavelength >= 440) and (wavelength < 490):
        R = 0.0
        G = (wavelength - 440) / (490 - 440)
        B = 1.0
    elif (wavelength >= 490) and (wavelength < 510):
        R = 0.0
        G = 1.0
        B = -(wavelength - 510) / (510 - 490)
    elif (wavelength >= 510) and (wavelength < 580):
        R = (wavelength - 510) / (580 - 510)
        G = 1.0
        B = 0.0
    elif (wavelength >= 580) and (wavelength < 645):
        R = 1.0
        G = -(wavelength - 645) / (645 - 580)
        B = 0.0
    elif (wavelength >= 645) and (wavelength < 750):
        R = 1.0
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0

    # Adjust intensity [Complete]
    R = round(intensity_max * (R ** gamma))
    G = round(intensity_max * (G ** gamma))
    B = round(intensity_max * (B ** gamma))

    return R, G, B

# Function to convert RGB to HSV [Complete]
def rgb_to_hsv(R, G, B):
    R, G, B = R / 255.0, G / 255.0, B / 255.0
    h, s, v = colorsys.rgb_to_hsv(R, G, B)
    return (h * 179, s * 255, v * 255)

# Initialize wavelength variables with default values
wavelength1 = 615  # Default minimum wavelength
wavelength2 = 1200  # Default maximum wavelength

# JavaScript variables for wavelengths [Complete]
@app.route('/receive', methods=['POST'])
def recieve():
    global wavelength1, wavelength2
    data = request.get_json()

    wavelength1 = int(data.get('minimumValue'))
    wavelength2 = int(data.get('maximumValue'))
    update_wavelengths()

    return jsonify({"message": f"Received values: Min = {wavelength1}, Max = {wavelength2}"})

# Sets HSV values for the wavelengths [Complete]
def update_wavelengths():
    global hue1, sat1, val1, hue2, sat2, val2
    # Convert the first wavelength [Complete]
    R1, G1, B1 = wavelength_to_rgb(wavelength1)
    hue1, sat1, val1 = rgb_to_hsv(R1, G1, B1)
    

    # Convert the second wavelength [Complete]
    R2, G2, B2 = wavelength_to_rgb(wavelength2)
    hue2, sat2, val2 = rgb_to_hsv(R2, G2, B2)

# Initial conversion of default wavelengths [Complete]
update_wavelengths()

# Reads camera frames, filters it, and then converts to bytes [Complete]
def filtered_frames():
    while True:
        success, filtered_camera_frame = raw_camera.read()
        if not success:
            break
        else:
            hsv = cv2.cvtColor(filtered_camera_frame, cv2.COLOR_BGR2HSV)

            lower = np.array([hue2, 0 , 0])
            upper = np.array([hue1, 255 , 255])

            mask = cv2.inRange(hsv, lower, upper)
            result_frame = cv2.bitwise_and(filtered_camera_frame, filtered_camera_frame, mask = mask)

            ret, f_buffer = cv2.imencode('.jpeg', result_frame)
            result_frame = f_buffer.tobytes()
            yield(b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + result_frame + b'\r\n')

# Handles filtered camera output [Complete]
@app.route('/f_camera')
def f_camera():
    return Response(filtered_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

def select_roi_coordinates():
    global target_roi_coords, background_roi_coords
    success, frame = raw_camera.read()
    if not success:
        print("Error reading frame for ROI selection")
        return

    print("Select Target ROI")
    target = cv2.selectROI("Select Target ROI", frame, False)
    cv2.destroyWindow("Select Target ROI")

    print("Select Background ROI")
    background = cv2.selectROI("Select Background ROI", frame, False)
    cv2.destroyWindow("Select Background ROI")

    target_roi_coords = target
    background_roi_coords = background

def image_analysis():
    if not target_roi_coords or not background_roi_coords:
        print("ROIs not set. Run ROI selector first.")
        return

    x1, y1, w1, h1 = target_roi_coords
    x2, y2, w2, h2 = background_roi_coords

    results_dir = "analysis_results"
    os.makedirs(results_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(results_dir, f"cnr_snr_results_{timestamp}.csv")
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Test #", "µ_signal_raw", "µ_background_raw", "σ_background_raw", "CNR Raw", "SNR Raw", "µ_signal_filtered", "µ_background_filtered", "σ_background_filtered", "CNR Filtered", "SNR Filtered"])

        n = 10
        while n > 0:
            success_raw, frame_raw_analysis = raw_camera.read()
            success_filtered, frame_filtered_analysis = raw_camera.read()
            if not success_raw or not success_filtered:
                break
        
            gray_raw = cv2.cvtColor(frame_raw_analysis, cv2.COLOR_BGR2GRAY)
            gray_filtered = cv2.cvtColor(frame_filtered_analysis, cv2.COLOR_BGR2GRAY)

            target_roi_raw = gray_raw[y1:y1+h1, x1:x1+w1]
            background_roi_raw = gray_raw[y2:y2+h2, x2:x2+w2]
            target_roi_filtered = gray_filtered[y1:y1+h1, x1:x1+w1]
            background_roi_filtered = gray_filtered[y2:y2+h2, x2:x2+w2]

            mean_signal_raw = np.mean(target_roi_raw)
            mean_background_raw = np.mean(background_roi_raw)
            std_background_raw = np.std(background_roi_raw)

            mean_signal_filtered = np.mean(target_roi_filtered)
            mean_background_filtered = np.mean(background_roi_filtered)
            std_background_filtered = np.std(background_roi_filtered)

            cnr_raw = abs(mean_signal_raw - mean_background_raw) / std_background_raw if std_background_raw != 0 else 0
            cnr_filtered = abs(mean_signal_filtered - mean_background_filtered) / std_background_filtered if std_background_filtered != 0 else 0
            snr_raw = mean_signal_raw / std_background_raw if std_background_raw != 0 else 0
            snr_filtered = mean_signal_filtered / std_background_filtered if std_background_filtered != 0 else 0

            #print(f"[Test #{11 - n}], µ_signal_raw: {mean_signal_raw}, µ_background_raw: {mean_background_raw}, σ_backround: {std_background_raw}, CNR Raw: {cnr_raw:.2f}, SNR Raw: {snr_raw:.2f}, µ_signal_filtered: {mean_signal_filtered}, µ_background_filtered: {mean_background_filtered}, σ_backround: {std_background_filtered}, CNR Filtered: {cnr_filtered:.2f}, SNR Filtered: {snr_filtered:.2f}")
            writer.writerow([f"Test #{11 - n}", mean_signal_raw, mean_background_raw, std_background_raw, round(cnr_raw, 2), round(snr_raw, 2), mean_signal_filtered, mean_background_filtered, std_background_filtered, round(cnr_filtered, 2), round(snr_filtered, 2)])

            n -= 1

        print(f"Results saved to: {filename}")

def delayed_analysis():
    time.sleep(3)
    image_analysis()

def pre_camera(frame_count = 20):
    for _ in range(frame_count):
        raw_camera.read()

if __name__ == '__main__':
    pre_camera(20)
    select_roi_coordinates()
    #app.run(debug=True)
    threading.Thread(target=delayed_analysis).start()
    gui.run()