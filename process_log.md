# T2.1 - Compressed Crop Disease Classifier
**AIMS KTT Hackathon - Tier 2**
**Candidate :** Jerome TEYI
**Domaine :** AgriTech • Computer Vision • Quantization • Serving
---

## Process Log

| Time (UTC) | Tool | Prompt | Technical Decision |
|---|---|---|---|
| 2026-04-23 12:10:00 | Codex | Finalize README and complete remaining official deliverables. | Added `LICENSE`, `docs/video_notes.md`, `scripts/train.py`, and `scripts/export_int8.py`, then rewrote `README.md` to reflect the final tree, API commands, metrics, Docker, USSD fallback, and video guide. |
| 2026-04-23 12:05:00 | Codex | Create final video script and oral Q&A guide. | Added `VIDEO_SCRIPT_AND_QA.txt` with the required 4-minute video structure, screen-share cues, and spoken answers to the technical, business, and local-context questions. |
| 2026-04-23 12:00:00 | Codex | Add USSD fallback, sample image, curl script, and model card. | Created the African-context USSD fallback workflow, copied a maize rust sample image, added a one-command API test script, and documented model architecture, INT8 quantization, metrics, and limitations. |
| 2026-04-23 11:50:00 | Codex | Update README with FastAPI run command. | Added the required `python -m uvicorn service.app:app --host 0.0.0.0 --port 8000` command under a Serving API section. |
| 2026-04-23 11:45:00 | Codex | Check Software Engineering deliverables and add Docker instructions. | Added root-level `DOCKER_INSTRUCTIONS.md` with build, run, health-check, and `/predict` test commands for the FastAPI TFLite service. |
| 2026-04-23 11:40:00 | Codex | Centralize dependency management in root requirements file. | Moved service API dependencies into root `requirements.txt`, deleted `service/requirements.txt`, and updated Dockerfile to install from the root requirements file. |
| 2026-04-23 11:05:00 | Codex | Verify persistent Keras compile error and harden notebook cell. | Confirmed the previous compile fix was missing after notebook rewrite, added `deploy_model.compile(...)` in both model-build and evaluation cells, and cleared stale error outputs. |
| 2026-04-23 11:00:00 | Codex | Fix Keras deploy model evaluation error. | Added an explicit `deploy_model.compile(...)` step so the inference graph can be evaluated before TFLite export. |
| 2026-04-23 10:55:00 | Codex | Add Google Drive link for zipped source data to README. | Documented the shared Drive folder containing the prepared dataset ZIP archives used before synthetic dataset generation. |
| 2026-04-23 10:50:00 | Codex | Rewrite notebook for Edge ML audit improvements. | Rebuilt `notebooks/training_quantization.ipynb` with MobileNetV3Small `alpha=0.75`, a lightweight GAP-to-softmax head, strict class validation, train-time augmentation, deploy-time rescaling, full INT8 TFLite export, size check, and Macro-F1 reporting. |
| 2026-04-23 10:45:00 | Codex | Fix TFLite conversion failure: `NoneType` object is not callable. | Replaced direct `from_keras_model` conversion with SavedModel export plus `from_saved_model`, and switched checkpointing to best weights only to avoid unstable Keras reloads. |
| 2026-04-23 10:40:00 | Codex | Correct notebook path-resolution error. | Replaced single-parent path detection with an upward project-root search for `data/mini_plant_set`, preventing `notebooks/data/...` lookup failures. |
| 2026-04-23 10:36:00 | Codex | Fix notebook path error and switch to narrative Markdown comments. | Added project-root auto-detection for notebook execution from `notebooks/` and replaced curve commentary with a generated Markdown interpretation cell. |
| 2026-04-23 10:30:00 | Codex | Apply mandatory official Markdown header and create honor-code signature file. | Added the strict project header to maintained Markdown files and created `SIGNED.md` with the hackathon honor-code declaration. |
| 2026-04-23 10:16:16 | Codex | Audit Strict Word: initialize compliance for T2.1 compressed crop disease classifier. | Aligned deliverables to the official root-level tree, selected MobileNetV3-Small as the CPU-first backbone, and mandated full INT8 TFLite export with validation representative data. |
| 2026-04-23 10:18:00 | Codex | Enforce official Word project structure. | Moved the training notebook to `notebooks/training_quantization.ipynb` and the synthesis script to `scripts/generate_synthetic_data.py`. |
| 2026-04-23 10:20:00 | Codex | Update notebook quality standard. | Added titled training curves and a printed curve interpretation to the quantization notebook. |
| 2026-04-23 10:22:00 | Codex | Regenerate official dataset folders. | Generated `data/mini_plant_set` and `data/test_field` with 1,500 standard images and 60 robustness images. |
| 2026-04-23 10:24:00 | Codex | Initialize README and dependency list. | Added reproduction instructions, data-source documentation, INT8 MobileNetV3-Small architecture notes, and runtime dependencies. |
