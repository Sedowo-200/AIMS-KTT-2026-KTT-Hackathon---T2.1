# T2.1 - Compressed Crop Disease Classifier
**AIMS KTT Hackathon - Tier 2**
**Candidate :** Jerome TEYI
**Domaine :** AgriTech • Computer Vision • Quantization • Serving
---

## USSD Fallback Workflow

This fallback is designed for farmers who do not have reliable 4G internet or a smartphone. Since USSD cannot transmit images directly, the workflow uses a local relay point such as an agricultural extension officer, cooperative kiosk, or village agent.

## Three-Step Flow

1. **Image capture and local upload**

   The farmer visits a cooperative kiosk or extension officer with a diseased crop leaf. The agent captures the leaf image using a smartphone or kiosk camera and uploads it to the local edge device or local server. The system stores the image and creates a short image ID, for example `IMG-0421`.

2. **USSD request**

   The farmer or agent dials a USSD code such as:

   ```text
   *123*421#
   ```

   The USSD gateway sends the image ID to the local diagnosis server. The server maps the ID to the stored image and runs the INT8 `model.tflite` classifier locally on CPU.

3. **Text diagnosis response**

   The system returns a short SMS/USSD message with the predicted disease, confidence level, and practical next action. The response is text-only, low-bandwidth, and compatible with feature phones.

## Example Diagnosis Message

### Kinyarwanda

```text
Igisubizo: Indwara ishobora kuba ari maize_rust.
Icyizere: 89%.
Inama: Kuraho amababi yanduye cyane, wirinde gukwirakwiza ibisigazwa, kandi wegere umujyanama w'ubuhinzi ku muti ukwiye.
```

### French

```text
Diagnostic : la feuille semble atteinte de maize_rust.
Confiance : 89%.
Conseil : retirer les feuilles très infectées, éviter de disperser les résidus, et consulter un agent agricole pour le traitement adapté.
```

## Edge Computing Rationale

The INT8 TFLite model is small enough to run on a cooperative laptop, kiosk device, or low-power CPU server. This reduces dependence on cloud connectivity and keeps inference available even when internet access is intermittent.

## Low-Confidence Escalation

If confidence is below 60%, the system should send:

```text
Low confidence. Please take a second photo in daylight, closer to the leaf, and contact the extension officer if symptoms persist.
```

## Unit Economics

For 1,000 farmers, the cooperative can run a weekly kiosk diagnosis day using one shared smartphone and one local CPU device. If the setup cost is amortized over many diagnosis sessions, the cost per diagnosis becomes mainly staff time, electricity, and device maintenance. This is more accessible than requiring every farmer to own a smartphone with mobile data.
