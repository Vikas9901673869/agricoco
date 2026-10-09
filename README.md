# 🌴 Coconut & Palm Health Diagnostic AI (agricoco)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Computer Vision](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF.svg)](https://docs.ultralytics.com/)
[![Architecture](https://img.shields.io/badge/RAG-Hybrid%20Knowledge%20Pipeline-success.svg)](#-retrieval-augmented-generation-rag-architecture)
[![LLM](https://img.shields.io/badge/LLM-Google%20Gemini%201.5%20Flash-orange.svg)](https://deepmind.google/technologies/gemini/)

An end-to-end intelligent agro-diagnostic system combining **real-time computer vision (Ultralytics YOLOv8)** with a **domain-specific RAG (Retrieval-Augmented Generation) advisory model**. The system grounds generative AI responses in verified **ICAR-CPCRI** horticultural standards to deliver hallucination-free chemical treatments, live farm weather telemetry, an automated dosage calculator, and trilingual voice assistance (**English**, **ಕನ್ನಡ**, and **ತುಳು**).

---

## 🧠 Retrieval-Augmented Generation (RAG) Architecture

Standard LLMs frequently hallucinate chemical formulations, which can lead to crop burn (phytotoxicity) or ineffective disease management. **agricoco implements a strict domain-grounded RAG pipeline**:

```text
       [ YOLOv8 Visual Diagnosis ]
                   │ (Class Key: e.g., "bud rot")
                   ▼
┌─────────────────────────────────────────────────────┐
│ 1. RETRIEVAL LAYER                                  │
│    Queries structured ICAR-CPCRI agronomy corpus:   │
│    - Pathogen etiology & fungal triggers            │
│    - Chemical active ingredients & safe concentrations│
│    - Application intervals & organic biocontrols    │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ 2. AUGMENTATION LAYER                               │
│    Constructs a constrained, localized prompt:      │
│    - Grounds LLM strictly on retrieved facts        │
│    - Injects regional context & selected language   │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ 3. GENERATION LAYER (Gemini 1.5 Flash)              │
│    Synthesizes concise, actionable advice in        │
│    plain farmer terminology (<40 words)             │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ 4. MULTILINGUAL AUDIO SYNTHESIS                     │
│    Voice readout in English, Kannada, or Tulu       │
└─────────────────────────────────────────────────────┘