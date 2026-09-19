# 🔍 Digital Image Forensic Analyzer

A web-based digital image forensic analysis application built with **Python, Flask, Pillow, OpenCV, NumPy, and ReportLab**.

The application analyzes uploaded images using multiple forensic techniques and generates a combined **Forensic Indicator Score** along with a downloadable PDF forensic analysis report.

> **Disclaimer:** This application is intended for educational and academic purposes. Its forensic indicator score is a rule-based heuristic and is not proof that an image has been manipulated. Results should not be treated as conclusive forensic evidence.

---

## 📌 Project Overview

Digital images can contain useful information about their origin, processing history, and possible inconsistencies.

The **Digital Image Forensic Analyzer** provides a web-based interface where users can upload an image and perform multiple forensic analyses from a single dashboard.

The application analyzes:

- Image metadata / EXIF information
- Error Level Analysis (ELA)
- Image noise characteristics
- Image statistics
- RGB and grayscale histograms
- Potentially inconsistent image regions
- Combined forensic indicators

The application can also generate a structured **PDF Forensic Analysis Report** containing the analysis results and visualizations.

---

## 🎯 Objectives

The main objectives of this project are:

1. Analyze digital images using multiple forensic techniques.
2. Extract and display available EXIF metadata.
3. Perform Error Level Analysis to identify areas responding differently to JPEG recompression.
4. Analyze image noise characteristics.
5. Calculate statistical properties of an image.
6. Generate RGB and grayscale histograms.
7. Detect potentially inconsistent regions using heuristic analysis.
8. Combine multiple analysis results into a forensic indicator score.
9. Generate a professional PDF report containing the analysis results.
10. Provide a simple and user-friendly web interface.

---

## ✨ Features

### 🖼️ Image Upload

Supports the following image formats:

- JPG
- JPEG
- PNG
- BMP
- WEBP

Maximum upload size:

```text
10 MB
