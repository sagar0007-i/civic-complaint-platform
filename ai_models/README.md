# AI Models & Weights Directory

Place your trained YOLO weights in this directory.

### Expected File:
- **`pothole_yolo.pt`** (or `pothole_yolo.onnx`): Trained YOLO pothole detector weights exported from Google Colab.

### How to add:
1. Download `best.pt` from your Colab notebook (`/content/runs/detect/train/weights/best.pt`).
2. Rename it to `pothole_yolo.pt`.
3. Save it in this directory (`civic-complaint-platform/ai_models/pothole_yolo.pt`).

*Note: The platform includes an intelligent graceful fallback so it continues to function seamlessly even if weights are not yet downloaded.*
