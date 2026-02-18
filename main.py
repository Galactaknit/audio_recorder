import gradio as gr
from pydub import AudioSegment
import os
import json
from datetime import datetime
import subprocess


# ============================================================
#  Configuration
# ============================================================

OUTPUT_DIR   = "chapitres"
CHAPTERS_FILE = f"{OUTPUT_DIR}/chapters.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
#  Persistance JSON
# ============================================================

def load_chapters():
    if os.path.exists(CHAPTERS_FILE):
        with open(CHAPTERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_chapters_json(chapters):
    with open(CHAPTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)


CHAPTERS_LIST = load_chapters()


# ============================================================
#  Gestion des chapitres
# ============================================================

def save_chapter(audio, chapter_title):
    if audio is None:
        return "Aucun enregistrement."

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = chapter_title.strip().replace(" ", "_") or f"chapitre_{timestamp}"
    m4a_path   = f"{OUTPUT_DIR}/{safe_title}.m4a"

    sample_rate, data = audio
    audio_segment = AudioSegment(
        data.tobytes(),
        frame_rate=sample_rate,
        sample_width=data.dtype.itemsize,
        channels=1
    )
    audio_segment.export(m4a_path, format="ipod")

    CHAPTERS_LIST.append((m4a_path, safe_title))
    save_chapters_json(CHAPTERS_LIST)

    return f"Chapitre sauvegardé : {m4a_path}"


def get_chapters_display():
    if not CHAPTERS_LIST:
        return [["Aucun chapitre enregistré", "", ""]]

    rows = []
    for idx, (file_path, title) in enumerate(CHAPTERS_LIST):
        if os.path.exists(file_path):
            audio    = AudioSegment.from_file(file_path)
            duration = str(round(audio.duration_seconds, 1)) + "s"
        else:
            duration = "fichier manquant"

        rows.append([idx + 1, title, duration])

    return rows


# ============================================================
#  Export M4B
# ============================================================

def export_m4b(book_title="Mon_Livre"):
    if not CHAPTERS_LIST:
        return "Aucun chapitre à exporter."

    # Fichier de concaténation FFmpeg
    concat_file = f"{OUTPUT_DIR}/concat.txt"
    with open(concat_file, "w") as f:
        for file_path, _ in CHAPTERS_LIST:
            f.write(f"file '{os.path.abspath(file_path)}'\n")

    # Fichier de métadonnées FFmpeg (chapitres)
    metadata_file = f"{OUTPUT_DIR}/metadata.txt"
    total_ms = 0
    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write(";FFMETADATA1\n")
        for _, (file_path, title) in enumerate(CHAPTERS_LIST):
            audio_segment = AudioSegment.from_file(file_path)
            duration_ms   = int(audio_segment.duration_seconds * 1000)

            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={total_ms}\n")
            f.write(f"END={total_ms + duration_ms}\n")
            f.write(f"title={title}\n")

            total_ms += duration_ms

    # Commande FFmpeg : concat + injection des chapitres
    output_m4b = f"{OUTPUT_DIR}/{book_title}.m4b"
    subprocess.run(
        [
            "ffmpeg",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-i", metadata_file,
            "-map_metadata", "1",
            "-c", "copy",
            output_m4b
        ],
        check=True
    )

    return f"Livre audio exporté : {output_m4b}"


# ============================================================
#  Interface Gradio
# ============================================================

with gr.Blocks(title="Livre Audio – Enregistrement et Export M4B") as app:

    gr.Markdown("## 🎙️ Enregistrement de livre audio avec chapitres")

    # --- Saisie ---
    chapter_title = gr.Textbox(
        label="Titre du chapitre",
        placeholder="Chapitre 1"
    )
    audio_input = gr.Audio(
        sources=["microphone"],
        type="numpy",
        label="Enregistrement"
    )
    save_button = gr.Button("💾 Sauvegarder le chapitre")
    status      = gr.Textbox(label="Statut", interactive=False)

    gr.Markdown("---")

    # --- Export ---
    export_button = gr.Button("📦 Export M4B")
    export_status = gr.Textbox(label="Export", interactive=False)

    gr.Markdown("---")

    # --- Liste des chapitres ---
    gr.Markdown("### 📋 Chapitres enregistrés")
    chapters_table = gr.DataFrame(
        headers=["#", "Titre", "Durée"],
        datatype=["number", "str", "str"],
        interactive=False,
        label="Liste des chapitres"
    )
    refresh_button = gr.Button("🔄 Rafraîchir la liste")

    # --- Événements ---
    save_button.click(
        fn=save_chapter,
        inputs=[audio_input, chapter_title],
        outputs=status
    ).then(
        fn=get_chapters_display,
        outputs=chapters_table
    )

    export_button.click(
        fn=export_m4b,
        inputs=[chapter_title],
        outputs=export_status
    )

    refresh_button.click(
        fn=get_chapters_display,
        outputs=chapters_table
    )

    app.load(
        fn=get_chapters_display,
        outputs=chapters_table
    )


app.launch()