import base64
import logging
import os
import tempfile
import uuid
from io import BytesIO

import gradio as gr
from dotenv import load_dotenv
from groq import Groq
from PIL import Image

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# =========================================================
# Step 1: Speech to Text  (from voice_of_the_patient.py)
# =========================================================
def transcribe_patient_voice(audio_file_path):
    groq_api_key = os.environ.get("GROQ_API_KEY")

    client = Groq(api_key=groq_api_key)

    with open(audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model=os.environ.get("WHISPER_MODEL", "whisper-large-v3")
        )

    return transcription.text


# =========================================================
# Step 2: Brain of the Doctor  (from brain_of_the_doctor_groq.py)
# =========================================================
def encode_image_for_groq(filepath):
    image = Image.open(filepath)
    image.thumbnail((1024, 1024))

    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def brain_of_the_doctor(patient_text, image_filepath=None, video_filepath=None):
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("Missing GROQ_API_KEY in .env or environment")

    if not image_filepath:
        raise ValueError("Groq vision requires an image. Please upload a skin image.")

    # Groq vision does not accept video here. When main.py passes both image and
    # video, this uses the same image as the visual input and ignores the video.
    image_data = encode_image_for_groq(image_filepath)

    prompt = (
        "You are a confident, natural doctor specializing in skin care. Speak with the reassurance, clarity, and authority of a real doctor. "
        "Limit your entire response to two or three sentences maximum. "
        "If the patient has provided a video, explain that you are reviewing the uploaded image because this model cannot process video directly. "
        "Do not use any special characters, symbols, asterisks, or markdown formatting in your response because it will be converted directly to audio.\n\n"
        f"Patient text: {patient_text}"
    )

    if video_filepath:
        prompt += "\nThe patient also uploaded a video, but use the provided image as the visual reference."

    client = Groq(api_key=groq_api_key)
    response = client.chat.completions.create(
        model=os.environ.get("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"),
        max_completion_tokens=1000,
        messages=[
            {
                "role": "system",
                "content": "You are a careful skin care assistant. Give general information, not a diagnosis.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}",
                        },
                    },
                ],
            },
        ],
    )

    return response.choices[0].message.content


# =========================================================
# Step 3: Voice of the Doctor  (from voice_of_the_doctor.py)
# =========================================================
def convert_text_to_doctor_audio(text):
    from deepgram import DeepgramClient

    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY not found in .env")

    deepgram = DeepgramClient(api_key=api_key)

    audio = deepgram.speak.v1.audio.generate(
        text=text,
        model=os.environ.get("DEEPGRAM_VOICE_MODEL", "aura-2-thalia-en"),
        encoding="mp3"
    )

    # Unique file per request so simultaneous users don't overwrite each other
    audio_path = os.path.join(tempfile.gettempdir(), f"doctor_response_{uuid.uuid4().hex}.mp3")

    with open(audio_path, "wb") as file:
        for chunk in audio:
            file.write(chunk)

    return audio_path


def play_audio(audio_path):
    # Local playback only works on Windows desktops with a display.
    # Safe to skip when running on a server (e.g. Render).
    if os.name == "nt":
        os.startfile(audio_path)


# =========================================================
# Step 4: Logic + UI  (from main.py)
# =========================================================
# =========================================================
# Step 4: Logic + UI  (from main.py)
# Paste this over your old Step 4. Everything above it
# (imports, transcribe_patient_voice, brain_of_the_doctor,
# convert_text_to_doctor_audio, play_audio) stays unchanged.
# =========================================================
import os
import gradio as gr


# ---------------------------------------------------------
# YOUR ORIGINAL LOGIC  (unchanged)
# ---------------------------------------------------------
def process_inputs(audio_filepath, image_filepath, video_filepath):

    # User will ask Questions in audio and this audio will be converted to text
    patient_text = transcribe_patient_voice(audio_filepath)

    # this + users image/video be sent to brain of the doctor and brain of the doctor will respond in text
    doctor_text = brain_of_the_doctor(
        patient_text=patient_text,
        image_filepath=image_filepath,
        video_filepath=video_filepath
    )

    # we will convert this text response from the doctor to audio response
    doctor_audio = convert_text_to_doctor_audio(doctor_text)

    # play audio for the patient
    play_audio(doctor_audio)
    return patient_text, doctor_text, str(doctor_audio)


# ============================ CSS ==============================
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #ffffff;
    --bg-soft: #f4f4f5;
    --ink: #0a0a0a;
    --ink-soft: #404040;
    --line: #e4e4e7;
    --radius: 20px;
    --shadow: 6px 6px 0 var(--ink);
    --shadow-hover: 10px 10px 0 var(--ink);
}

html { scroll-behavior: smooth; }
::selection { background: var(--ink); color: #fff; }

body, .dark body {
    background: #fafafa !important;
    color: var(--ink) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}
.gradio-container, .dark .gradio-container {
    background: transparent !important;
    max-width: 1240px !important;
    margin: 0 auto !important;
    padding: clamp(12px, 3vw, 32px) !important;
    color: var(--ink) !important;
    position: relative; z-index: 1;
}

/* ========== ANIMATED BACKGROUND ========== */
#bg {
    position: fixed; inset: 0; z-index: 0;
    pointer-events: none; overflow: hidden;
    background: linear-gradient(135deg, #ffffff 0%, #f4f4f5 50%, #ffffff 100%);
    background-size: 300% 300%;
    animation: bgShift 18s ease infinite;
}
#bg .grid {
    position: absolute; inset: -50%;
    background-image:
        linear-gradient(rgba(0,0,0,.07) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,.07) 1px, transparent 1px);
    background-size: 44px 44px;
    transform: perspective(700px) rotateX(55deg) translateY(0);
    transform-origin: center top;
    animation: gridMove 12s linear infinite;
    -webkit-mask-image: radial-gradient(ellipse at center top, #000 10%, transparent 70%);
            mask-image: radial-gradient(ellipse at center top, #000 10%, transparent 70%);
}
#bg .orb {
    position: absolute; border-radius: 50%;
    filter: blur(70px); opacity: .22;
    background: #000;
    will-change: transform;
}
#bg .o1 { width: 420px; height: 420px; top: -120px; left: -100px; animation: drift1 20s ease-in-out infinite; }
#bg .o2 { width: 360px; height: 360px; bottom: -120px; right: -80px; background:#525252; animation: drift2 24s ease-in-out infinite; }
#bg .o3 { width: 260px; height: 260px; top: 45%; left: 55%; background:#a3a3a3; opacity:.28; animation: drift3 28s ease-in-out infinite; }
#bg .ring {
    position: absolute; border: 1.5px solid rgba(0,0,0,.12); border-radius: 50%;
    top: 20%; right: 8%; width: 220px; height: 220px;
    animation: spin 40s linear infinite;
}
#bg .ring::after {
    content: ""; position: absolute; top: -5px; left: 50%;
    width: 10px; height: 10px; border-radius: 50%; background: var(--ink);
}
#bg .ring.r2 { top: auto; right: auto; bottom: 12%; left: 6%; width: 150px; height: 150px; animation-direction: reverse; animation-duration: 30s; }

@keyframes bgShift { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
@keyframes gridMove { from{background-position:0 0} to{background-position:0 44px} }
@keyframes drift1 { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(160px,120px) scale(1.2)} }
@keyframes drift2 { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(-180px,-100px) scale(1.15)} }
@keyframes drift3 { 0%,100%{transform:translate(0,0)} 33%{transform:translate(-120px,80px)} 66%{transform:translate(90px,-90px)} }
@keyframes spin { to { transform: rotate(360deg); } }

/* ========== GENERAL ANIMATIONS ========== */
@keyframes fadeUp { from{opacity:0;transform:translateY(26px)} to{opacity:1;transform:translateY(0)} }
@keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
@keyframes pulseDot { 0%,100%{box-shadow:0 0 0 0 rgba(255,255,255,.7)} 50%{box-shadow:0 0 0 8px rgba(255,255,255,0)} }
@keyframes floatY { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.35} }
@keyframes stripes { from{background-position:0 0} to{background-position:40px 0} }

/* ========== HERO ========== */
#hero {
    background: #0a0a0a; color: #fff !important;
    border-radius: 26px; padding: clamp(26px, 5vw, 52px) clamp(20px, 4vw, 44px);
    margin-bottom: 26px; position: relative; overflow: hidden;
    animation: fadeUp .8s ease both;
    box-shadow: 0 24px 60px rgba(0,0,0,.25);
}
#hero::after {
    content:""; position:absolute; inset:0;
    background: linear-gradient(110deg, transparent 30%, rgba(255,255,255,.12) 50%, transparent 70%);
    background-size: 200% 100%; animation: shimmer 5s linear infinite; pointer-events:none;
}
#hero h1 { color:#fff !important; font-size: clamp(1.8rem, 5vw, 2.8rem); font-weight:800; margin:0 0 10px; letter-spacing:-.02em; }
#hero p  { color:#d4d4d8 !important; font-size: clamp(.95rem, 2vw, 1.08rem); margin:0; max-width:640px; line-height:1.65; }
#hero .badge {
    display:inline-flex; align-items:center; gap:8px; border:1px solid #52525b; border-radius:999px;
    padding:6px 14px; font-size:.8rem; color:#fff !important; margin-bottom:18px; background:rgba(255,255,255,.07);
}
#hero .dot { width:8px; height:8px; border-radius:50%; background:#fff; animation: pulseDot 2s infinite; }
#hero .features { display:flex; gap:10px; margin-top:24px; flex-wrap:wrap; }
#hero .chip {
    background:#fff; color:#0a0a0a !important; font-weight:600; padding:8px 16px; border-radius:999px; font-size:.85rem;
    transition: transform .25s ease, background .25s ease; animation: floatY 4s ease-in-out infinite;
}
#hero .chip:nth-child(2){animation-delay:.4s} #hero .chip:nth-child(3){animation-delay:.8s}
#hero .chip:hover { transform: translateY(-4px) scale(1.06); background:#e4e4e7; }

/* ========== STEPS BAR ========== */
#steps { display:flex; gap:10px; margin: 0 0 22px; animation: fadeUp .8s ease .1s both; flex-wrap:wrap; }
#steps .step {
    flex:1; min-width:150px; display:flex; align-items:center; gap:12px;
    background: rgba(255,255,255,.85); backdrop-filter: blur(10px);
    border:1.5px solid var(--ink); border-radius:14px; padding:12px 16px;
    color: var(--ink) !important; font-weight:600; font-size:.92rem;
    transition: transform .25s ease, background .25s ease, color .25s ease;
}
#steps .step:hover { transform: translateY(-3px); background: var(--ink); color:#fff !important; }
#steps .num {
    width:28px; height:28px; border-radius:50%; background:var(--ink); color:#fff !important;
    display:grid; place-items:center; font-size:.85rem; flex-shrink:0; transition: all .25s;
}
#steps .step:hover .num { background:#fff; color:var(--ink) !important; }

/* ========== CARDS (glass + hard shadow) ========== */
.card {
    background: rgba(255,255,255,.88) !important;
    backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
    border: 1.5px solid var(--ink) !important;
    border-radius: var(--radius) !important;
    padding: clamp(14px, 2.5vw, 24px) !important;
    box-shadow: var(--shadow);
    transition: transform .3s ease, box-shadow .3s ease;
    animation: fadeUp .8s ease both;
}
.card:hover { transform: translate(-3px,-3px); box-shadow: var(--shadow-hover); }
#left-card { animation-delay:.15s; } #right-card { animation-delay:.3s; }

.section-title { font-size:1.15rem; font-weight:800; color:var(--ink) !important; margin-bottom:4px; letter-spacing:-.01em; }
.section-sub   { color:var(--ink-soft) !important; font-size:.9rem; margin-bottom:14px; line-height:1.5; }

/* ========== INPUT STATUS CHIPS ========== */
.status-row { display:flex; gap:8px; flex-wrap:wrap; margin: 4px 0 14px; }
.pill {
    display:inline-flex; align-items:center; gap:7px; padding:6px 13px; border-radius:999px;
    font-size:.8rem; font-weight:700; border:1.5px solid var(--line);
    background:#fff; color:#71717a !important; transition: all .3s ease;
}
.pill i { width:8px; height:8px; border-radius:50%; background:#d4d4d8; display:inline-block; transition: all .3s; }
.pill.on { background:var(--ink); color:#fff !important; border-color:var(--ink); transform: scale(1.04); }
.pill.on i { background:#fff; animation: blink 1.6s infinite; }

/* ========== TIPS ========== */
.tip {
    background: var(--bg-soft); border-left: 4px solid var(--ink); border-radius: 10px;
    padding: 10px 14px; font-size:.85rem; color: var(--ink-soft) !important; margin-bottom: 12px; line-height:1.5;
}
.tip b { color: var(--ink) !important; }

/* ========== TEXT VISIBILITY ========== */
label, label span, .block-label, .block-title, .gradio-container label,
.gradio-container .prose, .gradio-container p, .gradio-container h1,
.gradio-container h2, .gradio-container h3, .gradio-container span {
    color: var(--ink);
}
.gradio-container label span, .gradio-container .block-title { font-weight:600 !important; }

textarea, input[type="text"], .gradio-container textarea {
    background: var(--bg-soft) !important; color: var(--ink) !important;
    border: 1.5px solid var(--line) !important; border-radius: 12px !important;
    font-size: 1rem !important; line-height: 1.65 !important;
    transition: border-color .25s, box-shadow .25s, background .25s;
}
textarea:focus, input[type="text"]:focus {
    border-color: var(--ink) !important; background:#fff !important;
    box-shadow: 0 0 0 3px rgba(0,0,0,.12) !important;
}
textarea::placeholder { color:#71717a !important; opacity:1; }

.gradio-container .block, .gradio-container .form { background: transparent !important; border-color: var(--line) !important; }
.gradio-container [data-testid="block-label"] { background: var(--ink) !important; color:#fff !important; }
.gradio-container [data-testid="block-label"] * { color:#fff !important; }

/* Upload dropzones */
.gradio-container .upload-container, .gradio-container [data-testid="image"], .gradio-container [data-testid="video"] {
    border: 2px dashed var(--ink) !important; border-radius: 16px !important;
    background: rgba(255,255,255,.7) !important; transition: all .3s ease;
}
.gradio-container .upload-container:hover { background:#fff !important; transform: scale(1.01); box-shadow: 0 8px 24px rgba(0,0,0,.12); }
.gradio-container .wrap, .gradio-container .upload-container * { color: var(--ink) !important; }

/* Audio controls */
.gradio-container audio { width:100%; }
.gradio-container button.record, .gradio-container .record-button { transition: transform .2s; }
.gradio-container button.record:hover { transform: scale(1.06); }

/* ========== TABS ========== */
.tab-nav, [role="tablist"] { border-bottom: 2px solid var(--ink) !important; gap: 6px; flex-wrap: wrap; }
button[role="tab"] {
    color: var(--ink) !important; font-weight:700 !important; border-radius: 12px 12px 0 0 !important;
    padding: 10px 16px !important; transition: background .25s, color .25s, transform .2s;
}
button[role="tab"]:hover { background: var(--bg-soft) !important; transform: translateY(-2px); }
button[role="tab"][aria-selected="true"] { background: var(--ink) !important; color:#fff !important; border-color: var(--ink) !important; }

/* ========== BUTTONS ========== */
#analyze-btn, #clear-btn {
    min-height: 52px; border-radius: 14px !important; font-weight:800 !important; font-size:1.02rem !important;
    border: 2px solid var(--ink) !important;
    transition: transform .2s ease, background .25s ease, color .25s ease, box-shadow .25s ease;
}
#analyze-btn { background: var(--ink) !important; color:#fff !important; }
#analyze-btn:hover:not([disabled]) { background:#fff !important; color:var(--ink) !important; transform:translateY(-3px); box-shadow:0 12px 26px rgba(0,0,0,.28); }
#analyze-btn[disabled] {
    cursor: wait; opacity: 1 !important;
    background: repeating-linear-gradient(45deg, #0a0a0a 0 10px, #2a2a2a 10px 20px) !important;
    background-size: 40px 40px; animation: stripes .8s linear infinite;
}
#clear-btn { background:#fff !important; color:var(--ink) !important; }
#clear-btn:hover { background:var(--ink) !important; color:#fff !important; transform:translateY(-3px); }
#analyze-btn:active, #clear-btn:active { transform: scale(.97); }

/* Pipeline status */
.pipe {
    margin-top: 12px; padding: 10px 14px; border-radius: 12px; font-size:.88rem; font-weight:600;
    border: 1.5px solid var(--line); background:#fff; color:var(--ink) !important;
}
.pipe.busy { background: var(--ink); color:#fff !important; border-color: var(--ink); animation: blink 1.2s infinite; }
.pipe.done { border-color: var(--ink); }
.pipe.err  { background:#fff; border: 2px solid var(--ink); }

/* ========== FOOTER ========== */
#footer {
    margin-top:28px; padding:18px 24px; border:1.5px dashed var(--ink); border-radius:14px;
    color:var(--ink) !important; font-size:.88rem; text-align:center; background: rgba(255,255,255,.8);
    animation: fadeUp 1s ease .45s both;
}
footer { display:none !important; }

/* Scrollbar */
::-webkit-scrollbar { width:10px; height:10px; }
::-webkit-scrollbar-track { background:#f4f4f5; }
::-webkit-scrollbar-thumb { background:#0a0a0a; border-radius:10px; border:2px solid #f4f4f5; }

/* Focus ring (accessibility) */
button:focus-visible, textarea:focus-visible, input:focus-visible { outline: 3px solid var(--ink) !important; outline-offset: 2px; }

/* ========== RESPONSIVE ========== */
@media (max-width: 980px) {
    #main-row { flex-direction: column !important; }
    #main-row > div { min-width: 100% !important; width: 100% !important; }
    #bg .ring { display:none; }
}
@media (max-width: 640px) {
    :root { --shadow: 4px 4px 0 var(--ink); --shadow-hover: 6px 6px 0 var(--ink); }
    #steps .step { min-width: 100%; }
    .btn-row { flex-direction: column-reverse !important; }
    .btn-row > * { width:100% !important; min-width:100% !important; }
    #bg .orb { filter: blur(50px); }
    #bg .o1, #bg .o2 { width: 240px; height: 240px; }
}

/* Respect users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: .001ms !important; animation-iteration-count: 1 !important; transition-duration: .001ms !important; }
}
"""

# ============================ HTML BLOCKS =======================
BG_HTML = """
<div id="bg">
    <div class="grid"></div>
    <div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>
    <div class="ring"></div><div class="ring r2"></div>
</div>
"""

HERO_HTML = """
<div id="hero">
    <div class="badge"><span class="dot"></span> AI Powered &bull; Vision + Voice</div>
    <h1>AI Skin Specialist</h1>
    <p>Describe your skin concern with your voice, add a clear photo or short video,
       and receive an instant AI-generated assessment, spoken back to you.</p>
    <div class="features">
        <span class="chip">🎙 Voice Input</span>
        <span class="chip">📷 Image Analysis</span>
        <span class="chip">🔊 Spoken Reply</span>
    </div>
</div>
"""

STEPS_HTML = """
<div id="steps">
    <div class="step"><span class="num">1</span> Share your concern</div>
    <div class="step"><span class="num">2</span> AI analyzes</div>
    <div class="step"><span class="num">3</span> Read &amp; listen</div>
</div>
"""

FOOTER_HTML = """
<div id="footer">
    ⚠️ This tool provides AI-generated guidance only and is not a substitute for professional
    medical advice, diagnosis, or treatment. Please consult a licensed dermatologist.
</div>
"""


# ============================ UI HELPERS ========================
def pills(audio=None, image=None, video=None):
    def pill(name, active):
        cls = "pill on" if active else "pill"
        return f'<span class="{cls}"><i></i>{name}</span>'
    return (
        '<div class="status-row">'
        + pill("Voice", bool(audio))
        + pill("Image", bool(image))
        + pill("Video", bool(video))
        + "</div>"
    )


def pipe(state="idle"):
    msgs = {
        "idle": ("", "Ready — add an input and press Analyze."),
        "busy": ("busy", "⏳ Analyzing your inputs, please wait…"),
        "done": ("done", "✅ Analysis complete."),
        "err": ("err", "⚠️ Something went wrong. Check your inputs and try again."),
    }
    cls, text = msgs[state]
    return f'<div class="pipe {cls}">{text}</div>'


def run(audio, image, video):
    """UI wrapper: validates input, then calls your unchanged process_inputs()."""
    if not any([audio, image, video]):
        raise gr.Error("Please add at least one input: a voice recording, an image, or a video.")
    try:
        return process_inputs(audio, image, video)
    except Exception as e:
        raise gr.Error(f"Analysis failed: {e}")


def set_busy():
    return gr.update(value="Analyzing…", interactive=False), pipe("busy")


def set_idle(stt, resp):
    state = "done" if (stt or resp) else "err"
    return gr.update(value="Analyze Now →", interactive=True), pipe(state)


def clear_all():
    return None, None, None, "", "", None, pills(), pipe("idle")


# ============================ THEME =============================
theme = gr.themes.Base(
    primary_hue=gr.themes.colors.neutral,
    neutral_hue=gr.themes.colors.neutral,
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
).set(
    body_background_fill="#fafafa",
    body_background_fill_dark="#fafafa",
    body_text_color="#0a0a0a",
    body_text_color_dark="#0a0a0a",
    block_background_fill="#ffffff",
    block_background_fill_dark="#ffffff",
    block_label_text_color="#0a0a0a",
    block_label_text_color_dark="#0a0a0a",
    input_background_fill="#f4f4f5",
    input_background_fill_dark="#f4f4f5",
    button_primary_background_fill="#0a0a0a",
    button_primary_text_color="#ffffff",
)

# ============================ UI ================================
with gr.Blocks(title="AI Skin Specialist with Vision and Voice") as iface:

    gr.HTML(BG_HTML)
    gr.HTML(HERO_HTML)
    gr.HTML(STEPS_HTML)

    with gr.Row(equal_height=False, elem_id="main-row"):

        # ------------------- LEFT: INPUTS -------------------
        with gr.Column(scale=1, min_width=340, elem_classes="card", elem_id="left-card"):
            gr.HTML(
                '<div class="section-title">1. Share your concern</div>'
                '<div class="section-sub">Add any one input, or combine all three for the best result.</div>'
            )
            input_status = gr.HTML(pills())

            with gr.Tabs():
                with gr.Tab("🎙 Voice"):
                    gr.HTML('<div class="tip"><b>Tip:</b> Speak clearly in a quiet place. '
                            'Mention where the problem is, how long you have had it, and any itching or pain.</div>')
                    audio_in = gr.Audio(
                        sources=["microphone", "upload"],
                        type="filepath",
                        label="Patient Voice",
                        waveform_options=gr.WaveformOptions(
                            waveform_color="#a3a3a3",
                            waveform_progress_color="#0a0a0a",
                            show_recording_waveform=True,
                        ),
                    )
                with gr.Tab("📷 Image"):
                    gr.HTML('<div class="tip"><b>Tip:</b> Use natural daylight, keep the camera steady '
                            'and close, and avoid filters or heavy shadows.</div>')
                    image_in = gr.Image(
                        sources=["upload", "webcam", "clipboard"],
                        type="filepath",
                        label="Patient Image",
                        height=320,
                    )
                with gr.Tab("🎥 Video"):
                    gr.HTML('<div class="tip"><b>Tip:</b> Keep the video short (under 30 seconds) '
                            'and slowly move the camera around the affected area.</div>')
                    video_in = gr.Video(
                        sources=["upload", "webcam"],
                        label="Patient Video",
                        height=320,
                    )

            with gr.Row(elem_classes="btn-row"):
                clear_btn = gr.Button("Clear", elem_id="clear-btn", scale=1, min_width=120)
                analyze_btn = gr.Button("Analyze Now →", elem_id="analyze-btn", scale=2, min_width=200)

            pipeline = gr.HTML(pipe("idle"))

        # ------------------- RIGHT: OUTPUTS -------------------
        with gr.Column(scale=1, min_width=340, elem_classes="card", elem_id="right-card"):
            gr.HTML(
                '<div class="section-title">2. Your results</div>'
                '<div class="section-sub">Your transcription, the doctor\'s advice, and a spoken reply.</div>'
            )
            stt_out = gr.Textbox(
                label="Speech To Text",
                lines=3,
                placeholder="Your transcribed voice will appear here...",
                interactive=False,
            )
            doctor_out = gr.Textbox(
                label="Doctor's Response",
                lines=10,
                placeholder="The doctor's assessment will appear here...",
                interactive=False,
            )
            voice_out = gr.Audio(
                label="Doctor's Voice",
                autoplay=False,
                waveform_options=gr.WaveformOptions(
                    waveform_color="#a3a3a3",
                    waveform_progress_color="#0a0a0a",
                ),
            )

    gr.HTML(FOOTER_HTML)

    # ---------------- EVENTS ----------------
    gr.on(
        triggers=[
            audio_in.change, audio_in.clear, audio_in.stop_recording,
            image_in.change, image_in.clear,
            video_in.change, video_in.clear,
        ],
        fn=pills,
        inputs=[audio_in, image_in, video_in],
        outputs=input_status,
        show_progress="hidden",
    )

    analyze_btn.click(
        fn=set_busy, inputs=None, outputs=[analyze_btn, pipeline], show_progress="hidden",
    ).then(
        fn=run,
        inputs=[audio_in, image_in, video_in],
        outputs=[stt_out, doctor_out, voice_out],
    ).then(
        fn=set_idle, inputs=[stt_out, doctor_out], outputs=[analyze_btn, pipeline], show_progress="hidden",
    )

    clear_btn.click(
        fn=clear_all,
        inputs=None,
        outputs=[audio_in, image_in, video_in, stt_out, doctor_out, voice_out, input_status, pipeline],
    )


# ---------------------------------------------------------
# YOUR ORIGINAL LAUNCH  (unchanged)
# ---------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    # Gradio 6: theme and css are passed to launch()
    iface.launch(
        server_name="0.0.0.0",
        server_port=port,
        debug=False,
        theme=theme,
        css=CUSTOM_CSS,
    )