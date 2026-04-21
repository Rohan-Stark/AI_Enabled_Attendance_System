"""
Camera Manager — handles webcam capture with frame optimization.
Processes every Nth frame and resizes for performance.
Provides MJPEG streaming for Flask responses.
"""
import cv2
import time
import logging
import threading
import platform

logger = logging.getLogger(__name__)


class Camera:
    """
    Thread-safe webcam wrapper optimized for real-time face recognition.
    Supports frame skipping and resizing to keep CPU usage manageable.
    """

    def __init__(self, source: int = 0, resize_factor: float = 0.25,
                 process_every_n: int = 2):
        """
        Args:
            source: Camera index (0 = default webcam).
            resize_factor: Scale factor for processing frames (0.25 = 1/4 size).
            process_every_n: Only process every Nth frame.
        """
        self.source = source
        self.resize_factor = resize_factor
        self.process_every_n = process_every_n
        self._cap = None
        self._lock = threading.Lock()
        self._frame_count = 0

    def start(self) -> bool:
        """Open the webcam. Returns True if successful."""
        with self._lock:
            # Use DirectShow backend on Windows for better compatibility
            if platform.system() == "Windows":
                self._cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            else:
                self._cap = cv2.VideoCapture(self.source)
            if not self._cap.isOpened():
                logger.error(f"Cannot open camera {self.source}")
                return False
            # Optimize capture buffer
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            logger.info(f"Camera {self.source} opened")
            return True

    def stop(self):
        """Release the webcam."""
        with self._lock:
            if self._cap and self._cap.isOpened():
                self._cap.release()
                logger.info("Camera released")

    def read_frame(self):
        """
        Read a raw frame from the webcam.

        Returns:
            (success, frame) tuple.
        """
        with self._lock:
            if self._cap is None or not self._cap.isOpened():
                return False, None
            return self._cap.read()

    def read_processing_frame(self):
        """
        Read a frame and return both original and resized version.
        Also tracks frame count for skip logic.

        Returns:
            (original_frame, small_frame, should_process)
        """
        success, frame = self.read_frame()
        if not success or frame is None:
            return None, None, False

        self._frame_count += 1
        should_process = (self._frame_count % self.process_every_n) == 0

        small = cv2.resize(frame, (0, 0),
                           fx=self.resize_factor, fy=self.resize_factor)
        return frame, small, should_process

    @property
    def is_opened(self) -> bool:
        with self._lock:
            return self._cap is not None and self._cap.isOpened()

    def generate_mjpeg(self, process_callback=None):
        """
        Generator that yields MJPEG frames for Flask streaming.

        Args:
            process_callback: Optional function(frame) -> annotated_frame
                             Called on every processable frame.
        """
        while self.is_opened:
            frame, small, should_process = self.read_processing_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            display = frame
            if should_process and process_callback:
                display = process_callback(frame, small)

            _, buffer = cv2.imencode(".jpg", display, [cv2.IMWRITE_JPEG_QUALITY, 70])
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )

        logger.info("MJPEG stream ended")
