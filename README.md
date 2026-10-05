# 🩺 AI Skin Specialist with Vision and Voice

An AI-powered web app where a patient **speaks** about a skin concern, **uploads a photo**, and receives a short AI-generated assessment as **text and a spoken voice reply**.

🔗 **Live demo:** https://ai-skin-specialist-4t4z.onrender.com/

> ⏳ The app is hosted on Render's free plan, so it sleeps when idle. The first visit after a while can take 30 to 60 seconds to wake up.

---

## ✨ Features

- 🎙 **Speech to Text:** record with the microphone or upload an audio file; it is transcribed automatically.
- 📷 **Image analysis:** upload or capture a skin photo that the vision model reviews together with the patient's description.
- 🎥 **Video input:** a video box is available in the UI, but the current vision model uses the image only.
- 🔊 **Text to Speech:** the doctor's reply is converted to a natural voice you can play in the browser.
- 🎨 **Modern black and white UI:** animated background, responsive layout (desktop, tablet and phone), live input indicators, loading states and error messages.

---

## 🔄 How it works

```
Patient voice ──► Speech to Text ──┐
                                   ├─► Vision + reasoning model ──► Doctor's text ──► Text to Speech ──► Doctor's voice
Patient image ─────────────────────┘
```

1. **Speech to Text:** the recording is sent to Whisper and returned as text.
2. **Brain of the doctor:** the text and the skin image go to a multimodal model, which writes a short, plain-language response.
3. **Voice of the doctor:** the response is converted to an mp3 and played back in the app.

---

## 🧰 Tech stack

| Area | Tool |
|---|---|
| Language | Python 3.12 |
| Web UI | [Gradio](https://www.gradio.app/) 6 (Blocks, custom CSS and animations) |
| Speech to Text | [Groq](https://groq.com/) API with OpenAI **Whisper large-v3** |
| Vision and reasoning | Groq API, multimodal model (default: `meta-llama/llama-4-scout-17b-16e-instruct`, configurable) |
| Text to Speech | [Deepgram](https://deepgram.com/) **Aura 2** voice (`aura-2-thalia-en`) |
| Image handling | Pillow (resized and compressed before sending) |
| Config and secrets | python-dotenv (`.env` locally, environment variables on Render) |
| Hosting | [Render](https://render.com/) (Web Service, free plan) |

---

## 📁 Project structure

```
├── main.py             # Speech to Text, vision model, Text to Speech, and the Gradio UI
├── requirements.txt    # Python dependencies
├── render.yaml         # Render deployment blueprint
├── .env.example        # Example environment variables
└── .gitignore          # Keeps .env and local files out of git
```

---

## ⚙️ Environment variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq key for Whisper and the vision model |
| `DEEPGRAM_API_KEY` | ✅ | Deepgram key for the doctor's voice |
| `GROQ_MODEL` | optional | Vision model name (default `meta-llama/llama-4-scout-17b-16e-instruct`) |
| `WHISPER_MODEL` | optional | Whisper model (default `whisper-large-v3`) |
| `DEEPGRAM_VOICE_MODEL` | optional | Voice model (default `aura-2-thalia-en`) |
| `PORT` | set by Render | Port the app listens on (default `7860` locally) |

Never commit your real keys. Copy `.env.example` to `.env` locally and fill it in.

---

## 💻 Run locally

```bash
# 1. Clone
git clone https://github.com/Atifkhan79/AI-SKIN-SPECIALIST.git
cd AI-SKIN-SPECIALIST

# 2. Create a virtual environment and install
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

# 3. Add your keys
copy .env.example .env          # then edit .env

# 4. Start
python main.py
```

Open http://localhost:7860.

---

## ☁️ Deploy on Render

1. Push this project to GitHub (without your `.env`).
2. On Render choose **New → Blueprint** (or **Web Service**) and select the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py`
5. Add `GROQ_API_KEY` and `DEEPGRAM_API_KEY` under **Environment**, then deploy.

---

## 📝 Notes and limitations

- An **image is required**; the current vision model does not read video.
- Audio is recorded in the browser, so the site must be opened over **HTTPS** (Render does this) for the microphone to work.
- Responses are intentionally short and written for speech (no markdown or symbols).

---

## ⚠️ Medical disclaimer

This project provides **general, AI-generated information only**. It is **not** a medical device and **not** a substitute for professional medical advice, diagnosis or treatment. Always consult a licensed dermatologist or doctor about any skin concern.

---

## 👤 Author

**Atif Khan**
