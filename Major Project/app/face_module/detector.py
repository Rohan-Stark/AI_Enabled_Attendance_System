"""
Face Detector — handles face detection and 128-d encoding generation.
Uses ageitgey/face_recognition with OpenCV for image handling.
"""
from typing import Optional, List, Tuple
import face_recognition
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FaceDetector:
    """Detect faces and compute 128-dimensional encodings."""

    def __init__(self, model: str = "hog", num_jitters: int = 1):
        """
        Args:
            model: 'hog' for CPU (fast) or 'cnn' for GPU (accurate).
            num_jitters: Re-sample face this many times for better encoding.
        """
        self.model = model
        self.num_jitters = num_jitters

    def detect_faces(self, frame: np.ndarray) -> list:
        """
        Detect face bounding boxes in a BGR frame.

        Returns:
            List of (top, right, bottom, left) tuples.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb, model=self.model)
        logger.debug(f"Detected {len(locations)} face(s)")
        return locations

    def encode_faces(self, frame: np.ndarray, locations: list = None) -> list:
        """
        Compute 128-d face encodings for all faces in frame.

        Args:
            frame: BGR image.
            locations: Pre-computed face locations (optional).

        Returns:
            List of 128-d numpy arrays.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if locations is None:
            locations = face_recognition.face_locations(rgb, model=self.model)
        encodings = face_recognition.face_encodings(
            rgb, known_face_locations=locations, num_jitters=self.num_jitters
        )
        return encodings

    def encode_single_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load an image file and return the first face encoding found.
        Used for student registration.
        """
        try:
            img = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(img, num_jitters=self.num_jitters)
            if encodings:
                return encodings[0]
            logger.warning(f"No face found in {image_path}")
            return None
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None

    @staticmethod
    def draw_boxes(frame: np.ndarray, locations: list, names: list = None,
                   color: tuple = (0, 255, 0)) -> np.ndarray:
        """Draw bounding boxes and optional names on frame."""
        annotated = frame.copy()
        for i, (top, right, bottom, left) in enumerate(locations):
            cv2.rectangle(annotated, (left, top), (right, bottom), color, 2)
            if names and i < len(names):
                label = names[i]
                # Label background
                cv2.rectangle(annotated, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
                cv2.putText(annotated, label, (left + 6, bottom - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        return annotated
