# T2.1 - Compressed Crop Disease Classifier
**AIMS KTT Hackathon - Tier 2**
**Candidate :** Jerome TEYI
**Domaine :** AgriTech • Computer Vision • Quantization • Serving
---

## Model Card

## Model Overview

This model classifies crop leaf images into five classes: `healthy`, `maize_rust`, `maize_blight`, `cassava_mosaic`, and `bean_spot`. It is designed for low-power CPU inference and edge deployment.

## Architecture

- Backbone: MobileNetV3-Small
- Width multiplier: `alpha=0.75`
- Input size: `224x224x3`
- Head: GlobalAveragePooling2D, light Dropout, Softmax output
- Number of classes: 5

## Quantization

- Format: TensorFlow Lite
- Quantization: Full Integer INT8
- Representative data: validation split
- Input tensor type: INT8
- Output tensor type: INT8
- Final model size: 0.79 MB

## Training Data

The training dataset is a compact five-class plant disease subset generated from public sources and prepared as `data/mini_plant_set`. Each class is capped at 300 images and split into train, validation, and test folders using an 80/10/10 split.

## Evaluation

| Model / Dataset | Accuracy | Macro-F1 |
|---|---:|---:|
| Keras deployment graph / clean test | 0.9733 | Not recorded |
| INT8 TFLite / clean test | 0.6733 | 0.6664 |
| INT8 TFLite / field-noisy test | 0.6167 | 0.5710 |

The INT8 model is highly compact and suitable for low-resource deployment, but quantization caused a significant accuracy drop compared with the float32 Keras graph. Further fine-tuning or quantization-aware training is recommended before high-stakes agricultural use.

## Intended Use

The model is intended for prototype crop disease screening in a hackathon setting. It can support extension officers, cooperative kiosks, and local field agents by providing a quick first-pass diagnosis.

## Limitations

- The model should not be used as the only basis for treatment decisions.
- It is trained only for the five listed classes and may fail on other crops or diseases.
- Night images, blurry images, occluded leaves, and very unusual lighting can reduce reliability.
- The current INT8 model does not yet meet the target of at least 80% Macro-F1 on the clean test split.

## Ethical and Operational Notes

Predictions should be shown with confidence scores and reviewed by an agricultural extension officer when possible. For low-confidence predictions, the system should request a second image from another angle or escalate the case to a human expert.
