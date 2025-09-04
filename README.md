# [Presentation Slides](https://docs.google.com/presentation/d/14ZhKQd_uRxixMc3ZrCBNsQ293BQTgOte0IkRgQK1ebs/edit?slide=id.SLIDES_API246794049_0#slide=id.SLIDES_API246794049_0) | Enginuity AI – Engineering Notes Assistant

Enginuity AI is an **AI-powered platform** that transforms engineering lectures into **structured, accessible study notes**. Students can upload lecture audio, slides, or PDFs, and Enginuity generates transcripts, organizes content into concepts, formulas, and code snippets, provides smart search and quizzes, and even offers a chatbot that answers questions from your lecture data.

---

## Project Overview

The system follows these main steps:

1. **Lecture Ingestion** – Upload audio (lectures/tutorials), PDFs, or PowerPoint slides.
2. **Transcription & Extraction** – Convert speech to text (Whisper) and extract slide/PDF text.
3. **Structuring** – Split content into sections; label as concepts, definitions, formulas, code snippets, or examples.
4. **Formula & Code Recognition** – Parse LaTeX/MathML formulas and highlight code snippets with syntax coloring.
5. **Vector Store & Embeddings** – Generate embeddings for lecture chunks and index them in Chroma for semantic search.
6. **Accessible Study Outputs** – View notes in a clean web UI, with text-to-speech, font/contrast settings, and export to PDF, Word, LaTeX, or Anki.
7. **Quiz Generation** – Auto-generate multiple-choice and fill-in-the-blank questions to reinforce learning.
8. **Chatbot (RAG)** – Ask questions, and the system answers using only your lecture notes, citing sources.

---

## Project Structure

```
enginuity-ai/
├── app/                    # Streamlit app pages
│   ├── 00_Home.py          # Landing page & settings
│   ├── 10_Upload.py        # File upload & ingestion
│   ├── 30_Notes.py         # Notes viewer with TTS
│   ├── 40_Search.py        # Keyword + semantic search
│   ├── 50_Quiz.py          # Quiz generation & export
│   └── 60_Chat.py          # Chatbot (RAG)
│
├── core/                   # Backend logic (pure Python modules)
│   ├── ingest/             # Audio, PDF, PPT processing
│   ├── structure/          # Chunking & labeling
│   ├── vector/             # Embedding & index helpers
│   ├── export/             # Exporters: md, pdf, docx, anki
│   ├── qa/                 # Quiz generator
│   └── chat/               # RAG chatbot logic
│
├── data/                   # Uploaded files, processed outputs, indexes (gitignored)
├── requirements.txt        # Python dependencies
├── README.md               # Project overview
└── .gitignore              # Ignore venv, caches, data/
```

---

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Core libraries used:

* **Streamlit** – UI framework
* **faster-whisper** – Speech-to-text
* **PyMuPDF / python-pptx** – PDF/slide text extraction
* **Chroma / FAISS** – Vector store for search & chatbot
* **sentence-transformers** – Embeddings
* **SymPy / Mathpix API** – Formula parsing & recognition
* **pygments** – Code snippet highlighting
* **WeasyPrint / python-docx / genanki** – Export (PDF, Word, Anki)
* **edge-tts** – Text-to-speech

---

## How to Run

1. Clone the repo and install requirements:

   ```bash
   git clone https://github.com/YourUsername/enginuity-ai.git
   cd enginuity-ai
   pip install -r requirements.txt
   ```

2. Run the Streamlit app:

   ```bash
   streamlit run app/00_Home.py
   ```

3. Open in browser → upload a lecture PDF/audio/slide and explore notes, search, quiz, and chat features.

---

## Workflow

### 1. Ingestion

* Audio → Whisper STT
* PDFs/PPTs → PyMuPDF/python-pptx

### 2. Structuring

* Chunk & label text (Concept, Definition, Formula, Code, Example)
* Summarize sections

### 3. Vector Store

* Embeddings → Chroma index for retrieval & chatbot

### 4. Outputs

* Notes viewer with TTS + accessibility settings
* Export to PDF/DOCX/LaTeX/Anki

### 5. Enrichment

* Auto-generated quizzes
* RAG chatbot answering from notes

---

## Example Inputs

* 📄 Lecture slides (PDF)
* 🎙️ Recorded lecture audio (MP3/WAV)
* 📝 Annotated notes

---

## Future Work

* Real-time lecture capture (Zoom/microphone).
* Deeper formula OCR with Mathpix/Nougat.
* Cross-lecture search and study packs.
* Advanced quiz generation with difficulty levels.

---


