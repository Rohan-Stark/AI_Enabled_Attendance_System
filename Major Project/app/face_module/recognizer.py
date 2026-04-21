"""
Face Recognizer — matches detected face encodings against known encodings.
"""
from typing import Optional, List, Tuple
import face_recognition
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FaceRecognizer:
    """Match face encodings against a database of known faces."""

    def __init__(self, tolerance: float = 0.45):
        """
        Args:
            tolerance: How much distance between faces to consider a match.
                       Lower = stricter. Default 0.45 balances accuracy.
        """
        self.tolerance = tolerance
        self.known_encodings: List[np.ndarray] = []
        self.known_ids: List[int] = []         # Student IDs
        self.known_names: List[str] = []        # Student names

    def load_known_faces(self, students: list):
        """
        Load face encodings from Student model instances.

        Args:
            students: List of Student objects with face_encoding_blob set.
        """
        self.known_encodings = []
        self.known_ids = []
        self.known_names = []

        for student in students:
            encoding = student.get_face_encoding()
            if encoding is not None:
                self.known_encodings.append(encoding)
                self.known_ids.append(student.id)
                self.known_names.append(student.name)

        logger.info(f"Loaded {len(self.known_encodings)} known face(s)")

    def identify(self, face_encoding: np.ndarray) -> Tuple[Optional[int], str, float]:
        """
        Match a single face encoding against known encodings.

        Returns:
            (student_id, student_name, distance) if matched,
            (None, "Unknown", min_distance) if no match.
        """
        if not self.known_encodings:
            return None, "Unknown", 1.0

        # Compute distances to all known faces
        distances = face_recognition.face_distance(self.known_encodings, face_encoding)
        min_idx = np.argmin(distances)
        min_distance = distances[min_idx]

        if min_distance <= self.tolerance:
            student_id = self.known_ids[min_idx]
            student_name = self.known_names[min_idx]
            logger.info(f"Matched: {student_name} (dist={min_distance:.3f})")
            return student_id, student_name, float(min_distance)

        logger.debug(f"No match — closest distance: {min_distance:.3f}")
        return None, "Unknown", float(min_distance)

    def identify_multiple(self, face_encodings: list) -> list[tuple]:
        """
        Identify multiple faces in a single frame.

        Returns:
            List of (student_id, name, distance) tuples.
        """
        results = []
        for enc in face_encodings:
            results.append(self.identify(enc))
        return results
