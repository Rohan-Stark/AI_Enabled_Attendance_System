"""
Anti-Spoofing — Eye Blink Detection using Eye Aspect Ratio (EAR).

The EAR method (Soukupová & Čech, 2016) uses 6 facial landmarks per eye
to compute a ratio that drops sharply during a blink. This prevents
attendance marking via a printed photo or a static screen image.

Requires: dlib's 68-point facial landmark predictor.
"""
import os
import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist
import logging

logger = logging.getLogger(__name__)

# Path to dlib's pre-trained landmark predictor
# Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
PREDICTOR_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "shape_predictor_68_face_landmarks.dat"
))

# Indices for left and right eye landmarks in the 68-point model
LEFT_EYE_IDX = list(range(42, 48))
RIGHT_EYE_IDX = list(range(36, 42))


def _eye_aspect_ratio(eye_points: np.ndarray) -> float:
    """
    Compute the Eye Aspect Ratio (EAR) for a single eye.

    EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)

    A low EAR indicates a closed eye (blink).
    """
    # Vertical distances
    v1 = dist.euclidean(eye_points[1], eye_points[5])
    v2 = dist.euclidean(eye_points[2], eye_points[4])
    # Horizontal distance
    h = dist.euclidean(eye_points[0], eye_points[3])

    ear = (v1 + v2) / (2.0 * h)
    return ear


class AntiSpoof:
    """
    Liveness detector using eye blink counting.
    The user must blink a required number of times to prove liveness.
    """

    def __init__(self, ear_threshold: float = 0.21,
                 consecutive_frames: int = 3,
                 required_blinks: int = 2):
        """
        Args:
            ear_threshold: EAR below this = eyes closed.
            consecutive_frames: Frames with low EAR needed to register one blink.
            required_blinks: Total blinks needed to pass liveness check.
        """
        self.ear_threshold = ear_threshold
        self.consecutive_frames = consecutive_frames
        self.required_blinks = required_blinks

        # Internal state
        self._blink_count = 0
        self._frame_counter = 0      # Consecutive low-EAR frames

        # Load dlib face detector & landmark predictor
        self._detector = dlib.get_frontal_face_detector()
        if os.path.exists(PREDICTOR_PATH):
            self._predictor = dlib.shape_predictor(PREDICTOR_PATH)
            self._available = True
            logger.info("Anti-spoof: dlib landmark predictor loaded.")
        else:
            self._predictor = None
            self._available = False
            logger.warning(
                f"Anti-spoof: Predictor not found at {PREDICTOR_PATH}. "
                "Blink detection DISABLED. Download shape_predictor_68_face_landmarks.dat"
            )

    @property
    def is_available(self) -> bool:
        return self._available

    def reset(self):
        """Reset blink counter for a new verification attempt."""
        self._blink_count = 0
        self._frame_counter = 0

    def process_frame(self, frame: np.ndarray) -> dict:
        """
        Process a single frame for blink detection.

        Returns:
            {
                'ear': float,           # Current average EAR
                'blink_count': int,     # Total blinks so far
                'verified': bool,       # True when enough blinks detected
                'message': str          # Status message for UI
            }
        """
        if not self._available:
            return {
                "ear": 0.0,
                "blink_count": 0,
                "verified": True,      # Pass through if detector unavailable
                "message": "Anti-spoof unavailable — skipped"
            }

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._detector(gray, 0)

        ear = 0.0

        if len(faces) == 0:
            return {
                "ear": 0.0,
                "blink_count": self._blink_count,
                "verified": False,
                "message": "No face detected — look at the camera"
            }

        # Use the first (largest) face
        face = faces[0]
        shape = self._predictor(gray, face)
        landmarks = np.array([[shape.part(i).x, shape.part(i).y] for i in range(68)])

        left_eye = landmarks[LEFT_EYE_IDX]
        right_eye = landmarks[RIGHT_EYE_IDX]

        left_ear = _eye_aspect_ratio(left_eye)
        right_ear = _eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0

        # Blink detection state machine
        if ear < self.ear_threshold:
            self._frame_counter += 1
        else:
            if self._frame_counter >= self.consecutive_frames:
                self._blink_count += 1
                logger.debug(f"Blink #{self._blink_count} detected")
            self._frame_counter = 0

        verified = self._blink_count >= self.required_blinks
        remaining = max(0, self.required_blinks - self._blink_count)
        msg = (
            "✓ Liveness verified!" if verified
            else f"Please blink {remaining} more time(s)"
        )

        return {
            "ear": round(ear, 3),
            "blink_count": self._blink_count,
            "verified": verified,
            "message": msg
        }
