# T2.1 - Compressed Crop Disease Classifier
**AIMS KTT Hackathon - Tier 2**
**Candidate :** Jerome TEYI
**Domaine :** AgriTech • Computer Vision • Quantization • Serving
---

CPU-first crop disease classifier for the AIMS KTT Hackathon. The project delivers a compact INT8 TensorFlow Lite model, a FastAPI `/predict` service, Docker serving instructions, and a low-bandwidth USSD fallback workflow for rural access.

## Official File Placement

- `README.md`: project overview and reproduction guide.
- `LICENSE`: MIT license.
- `process_log.md`: timeline, tools, prompts, and technical decisions.
- `SIGNED.md`: honor-code declaration.
- `ussd_fallback.md`: offline and feature-phone fallback workflow.
- `DOCKER_INSTRUCTIONS.md`: Docker build, run, health-check, and prediction commands.
- `VIDEO_SCRIPT_AND_QA.txt`: 4-minute video script and answers to required oral questions.
- `requirements.txt`: single dependency file for training, quantization, notebook execution, and API serving.
- `model.tflite`: final INT8 TensorFlow Lite model at project root.
- `notebooks/training_quantization.ipynb`: model training, evaluation, and full-integer quantization.
- `scripts/generate_synthetic_data.py`: official dataset synthesis script.
- `scripts/train.py`: notebook execution helper.
- `scripts/export_int8.py`: exported TFLite artifact size checker.
- `data/mini_plant_set/`: 80/10/10 resized dataset.
- `data/test_field/`: degraded field-style robustness images.
- `service/app.py`: FastAPI inference service exposing `/predict`.
- `service/Dockerfile`: lightweight Docker image based on `python:3.9-slim`.
- `service/examples/predict_example.sh`: one-command curl test.
- `samples/maize_rust_1.jpg`: sample image for API testing.
- `docs/model_card.md`: model card with architecture, quantization, metrics, and limitations.
- `docs/video_notes.md`: video structure notes and pointer to the full script.

## Reproduction on Free Colab CPU

Before running, accept the Kaggle competition rules for Cassava Leaf Disease Classification and provide Kaggle credentials if your Colab session requires them.

```bash
!git clone <REPO_URL> crop-disease && cd crop-disease && pip -q install -r requirements.txt
!cd crop-disease && python scripts/generate_synthetic_data.py && python scripts/train.py
```

The notebook trains the model, exports `model.tflite`, reports model size, and evaluates Macro-F1 on both `data/mini_plant_set/test` and `data/test_field`.

## Data Sources

Prepared ZIP archives used for this submission are available on Google Drive:

- Google Drive dataset folder: https://drive.google.com/drive/folders/1IbMUu_9IUemeeUnQCb14lYlvPZsr866j?usp=sharing

The dataset is synthesized from public crop disease image sources:

- Cassava Leaf Disease Classification: https://www.kaggle.com/competitions/cassava-leaf-disease-classification/data
- Bean Disease Dataset: https://www.kaggle.com/datasets/therealoise/bean-disease-dataset
- PlantVillage maize subset extracted from `abdallahalidev/plantvillage-dataset` with `kagglehub`.

## Dataset

The official five-class task uses:

- `healthy`
- `maize_rust`
- `maize_blight`
- `cassava_mosaic`
- `bean_spot`

`scripts/generate_synthetic_data.py` caps each class at 300 images, resizes to `224x224`, creates an 80/10/10 split, and builds `data/test_field` with blur, noise, JPEG compression, and brightness jitter.

## Architecture and Quantization

The model uses MobileNetV3-Small pretrained on ImageNet with `alpha=0.75` for a compact mobile-friendly backbone. The training graph includes `RandomFlip("horizontal")`, `RandomRotation(0.1)`, and in-graph rescaling with `Rescaling(1/127.5, offset=-1)`. The deployment graph removes random augmentation and uses a lightweight head: `GlobalAveragePooling2D -> Dropout(0.2) -> Softmax(5)`.

The final export is full-integer INT8 TensorFlow Lite using a validation representative dataset. TFLite input and output tensors are forced to INT8. The final `model.tflite` size is approximately `0.79 MB`, below the 10 MB requirement.

## Evaluation

Recorded results:

| Model / Dataset | Accuracy | Macro-F1 |
|---|---:|---:|
| Keras deployment graph / clean test | 0.9733 | Not recorded |
| INT8 TFLite / clean test | 0.6733 | 0.6664 |
| INT8 TFLite / field-noisy test | 0.6167 | 0.5710 |

The INT8 model satisfies the size and serving constraints, but the current quantized Macro-F1 does not yet meet the target of at least 80% on the clean split. The next technical improvement would be deeper fine-tuning and/or quantization-aware training to recover the post-quantization accuracy drop.

## Serving API

Run the FastAPI inference service from the project root:

```bash
python -m uvicorn service.app:app --host 0.0.0.0 --port 8000
```

Test the API with the included sample image:

```bash
curl -X POST "http://localhost:8000/predict" \
     -F "file=@samples/maize_rust_1.jpg"
```

The API returns:

```json
{
  "label": "maize_rust",
  "confidence": 0.89,
  "top3": [],
  "latency_ms": 45,
  "rationale": "Prediction generated by an INT8 MobileNetV3-Small model from the uploaded leaf image."
}
```

## Docker

Build and run the API container:

```bash
docker build -t crop-classifier -f service/Dockerfile .
docker run --rm -p 8000:8000 crop-classifier
```

Detailed Docker commands are in `DOCKER_INSTRUCTIONS.md`.

## USSD Fallback

The low-bandwidth design is documented in `ussd_fallback.md`. The workflow uses a cooperative kiosk, village agent, or extension officer as a relay: image capture happens locally, the farmer or agent sends a USSD image ID, the INT8 model runs on a local CPU device, and the diagnosis is returned by SMS/USSD.

## Video

4-minute demo video URL: `TODO_ADD_VIDEO_URL`

Video notes are in `docs/video_notes.md`, and the full spoken guide is in `VIDEO_SCRIPT_AND_QA.txt`.
