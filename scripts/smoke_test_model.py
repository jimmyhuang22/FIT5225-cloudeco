from pathlib import Path
import cv2
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent   # 回到项目根目录
MODEL_PATH = BASE_DIR / "models" / "best_model.pt"
IMAGE_PATH = BASE_DIR / "samples" / "image_phone.jpeg"
OUTPUT_PATH = BASE_DIR / "samples" / "image_phone_pred.jpg"

def main() -> None:
    print("MODEL_PATH =", MODEL_PATH)
    print("IMAGE_PATH =", IMAGE_PATH)

    model = YOLO(str(MODEL_PATH))
    print("model.names =", model.names)

    results = model.predict(
        source=str(IMAGE_PATH),
        device="cpu",
        verbose=False
    )

    r = results[0]
    print("detections =", len(r.boxes))
    print("speed(ms) =", r.speed)

    annotated = r.plot()
    cv2.imwrite(str(OUTPUT_PATH), annotated)
    print("saved =", OUTPUT_PATH.resolve())

if __name__ == "__main__":
    main()
