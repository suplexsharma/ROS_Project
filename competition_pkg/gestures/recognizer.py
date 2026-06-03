import time
import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from .gesture import Gesture


def load_model(file):
    base_options = python.BaseOptions(
        model_asset_path=str(file)
    )
    options = vision.GestureRecognizerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.4,
        min_hand_presence_confidence=0.4,
        min_tracking_confidence=0.4,
    )
    recognizer = vision.GestureRecognizer.create_from_options(options)
    return recognizer


class GestureRecognizer:
    def __init__(self, model, confidence_threshold=0.6):
        self.model = model
        self.confidence_threshold = confidence_threshold

    @classmethod
    def load_from_path(cls, filename) -> "GestureRecognizer":
        model = load_model(filename)
        return cls(model)

    def process_frame(self, frame) -> Gesture:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        timestamp_ms = int(time.time() * 1000)
        result = self.model.recognize_for_video(
            mp_image,
            timestamp_ms
        )
        gesture = Gesture.NO_GESTURE
        if result.gestures and result.hand_landmarks:
            top_gesture = result.gestures[0][0]
            gesture_name = top_gesture.category_name
            confidence = top_gesture.score
            if confidence >= self.confidence_threshold:
                gesture =  Gesture.from_name(gesture_name)
        return gesture
