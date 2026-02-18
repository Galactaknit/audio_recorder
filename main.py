import gradio as gr
from pydub import AudioSegment
import os
import json
from datetime import datetime
import subprocess


# ============================================================
#  Configuration
# ============================================================

ROOT_DIR = "livres"
os.makedirs(ROOT_DIR, exist_ok=True)

current_book  = None
CHAPTERS_LIST = []

# Structure d'un livre :
#   livres/
#     └── MonLivre/
#           ├── chapters.json
#           ├── audio/        ← fichiers M4A (chapitres)
#           └── export/       ← fichier M4B final


# ============================================================
#  CSS personnalisé
# ============================================================

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,300;400;600&display=swap');

body, .gradio-container {
    background: #0f0f0f !important;
    font-family: 'DM Mono', monospace !important;
    color: #e8e2d9 !important;
}
h1, h2, h3, .gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {
    font-family: 'Fraunces', serif !important;
    font-weight: 300 !important;
    letter-spacing: -0.02em !important;
    color: #f5efe6 !important;
}
label, .gr-form label {
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #6b6560 !important;
}
input[type="text"], textarea, .gr-textbox textarea, .gr-textbox input {
    background: #1e1e1e !important;
    border: 1px solid #2e2e2e !important;
    border-radius: 8px !important;
    color: #e8e2d9 !important;
    font-family: 'DM Mono', monospace !important;
}
input[type="text"]:focus, textarea:focus {
    border-color: #c8a97e !important;
    box-shadow: 0 0 0 2px rgba(200,169,126,0.15) !important;
}
.gr-dropdown select, .gr-dropdown > div {
    background: #1e1e1e !important;
    border: 1px solid #2e2e2e !important;
    color: #e8e2d9 !important;
    font-family: 'DM Mono', monospace !important;
}
button.primary {
    background: #c8a97e !important;
    color: #0f0f0f !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: 0.08em !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
button.primary:hover {
    background: #e0c09a !important;
    transform: translateY(-1px) !important;
}
button.secondary, .gr-button {
    background: #1e1e1e !important;
    color: #e8e2d9 !important;
    border: 1px solid #2e2e2e !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: 0.06em !important;
    transition: all 0.2s ease !important;
}
button.secondary:hover, .gr-button:hover {
    border-color: #c8a97e !important;
    color: #c8a97e !important;
}
.gr-dataframe table {
    background: #181818 !important;
    border-collapse: collapse !important;
    width: 100% !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 13px !important;
}
.gr-dataframe th {
    background: #1e1e1e !important;
    color: #6b6560 !important;
    font-size: 10px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 10px 14px !important;
    border-bottom: 1px solid #2a2a2a !important;
}
.gr-dataframe td {
    padding: 10px 14px !important;
    border-bottom: 1px solid #1e1e1e !important;
    color: #e8e2d9 !important;
}
.gr-dataframe tr:hover td { background: #1e1e1e !important; }
.gr-dataframe tr.selected td {
    background: rgba(200,169,126,0.1) !important;
    border-left: 2px solid #c8a97e !important;
}
.status-box textarea {
    background: #111 !important;
    border: 1px solid #1e1e1e !important;
    color: #6b6560 !important;
    font-size: 12px !important;
    border-radius: 6px !important;
}
.gr-audio {
    background: #181818 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
}
.book-badge {
    display: inline-block;
    background: rgba(200,169,126,0.12);
    border: 1px solid rgba(200,169,126,0.3);
    border-radius: 6px;
    padding: 6px 14px;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #c8a97e;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.gr-accordion {
    background: #181818 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
}
.divider {
    border: none;
    border-top: 1px solid #2a2a2a;
    margin: 8px 0 16px 0;
}
"""


# ============================================================
#  Chemins par livre
# ============================================================

def book_dir(book_name):
    return os.path.join(ROOT_DIR, book_name)

def audio_dir(book_name):
    """Dossier des M4A."""
    return os.path.join(book_dir(book_name), "audio")

def export_dir(book_name):
    """Dossier du M4B final."""
    return os.path.join(book_dir(book_name), "export")

def chapters_file(book_name):
    return os.path.join(book_dir(book_name), "chapters.json")

def init_book_dirs(book_name):
    """Crée toute la structure de dossiers d'un livre."""
    os.makedirs(audio_dir(book_name),  exist_ok=True)
    os.makedirs(export_dir(book_name), exist_ok=True)


# ============================================================
#  Gestion des livres
# ============================================================

def get_books_list():
    return [
        d for d in sorted(os.listdir(ROOT_DIR))
        if os.path.isdir(os.path.join(ROOT_DIR, d))
    ]


def create_book(book_name):
    global current_book, CHAPTERS_LIST

    book_name = book_name.strip().replace(" ", "_")
    if not book_name:
        return "Nom invalide.", gr.update(), gr.update(), gr.update()

    if os.path.exists(book_dir(book_name)):
        return f"« {book_name} » existe déjà.", gr.update(), gr.update(), gr.update()

    init_book_dirs(book_name)
    save_chapters_json(book_name, [])

    current_book = book_name
    CHAPTERS_LIST.clear()

    return (
        f"✓ Livre créé : {book_name}",
        gr.update(choices=get_books_list(), value=book_name),
        get_chapters_display(),
        _book_badge()
    )


def switch_book(book_name):
    global current_book, CHAPTERS_LIST

    if not book_name:
        return "Aucun livre sélectionné.", get_chapters_display(), _book_badge()

    # Migration : si le livre n'a pas encore les sous-dossiers, on les crée
    init_book_dirs(book_name)

    current_book = book_name
    CHAPTERS_LIST.clear()
    CHAPTERS_LIST.extend(load_chapters(book_name))

    return f"✓ Livre chargé : {book_name}", get_chapters_display(), _book_badge()


def _book_badge():
    if current_book:
        return f'<div class="book-badge">📖 {current_book}</div>'
    return '<div class="book-badge" style="color:#555;border-color:#2a2a2a;">Aucun livre sélectionné</div>'


# ============================================================
#  Persistance JSON
# ============================================================

def load_chapters(book_name):
    path = chapters_file(book_name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_chapters_json(book_name, chapters):
    with open(chapters_file(book_name), "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)


# ============================================================
#  Gestion des chapitres
# ============================================================

def save_chapter(audio, chapter_title):
    if current_book is None:
        return "⚠️  Sélectionnez un livre d'abord."
    if audio is None:
        return "⚠️  Aucun enregistrement."

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = chapter_title.strip().replace(" ", "_") or f"chapitre_{timestamp}"

    # ← M4A dans audio/
    m4a_path = os.path.join(audio_dir(current_book), f"{safe_title}.m4a")

    sample_rate, data = audio
    audio_segment = AudioSegment(
        data.tobytes(),
        frame_rate=sample_rate,
        sample_width=data.dtype.itemsize,
        channels=1
    )
    audio_segment.export(m4a_path, format="ipod")

    creation_index = len(CHAPTERS_LIST)
    CHAPTERS_LIST.append((m4a_path, safe_title, creation_index))
    save_chapters_json(current_book, CHAPTERS_LIST)

    return f"✓  Chapitre sauvegardé : {safe_title}"


def get_chapters_display():
    if not CHAPTERS_LIST:
        return [["—", "Aucun chapitre", "—"]]

    rows = []
    for idx, entry in enumerate(CHAPTERS_LIST):
        file_path, title = entry[0], entry[1]
        if os.path.exists(file_path):
            audio    = AudioSegment.from_file(file_path)
            duration = str(round(audio.duration_seconds, 1)) + "s"
        else:
            duration = "fichier manquant"
        rows.append([idx + 1, title, duration])

    return rows


def move_chapter_up(selected_index):
    if selected_index is None or current_book is None:
        return get_chapters_display(), selected_index
    idx = int(selected_index)
    if idx <= 0:
        return get_chapters_display(), selected_index

    CHAPTERS_LIST[idx], CHAPTERS_LIST[idx - 1] = \
        CHAPTERS_LIST[idx - 1], CHAPTERS_LIST[idx]

    save_chapters_json(current_book, CHAPTERS_LIST)
    return get_chapters_display(), idx - 1


def move_chapter_down(selected_index):
    if selected_index is None or current_book is None:
        return get_chapters_display(), selected_index
    idx = int(selected_index)
    if idx >= len(CHAPTERS_LIST) - 1:
        return get_chapters_display(), selected_index

    CHAPTERS_LIST[idx], CHAPTERS_LIST[idx + 1] = \
        CHAPTERS_LIST[idx + 1], CHAPTERS_LIST[idx]

    save_chapters_json(current_book, CHAPTERS_LIST)
    return get_chapters_display(), idx + 1


def reset_order():
    if current_book is None:
        return get_chapters_display(), None
    CHAPTERS_LIST.sort(key=lambda e: e[2] if len(e) > 2 else 0)
    save_chapters_json(current_book, CHAPTERS_LIST)
    return get_chapters_display(), None


# ============================================================
#  Preview Audio
# ============================================================

def preview_chapter(selection: gr.SelectData):
    if not CHAPTERS_LIST:
        return None, None
    idx       = selection.index[0]
    file_path = CHAPTERS_LIST[idx][0]
    if os.path.exists(file_path):
        return file_path, idx
    return None, None


# ============================================================
#  Export M4B
# ============================================================

def export_m4b():
    if current_book is None:
        return "⚠️  Aucun livre sélectionné."
    if not CHAPTERS_LIST:
        return "⚠️  Aucun chapitre à exporter."

    out_audio  = audio_dir(current_book)
    out_export = export_dir(current_book)

    # ── Nom de fichier unique ────────────────────────────────
    base_name  = current_book
    output_m4b = os.path.join(out_export, f"{base_name}.m4b")
    counter    = 1
    while os.path.exists(output_m4b):
        output_m4b = os.path.join(out_export, f"{base_name}{counter}.m4b")
        counter += 1

    # ── Fichiers temporaires ─────────────────────────────────
    concat_file   = os.path.join(out_audio, "concat.txt")
    metadata_file = os.path.join(out_audio, "metadata.txt")

    with open(concat_file, "w") as f:
        for entry in CHAPTERS_LIST:
            f.write(f"file '{os.path.abspath(entry[0])}'\n")

    total_ms = 0
    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write(";FFMETADATA1\n")
        for entry in CHAPTERS_LIST:
            file_path, title = entry[0], entry[1]
            audio_segment    = AudioSegment.from_file(file_path)
            duration_ms      = int(audio_segment.duration_seconds * 1000)
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={total_ms}\n")
            f.write(f"END={total_ms + duration_ms}\n")
            f.write(f"title={title}\n")
            total_ms += duration_ms

    # ── Commande FFmpeg ──────────────────────────────────────
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

    return f"✓  Exporté : {output_m4b}"


# ============================================================
#  Interface Gradio
# ============================================================

with gr.Blocks(title="Audiobook Studio", css=CUSTOM_CSS) as app:

    # ── En-tête ──────────────────────────────────────────────
    gr.HTML("""
        <div style="padding: 32px 0 24px 0;">
            <div style="font-family:'Fraunces',serif; font-size:32px; font-weight:300;
                        color:#f5efe6; letter-spacing:-0.02em; margin-bottom:6px;">
                Audiobook Studio
            </div>
            <div style="font-family:'DM Mono',monospace; font-size:11px;
                        color:#4a4540; letter-spacing:0.15em; text-transform:uppercase;">
                Enregistrement · Chapitres · Export M4B
            </div>
        </div>
    """)

    # ── Gestion des livres (accordéon) ───────────────────────
    with gr.Accordion("📚  Gestion des livres", open=False):
        book_badge = gr.HTML(_book_badge())

        gr.HTML('<div style="height:12px"></div>')

        with gr.Row():
            book_selector = gr.Dropdown(
                label="Livres existants",
                choices=get_books_list(),
                value=None,
                interactive=True,
                scale=3
            )
            switch_button = gr.Button("📂  Charger ce livre", scale=1, variant="primary")

        gr.HTML('<hr class="divider">')

        with gr.Row():
            new_book_name = gr.Textbox(
                label="Créer un nouveau livre",
                placeholder="Titre du livre...",
                scale=3
            )
            create_book_button = gr.Button("➕  Créer", scale=1, variant="primary")

        switch_status = gr.Textbox(
            label="Statut",
            interactive=False,
            elem_classes=["status-box"]
        )

        # Arborescence affichée pour l'utilisateur
        gr.HTML("""
            <div style="margin-top:16px; font-family:'DM Mono',monospace;
                        font-size:11px; color:#4a4540; line-height:1.8;">
                <div style="color:#6b6560; letter-spacing:0.1em; margin-bottom:6px;">
                    STRUCTURE DES DOSSIERS
                </div>
                livres/<br>
                &nbsp;&nbsp;└── MonLivre/<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── chapters.json<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── audio/&nbsp;&nbsp;&nbsp;← fichiers .m4a<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── export/&nbsp;&nbsp;← fichier .m4b
            </div>
        """)

    gr.HTML('<div style="height:8px"></div>')

    # ── Colonnes principales ─────────────────────────────────
    with gr.Row(equal_height=False):

        # ── Colonne gauche : Enregistrement + Export ─────────
        with gr.Column(scale=1):
            gr.HTML("""
                <div style="font-family:'Fraunces',serif; font-size:18px;
                            color:#f5efe6; font-weight:300; margin-bottom:16px;">
                    🎙  Enregistrement
                </div>
            """)
            chapter_title = gr.Textbox(
                label="Titre du chapitre",
                placeholder="ex : Chapitre 1 — L'aube"
            )
            audio_input = gr.Audio(
                sources=["microphone"],
                type="numpy",
                label="Microphone"
            )
            save_button = gr.Button("💾  Sauvegarder le chapitre", variant="primary")
            status = gr.Textbox(
                label="Statut",
                interactive=False,
                elem_classes=["status-box"]
            )

            gr.HTML('<div style="height:24px"></div>')

            gr.HTML("""
                <div style="font-family:'Fraunces',serif; font-size:18px;
                            color:#f5efe6; font-weight:300; margin-bottom:16px;">
                    📦  Export
                </div>
            """)
            export_button = gr.Button("Exporter en M4B", variant="primary")
            export_status = gr.Textbox(
                label="Statut export",
                interactive=False,
                elem_classes=["status-box"]
            )

        # ── Colonne droite : Chapitres + Preview ─────────────
        with gr.Column(scale=2):
            gr.HTML("""
                <div style="font-family:'Fraunces',serif; font-size:18px;
                            color:#f5efe6; font-weight:300; margin-bottom:16px;">
                    📋  Chapitres
                </div>
            """)
            chapters_table = gr.DataFrame(
                headers=["#", "Titre", "Durée"],
                datatype=["number", "str", "str"],
                interactive=False,
                label=None
            )
            with gr.Row():
                move_up_button     = gr.Button("⬆  Monter")
                move_down_button   = gr.Button("⬇  Descendre")
                reset_order_button = gr.Button("🔁  Ordre original")
                refresh_button     = gr.Button("🔄  Rafraîchir")

            gr.HTML('<div style="height:16px"></div>')
            gr.HTML("""
                <div style="font-family:'Fraunces',serif; font-size:16px;
                            color:#f5efe6; font-weight:300; margin-bottom:8px;">
                    🎧  Preview
                </div>
            """)
            preview_player = gr.Audio(label=None, interactive=False)

    # ── État interne ─────────────────────────────────────────
    selected_index = gr.State(value=None)

    # ── Événements ───────────────────────────────────────────

    create_book_button.click(
        fn=create_book,
        inputs=new_book_name,
        outputs=[switch_status, book_selector, chapters_table, book_badge]
    )

    switch_button.click(
        fn=switch_book,
        inputs=book_selector,
        outputs=[switch_status, chapters_table, book_badge]
    )

    save_button.click(
        fn=save_chapter,
        inputs=[audio_input, chapter_title],
        outputs=status
    ).then(
        fn=get_chapters_display,
        outputs=chapters_table
    ).then(
        fn=lambda: None,
        outputs=audio_input
    )

    export_button.click(fn=export_m4b, outputs=export_status)

    refresh_button.click(fn=get_chapters_display, outputs=chapters_table)

    chapters_table.select(
        fn=preview_chapter,
        outputs=[preview_player, selected_index]
    )

    move_up_button.click(
        fn=move_chapter_up,
        inputs=selected_index,
        outputs=[chapters_table, selected_index]
    )

    move_down_button.click(
        fn=move_chapter_down,
        inputs=selected_index,
        outputs=[chapters_table, selected_index]
    )

    reset_order_button.click(
        fn=reset_order,
        outputs=[chapters_table, selected_index]
    )

    app.load(fn=get_chapters_display, outputs=chapters_table)


app.launch()