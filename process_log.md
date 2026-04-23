# T2.1 - Compressed Crop Disease Classifier
**AIMS KTT Hackathon - Tier 2**
**Candidate :** Jerome TEYI
**Domaine :** AgriTech • Computer Vision • Quantization • Serving
---

## Process Log

This log summarizes my candidate-led workflow. I used ChatGPT as a coding and review assistant to accelerate implementation, check compliance, debug errors, and improve documentation, while I made the final architecture, dataset, deployment, and reporting decisions.

| Time (UTC) | Candidate Work | ChatGPT Prompt / Support Used | Final Decision |
|---|---|---|---|
| 2026-04-23 09:40 | Prepared the local crop-disease sources and selected the 5 target classes. | Asked ChatGPT to help design a reproducible data synthesis script from my local folders. | Kept the official classes: `healthy`, `maize_rust`, `maize_blight`, `cassava_mosaic`, `bean_spot`. |
| 2026-04-23 09:55 | Built the official mini dataset and robustness folder. | Prompted for an 80/10/10 split, `224x224` resizing, max 300 images per class, and degraded field images. | Generated `data/mini_plant_set`, `data/test_field`, and ZIP archives. |
| 2026-04-23 10:20 | Organized the project according to the T2.1 brief. | Asked for an audit against the required Word/PDF tree. | Moved the notebook into `notebooks/` and the data generator into `scripts/`. |
| 2026-04-23 10:35 | Trained and debugged the MobileNetV3 notebook. | Used ChatGPT to diagnose path issues, Keras compile errors, and TFLite conversion failures. | Kept separate training and deployment graphs so augmentation is used for training but not exported into inference. |
| 2026-04-23 10:50 | Improved the edge model after audit. | Asked for Edge ML improvements: `alpha=0.75`, lighter head, strict class validation, augmentation, and full INT8 conversion. | Chose MobileNetV3-Small `alpha=0.75` with `GlobalAveragePooling2D -> Dropout -> Softmax`. |
| 2026-04-23 11:15 | Evaluated the final exported model. | Asked ChatGPT to help interpret the Keras and TFLite results. | Reported model size `0.79 MB`, clean INT8 Macro-F1 `0.6664`, and field INT8 Macro-F1 `0.5710`. |
| 2026-04-23 11:35 | Built the serving layer. | Prompted for a production-style FastAPI service using TFLite inference and Docker. | Created `/predict`, `service/Dockerfile`, and a single root `requirements.txt`. |
| 2026-04-23 11:50 | Added software-engineering delivery files. | Asked ChatGPT to compare the repo against the software-engineering deliverables. | Added `DOCKER_INSTRUCTIONS.md`, `service/examples/predict_example.sh`, and `samples/maize_rust_1.jpg`. |
| 2026-04-23 12:00 | Added local-context and model documentation. | Prompted for an African-context USSD fallback and model-card structure. | Added `ussd_fallback.md`, `docs/model_card.md`, and `docs/video_notes.md`. |
| 2026-04-23 12:10 | Prepared the video defense. | Asked ChatGPT to draft concise speaking notes for the 4-minute structure and required questions. | Created `VIDEO_SCRIPT_AND_QA.txt` with my numbers, demo commands, and oral-answer guide. |
| 2026-04-23 12:20 | Final README cleanup and compliance check. | Asked for README updates and final deliverable verification. | README now documents data sources, architecture, metrics, API, Docker, USSD fallback, and remaining video URL placeholder. |

## Sample Prompts Used

1. "Create a data synthesis script to generate the official hackathon dataset from my local folders, with 80/10/10 split, 224x224 resizing, max 300 images per class, and a degraded test_field set."

2. "As an Edge ML expert, rewrite my notebook using MobileNetV3-Small alpha=0.75, a lightweight classifier head, data augmentation, strict INT8 TFLite quantization, and Macro-F1 reporting."

3. "Senior Backend Engineer and MLOps: write service/app.py, Dockerfile, and API instructions for a FastAPI /predict endpoint using model.tflite."

## Discarded Prompt

I considered asking ChatGPT to simply maximize model accuracy with a larger architecture, but I discarded that direction because it conflicted with the edge-computing constraint. The brief prioritizes a compact model under 10 MB, low-latency CPU inference, and a deployable service, so I kept MobileNetV3-Small and INT8 quantization even though the quantized Macro-F1 still needs improvement.

## Hardest Decision

The hardest decision was balancing model performance against deployment constraints. The float32 Keras deployment graph reached strong clean-test accuracy, but the INT8 TFLite model dropped to `0.6664` Macro-F1 on the clean test split. I decided to keep the INT8 artifact because the challenge is explicitly about compressed edge deployment, and the final model is only `0.79 MB`. My next technical step would be quantization-aware training or deeper fine-tuning to recover accuracy while preserving the small model size.
