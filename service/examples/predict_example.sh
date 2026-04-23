#!/bin/bash
curl -X POST "http://localhost:8000/predict" \
     -F "file=@samples/maize_rust_1.jpg"
