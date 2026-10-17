
import cv2
import numpy as np
from pathlib import Path
import traceback

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DETECTION_MODEL = (
    PROJECT_ROOT / "models" / "face_detection_yunet_2023mar.onnx"
)

RECOGNITION_MODEL = (
    PROJECT_ROOT / "models" / "face_recognition_sface_2021dec.onnx"
)


def create_models():
    if not DETECTION_MODEL.is_file():
        raise FileNotFoundError(
            f"Face detection model not found: {DETECTION_MODEL}"
        )

    if not RECOGNITION_MODEL.is_file():
        raise FileNotFoundError(
            f"Face recognition model not found: {RECOGNITION_MODEL}"
        )

    detector = cv2.FaceDetectorYN.create(
        str(DETECTION_MODEL),
        "",
        (320, 320),
        0.8,
        0.3,
        5000,
    )

    recognizer = cv2.FaceRecognizerSF.create(
        str(RECOGNITION_MODEL),
        "",
    )

    print("YuNet face detector loaded.")
    print("Standard SFace model loaded.")

    return detector, recognizer


def capture_face_embedding():
    detector, recognizer = create_models()

    # Try the Windows camera backend first, then the default backend.
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        camera.release()
        raise RuntimeError(
            "Could not open the webcam. Check Windows camera permissions "
            "and close other applications using the camera."
        )

    captured_embedding = None
    window_name = "FaceVault - Face Registration Test"

    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        print("Click the FaceVault camera window.")
        print("Press C to capture your face.")
        print("Press Q or Esc to cancel.")

        while True:
            success, frame = camera.read()

            if not success or frame is None:
                raise RuntimeError("Could not read a webcam frame.")

            height, width = frame.shape[:2]
            detector.setInputSize((width, height))

            _, faces = detector.detect(frame)
            selected_face = None

            if faces is not None and len(faces) > 0:
                selected_face = max(
                    faces,
                    key=lambda face: float(face[2] * face[3]),
                )

                x, y, w, h = selected_face[:4].astype(int)

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2,
                )

                label = "Face detected - press C"
                color = (0, 255, 0)
            else:
                label = "No face detected - look at camera"
                color = (0, 0, 255)

            cv2.putText(
                frame,
                label,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2,
            )

            cv2.putText(
                frame,
                "C: Capture | Q / ESC: Cancel",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            cv2.imshow(window_name, frame)

            # Key presses are read from the OpenCV window.
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q"), 27):
                print("Face capture cancelled.")
                break

            if key in (ord("c"), ord("C")):
                if selected_face is None:
                    print("No face detected. Centre your face and try again.")
                    continue

                try:
                    aligned_face = recognizer.alignCrop(
                        frame,
                        selected_face,
                    )

                    if aligned_face is None or aligned_face.size == 0:
                        print("Face alignment failed. Try again.")
                        continue

                    embedding = recognizer.feature(aligned_face)

                    if embedding is None or embedding.size == 0:
                        print("Feature extraction failed. Try again.")
                        continue

                    embedding = np.asarray(
                        embedding,
                        dtype=np.float32,
                    ).reshape(-1)

                    if embedding.size != 128:
                        print(
                            f"Unexpected embedding size: {embedding.size}. "
                            "Expected 128. Try again."
                        )
                        continue

                    if not np.all(np.isfinite(embedding)):
                        print("Invalid face features. Try again.")
                        continue

                    captured_embedding = embedding.copy()
                    print("Face captured successfully.")
                    break

                except Exception as error:
                    print(
                        f"Face processing failed: "
                        f"{type(error).__name__}: {error}"
                    )
                    print("Camera remains open. Press C to try again.")

            # Stop if the user closes the preview using its X button.
            try:
                if cv2.getWindowProperty(
                    window_name, cv2.WND_PROP_VISIBLE
                ) < 1:
                    break
            except cv2.error:
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    return captured_embedding



def compare_face_embeddings(embedding_a, embedding_b):
    vector_a = np.asarray(
        embedding_a,
        dtype=np.float32,
    ).reshape(1, -1)

    vector_b = np.asarray(
        embedding_b,
        dtype=np.float32,
    ).reshape(1, -1)

    if vector_a.shape != vector_b.shape:
        raise ValueError(
            "Face feature vectors have different sizes."
        )

    detector, recognizer = create_models()

    score = recognizer.match(
        vector_a,
        vector_b,
        cv2.FaceRecognizerSF_FR_COSINE,
    )

    return float(score)


def test_face_recognition():
    try:
        print("FIRST CAPTURE")
        first = capture_face_embedding()

        if first is None:
            print("First capture cancelled or unsuccessful.")
            return

        print("\nSECOND CAPTURE")
        second = capture_face_embedding()

        if second is None:
            print("Second capture cancelled or unsuccessful.")
            return

        score = compare_face_embeddings(first, second)

        print("\nComparison completed.")
        print(f"Cosine similarity: {score:.4f}")
        print("This is a test, not secure identity verification.")

    except Exception as error:
        print("\nFaceVault error:", error)
        traceback.print_exc()


if __name__ == "__main__":
    test_face_recognition()
