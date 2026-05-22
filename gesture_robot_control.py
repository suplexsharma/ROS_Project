import time
from pathlib import Path

import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2


# =========================================================
# CONFIGURATION
# =========================================================

MODEL_PATH = Path("gesture_recognizer.task")

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

CONFIDENCE_THRESHOLD = 0.6

WINDOW_NAME = "Gesture Recognition"


# =========================================================
# GESTURE MAPPING
# =========================================================

GESTURE_ACTIONS = {
    "Thumb_Up": "MOVE FORWARD",
    "Thumb_Down": "MOVE BACKWARD",
    "Victory": "STOP",
    "Pointing_Up": "TURN LEFT",
    "Closed_Fist": "TURN RIGHT",
    "Open_Palm": "IDLE",
    "ILoveYou": "CUSTOM ACTION",
}


# =========================================================
# CHECK MODEL
# =========================================================

def check_model():

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"\nModel file not found:\n{MODEL_PATH}\n\n"
            "Download the MediaPipe gesture recognizer model manually\n"
            "and place it in the same folder as this script.\n\n"
            "Expected file:\n"
            "gesture_recognizer.task"
        )


# =========================================================
# SETUP RECOGNIZER
# =========================================================

def setup_recognizer():

    base_options = python.BaseOptions(
        model_asset_path=str(MODEL_PATH)
    )

    options = vision.GestureRecognizerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.4,
        min_hand_presence_confidence=0.4,
        min_tracking_confidence=0.4,
    )

    recognizer = vision.GestureRecognizer.create_from_options(
        options
    )

    return recognizer


# =========================================================
# DRAW HAND LANDMARKS
# =========================================================

def draw_landmarks(frame, hand_landmarks_list):

    if not hand_landmarks_list:
        return

    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands

    for hand_landmarks in hand_landmarks_list:

        normalized_landmarks = landmark_pb2.NormalizedLandmarkList(
            landmark=[
                landmark_pb2.NormalizedLandmark(
                    x=lm.x,
                    y=lm.y,
                    z=lm.z
                )
                for lm in hand_landmarks
            ]
        )

        mp_drawing.draw_landmarks(
            frame,
            normalized_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing.DrawingSpec(
                color=(0, 255, 0),
                thickness=2,
                circle_radius=2
            ),
            mp_drawing.DrawingSpec(
                color=(0, 0, 255),
                thickness=2
            ),
        )


# =========================================================
# PROCESS FRAME
# =========================================================

def process_frame(frame, recognizer):

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    timestamp_ms = int(time.time() * 1000)

    result = recognizer.recognize_for_video(
        mp_image,
        timestamp_ms
    )

    gesture_name = "No Gesture"
    confidence = 0.0
    robot_action = "NONE"

    if result.gestures and result.hand_landmarks:

        top_gesture = result.gestures[0][0]

        gesture_name = top_gesture.category_name
        confidence = top_gesture.score

        if confidence >= CONFIDENCE_THRESHOLD:

            robot_action = GESTURE_ACTIONS.get(
                gesture_name,
                "UNKNOWN"
            )

        draw_landmarks(
            frame,
            result.hand_landmarks
        )

    return frame, gesture_name, confidence, robot_action


# =========================================================
# DRAW UI
# =========================================================

def draw_ui(frame, gesture_name, confidence, robot_action):

    cv2.putText(
        frame,
        f"Gesture : {gesture_name}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        f"Confidence : {confidence:.2f}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        f"Robot Action : {robot_action}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 0),
        2,
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("\nStarting Gesture Recognition System...\n")

    check_model()

    recognizer = setup_recognizer()

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Unable to open webcam.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    print("Press 'Q' to quit.\n")

    while True:

        success, frame = cap.read()

        if not success:
            print("Failed to read frame.")
            break

        frame = cv2.flip(frame, 1)

        frame, gesture_name, confidence, robot_action = process_frame(
            frame,
            recognizer
        )

        draw_ui(
            frame,
            gesture_name,
            confidence,
            robot_action
        )

        cv2.imshow(
            WINDOW_NAME,
            frame
        )

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

    cap.release()

    cv2.destroyAllWindows()

    print("\nApplication Closed.\n")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()