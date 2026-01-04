from flask import Flask, jsonify, request, render_template, Response
import cv2
import mediapipe as mp
import numpy as np

# ---------------- Flask setup ----------------
app = Flask(__name__)

# ---------------- Global state ----------------
exercise_mode = 1
exercise_counts = {
    "bicep_curl_left": 0,
    "bicep_curl_right": 0,
    "squat": 0,
    "pushup": 0,
    "jumping_jack": 0
}

stages = {
    "curl_left": None,
    "curl_right": None,
    "squat": None,
    "pushup": None,
    "jumpingjack": None
}

# ---------------- MediaPipe setup ----------------
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

# ---------------- Utility functions ----------------
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - \
              np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360-angle if angle > 180 else angle

def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def extract_landmarks(landmarks):
    get = lambda p: [landmarks[p.value].x, landmarks[p.value].y]
    return {
        "left_shoulder": get(mp_pose.PoseLandmark.LEFT_SHOULDER),
        "left_elbow": get(mp_pose.PoseLandmark.LEFT_ELBOW),
        "left_wrist": get(mp_pose.PoseLandmark.LEFT_WRIST),
        "right_shoulder": get(mp_pose.PoseLandmark.RIGHT_SHOULDER),
        "right_elbow": get(mp_pose.PoseLandmark.RIGHT_ELBOW),
        "right_wrist": get(mp_pose.PoseLandmark.RIGHT_WRIST),
        "left_hip": get(mp_pose.PoseLandmark.LEFT_HIP),
        "left_knee": get(mp_pose.PoseLandmark.LEFT_KNEE),
        "left_ankle": get(mp_pose.PoseLandmark.LEFT_ANKLE),
        "right_hip": get(mp_pose.PoseLandmark.RIGHT_HIP),
        "right_knee": get(mp_pose.PoseLandmark.RIGHT_KNEE),
        "right_ankle": get(mp_pose.PoseLandmark.RIGHT_ANKLE),
    }

# ---------------- Video generator ----------------
def generate_frames():
    global exercise_mode, exercise_counts, stages

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if results.pose_landmarks:
            lm = extract_landmarks(results.pose_landmarks.landmark)

            # ---- angles ----
            left_elbow = calculate_angle(lm["left_shoulder"], lm["left_elbow"], lm["left_wrist"])
            right_elbow = calculate_angle(lm["right_shoulder"], lm["right_elbow"], lm["right_wrist"])
            left_knee = calculate_angle(lm["left_hip"], lm["left_knee"], lm["left_ankle"])
            right_knee = calculate_angle(lm["right_hip"], lm["right_knee"], lm["right_ankle"])

            avg_elbow = (left_elbow + right_elbow) / 2
            avg_knee = (left_knee + right_knee) / 2

            wrist_dist = distance(lm["left_wrist"], lm["right_wrist"])
            ankle_dist = distance(lm["left_ankle"], lm["right_ankle"])
            shoulder_dist = distance(lm["left_shoulder"], lm["right_shoulder"])
            norm_ankle = ankle_dist / shoulder_dist

            avg_shoulder_y = (lm["left_shoulder"][1] + lm["right_shoulder"][1]) / 2
            hands_up = lm["left_wrist"][1] < avg_shoulder_y and lm["right_wrist"][1] < avg_shoulder_y

            # ---- exercise logic ----
            if exercise_mode == 1:  # bicep curl
                if left_elbow > 160: stages["curl_left"] = "down"
                if left_elbow < 40 and stages["curl_left"] == "down":
                    stages["curl_left"] = "up"
                    exercise_counts["bicep_curl_left"] += 1

                if right_elbow > 160: stages["curl_right"] = "down"
                if right_elbow < 40 and stages["curl_right"] == "down":
                    stages["curl_right"] = "up"
                    exercise_counts["bicep_curl_right"] += 1

            elif exercise_mode == 2:  # squat
                if avg_knee > 160: stages["squat"] = "up"
                if avg_knee < 90 and stages["squat"] == "up":
                    stages["squat"] = "down"
                    exercise_counts["squat"] += 1

            elif exercise_mode == 3:  # pushup
                if avg_elbow > 160: stages["pushup"] = "up"
                if avg_elbow < 90 and stages["pushup"] == "up":
                    stages["pushup"] = "down"
                    exercise_counts["pushup"] += 1

            elif exercise_mode == 4:  # jumping jack
                if hands_up and norm_ankle > 1.4:
                    stages["jumpingjack"] = "open"
                if not hands_up and norm_ankle < 1.0 and stages["jumpingjack"] == "open":
                    stages["jumpingjack"] = "close"
                    exercise_counts["jumping_jack"] += 1

            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template("workinout.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/get_counts")
def get_counts():
    return jsonify(exercise_counts)

@app.route("/set_exercise", methods=["POST"])
def set_exercise():
    global exercise_mode
    exercise_mode = request.json["exercise_mode"]
    return jsonify({"status": "ok"})

# ---------------- Run app ----------------
if __name__ == "__main__":
    app.run(debug=True)
