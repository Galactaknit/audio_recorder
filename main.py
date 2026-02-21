import gradio as gr
from pydub import AudioSegment
import os
import re
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
.btn-delete button {
    background: #1e1212 !important;
    color: #c87e7e !important;
    border: 1px solid #3a2020 !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
    transition: all 0.2s ease !important;
}
.btn-delete button:hover {
    background: #2a1515 !important;
    border-color: #c87e7e !important;
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
#  Sanitisation des noms
# ============================================================

def sanitize_filename(name):
    replacements = {
        'à':'a','á':'a','â':'a','ã':'a','ä':'a','å':'a',
        'æ':'ae','ç':'c',
        'è':'e','é':'e','ê':'e','ë':'e',
        'ì':'i','í':'i','î':'i','ï':'i',
        'ð':'d','ñ':'n',
        'ò':'o','ó':'o','ô':'o','õ':'o','ö':'o',
        'ù':'u','ú':'u','û':'u','ü':'u',
        'ý':'y','ÿ':'y',
        'À':'A','Á':'A','Â':'A','Ã':'A','Ä':'A','Å':'A',
        'Æ':'AE','Ç':'C',
        'È':'E','É':'E','Ê':'E','Ë':'E',
        'Ì':'I','Í':'I','Î':'I','Ï':'I',
        'Ð':'D','Ñ':'N',
        'Ò':'O','Ó':'O','Ô':'O','Õ':'O','Ö':'O',
        'Ù':'U','Ú':'U','Û':'U','Ü':'U',
        'Ý':'Y',
    }
    for src, dst in replacements.items():
        name = name.replace(src, dst)

    name = re.sub(r"['\u2018\u2019\u201a\u201b\u2032\u2035\"„\u201c\u201d«»`]", "", name)
    name = re.sub(r"[\s\-_]+", "_", name)
    name = re.sub(r"[^A-Za-z0-9_]", "", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")

    return name


# ============================================================
#  Accès uniforme aux entrées de CHAPTERS_LIST
#  Chaque entrée : [file_path, display_title, creation_index]
# ============================================================

def entry_path(e):
    return e[0]

def entry_title(e):
    return e[1]

def entry_index(e):
    return e[2] if len(e) > 2 else 0

def normalize_entry(e):
    if len(e) == 2:
        return [e[0], e[1], 0]
    return list(e)

def normalize_list():
    for i, e in enumerate(CHAPTERS_LIST):
        CHAPTERS_LIST[i] = normalize_entry(e)


# ============================================================
#  Chemins par livre
# ============================================================

def book_dir(book_name):
    return os.path.join(ROOT_DIR, book_name)

def audio_dir(book_name):
    return os.path.join(book_dir(book_name), "audio")

def export_dir(book_name):
    return os.path.join(book_dir(book_name), "export")

def chapters_file(book_name):
    return os.path.join(book_dir(book_name), "chapters.json")

def init_book_dirs(book_name):
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

    book_name = sanitize_filename(book_name.strip())
    if not book_name:
        return "Le nom n'est pas valide, essaie autre chose 🌸", gr.update(), gr.update(), gr.update()

    if os.path.exists(book_dir(book_name)):
        return f"Un livre « {book_name} » existe déjà !", gr.update(), gr.update(), gr.update()

    init_book_dirs(book_name)
    save_chapters_json(book_name, [])

    current_book = book_name
    CHAPTERS_LIST.clear()

    return (
        f"✓ Ton livre « {book_name} » est prêt !",
        gr.update(choices=get_books_list(), value=book_name),
        get_chapters_display(),
        _book_badge()
    )


def switch_book(book_name):
    global current_book, CHAPTERS_LIST

    if not book_name:
        return "Aucun livre choisi.", get_chapters_display(), _book_badge()

    init_book_dirs(book_name)

    current_book = book_name
    CHAPTERS_LIST.clear()
    CHAPTERS_LIST.extend(load_chapters(book_name))
    normalize_list()

    return f"✓ Tu travailles maintenant sur « {book_name} » 📖", get_chapters_display(), _book_badge()


def _book_badge():
    if current_book:
        return f'<div class="book-badge">📖 Livre ouvert : {current_book}</div>'
    return '<div class="book-badge" style="color:#555;border-color:#2a2a2a;">Aucun livre ouvert pour l\'instant</div>'


# ============================================================
#  Persistance JSON
# ============================================================

def load_chapters(book_name):
    path = chapters_file(book_name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [normalize_entry(e) for e in data]
    return []


def save_chapters_json(book_name, chapters):
    with open(chapters_file(book_name), "w", encoding="utf-8") as f:
        json.dump([list(e) for e in chapters], f, ensure_ascii=False, indent=2)


# ============================================================
#  Gestion des chapitres
# ============================================================

def save_chapter(audio, chapter_title):
    if current_book is None:
        return "⚠️  Choisis d'abord un livre dans le menu en haut !"
    if audio is None:
        return "⚠️  Tu n'as pas encore enregistré ta voix 🎤"

    try:
        timestamp     = datetime.now().strftime("%Y%m%d_%H%M%S")
        display_title = chapter_title.strip() if chapter_title else ""
        display_title = display_title or f"histoire_{timestamp}"

        safe_title = sanitize_filename(display_title) or f"histoire_{timestamp}"

        m4a_path = os.path.join(audio_dir(current_book), f"{safe_title}.m4a")
        counter  = 1
        while os.path.exists(m4a_path):
            m4a_path = os.path.join(audio_dir(current_book), f"{safe_title}_{counter}.m4a")
            counter += 1

        sample_rate, data = audio
        audio_segment = AudioSegment(
            data.tobytes(),
            frame_rate=sample_rate,
            sample_width=data.dtype.itemsize,
            channels=1 if data.ndim == 1 else data.shape[1]
        )
        audio_segment.export(m4a_path, format="ipod")

        creation_index = len(CHAPTERS_LIST)
        CHAPTERS_LIST.append([m4a_path, display_title, creation_index])
        save_chapters_json(current_book, CHAPTERS_LIST)

        return f"✓  « {display_title} » a bien été enregistré 🌸"

    except Exception as ex:
        return f"❌  Quelque chose n'a pas fonctionné : {ex}"


def delete_chapter(selected_index):
    if selected_index is None:
        return "⚠️  Clique d'abord sur un chapitre dans la liste.", get_chapters_display(), None
    if current_book is None:
        return "⚠️  Aucun livre ouvert.", get_chapters_display(), None

    try:
        idx = int(selected_index)
        if idx < 0 or idx >= len(CHAPTERS_LIST):
            return "⚠️  Ce chapitre n'existe plus.", get_chapters_display(), None

        entry     = normalize_entry(CHAPTERS_LIST[idx])
        file_path = entry_path(entry)
        title     = entry_title(entry)

        if os.path.exists(file_path):
            os.remove(file_path)

        CHAPTERS_LIST.pop(idx)
        save_chapters_json(current_book, CHAPTERS_LIST)

        return f"✓  « {title} » a été supprimé.", get_chapters_display(), None

    except Exception as ex:
        return f"❌  Erreur : {ex}", get_chapters_display(), None


def get_chapters_display():
    if not CHAPTERS_LIST:
        return [["—", "Pas encore de chapitre", "—"]]

    rows = []
    for idx, e in enumerate(CHAPTERS_LIST):
        entry     = normalize_entry(e)
        file_path = entry_path(entry)
        title     = entry_title(entry)

        if os.path.exists(file_path):
            try:
                seg      = AudioSegment.from_file(file_path)
                duration = str(round(seg.duration_seconds, 1)) + "s"
            except Exception:
                duration = "problème de lecture"
        else:
            duration = "fichier introuvable"

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
    CHAPTERS_LIST.sort(key=lambda e: entry_index(e))
    save_chapters_json(current_book, CHAPTERS_LIST)
    return get_chapters_display(), None


# ============================================================
#  Preview Audio
# ============================================================

def preview_chapter(selection: gr.SelectData):
    if not CHAPTERS_LIST:
        return None, None
    idx       = selection.index[0]
    file_path = entry_path(normalize_entry(CHAPTERS_LIST[idx]))
    if os.path.exists(file_path):
        return file_path, idx
    return None, None


# ============================================================
#  Export M4B
# ============================================================

def export_m4b():
    if current_book is None:
        return "⚠️  Ouvre d'abord un livre !"
    if not CHAPTERS_LIST:
        return "⚠️  Il n'y a encore aucun chapitre dans ce livre."

    try:
        out_audio  = audio_dir(current_book)
        out_export = export_dir(current_book)

        base_name  = current_book
        output_m4b = os.path.join(out_export, f"{base_name}.m4b")
        counter    = 1
        while os.path.exists(output_m4b):
            output_m4b = os.path.join(out_export, f"{base_name}{counter}.m4b")
            counter += 1

        concat_file   = os.path.join(out_audio, "concat.txt")
        metadata_file = os.path.join(out_audio, "metadata.txt")

        with open(concat_file, "w", encoding="utf-8") as f:
            for e in CHAPTERS_LIST:
                safe_path = os.path.abspath(entry_path(normalize_entry(e)))
                safe_path = safe_path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        total_ms = 0
        with open(metadata_file, "w", encoding="utf-8") as f:
            f.write(";FFMETADATA1\n")
            for e in CHAPTERS_LIST:
                entry     = normalize_entry(e)
                file_path = entry_path(entry)
                title     = entry_title(entry)

                seg         = AudioSegment.from_file(file_path)
                duration_ms = int(seg.duration_seconds * 1000)

                safe_title = (
                    title
                    .replace("\\", "\\\\")
                    .replace("=",  "\\=")
                    .replace(";",  "\\;")
                    .replace("#",  "\\#")
                    .replace("\n", " ")
                )

                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={total_ms}\n")
                f.write(f"END={total_ms + duration_ms}\n")
                f.write(f"title={safe_title}\n")
                total_ms += duration_ms

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_file,
                "-i", metadata_file,
                "-map_metadata", "1",
                "-c", "copy",
                output_m4b
            ],
            check=True
        )

        return f"✓  Ton livre audio est prêt ! Tu le trouveras ici : {output_m4b} 🎉"

    except Exception as ex:
        return f"❌  Quelque chose n'a pas fonctionné : {ex}"


# ============================================================
#  Interface Gradio
# ============================================================

with gr.Blocks(title="Studio de Mamie 🎧", css=CUSTOM_CSS) as app:

    # ── En-tête ──────────────────────────────────────────────
    gr.HTML("""
        <div style="padding: 32px 0 24px 0;">
            <div style="font-family:'Fraunces',serif; font-size:32px; font-weight:300;
                        color:#f5efe6; letter-spacing:-0.02em; margin-bottom:6px;">
                Studio de Mamie 🎧
            </div>
            <div style="font-family:'DM Mono',monospace; font-size:11px;
                        color:#4a4540; letter-spacing:0.15em; text-transform:uppercase;">
                Enregistre ta voix · Crée tes histoires · Écoute ton livre
            </div>
        </div>
    """)

    # ── Gestion des livres (accordéon) ───────────────────────
    with gr.Accordion("📚  Mes livres audio", open=False):
        book_badge = gr.HTML(_book_badge())

        gr.HTML('<div style="height:12px"></div>')

        with gr.Row():
            book_selector = gr.Dropdown(
                label="Choisir un de mes livres",
                choices=get_books_list(),
                value=None,
                interactive=True,
                scale=3
            )
            switch_button = gr.Button("📂  Ouvrir ce livre", scale=1, variant="primary")

        gr.HTML('<hr class="divider">')

        with gr.Row():
            new_book_name = gr.Textbox(
                label="Créer un tout nouveau livre",
                placeholder="ex : Mes souvenirs d'enfance, Les recettes de famille...",
                scale=3
            )
            create_book_button = gr.Button("✨  Créer", scale=1, variant="primary")

        switch_status = gr.Textbox(
            label="Ce qui se passe...",
            interactive=False,
            elem_classes=["status-box"]
        )

        gr.HTML("""
            <div style="margin-top:16px; font-family:'DM Mono',monospace;
                        font-size:11px; color:#4a4540; line-height:1.8;">
                <div style="color:#6b6560; letter-spacing:0.1em; margin-bottom:6px;">
                    OÙ SONT SAUVEGARDÉS TES FICHIERS
                </div>
                livres/<br>
                &nbsp;&nbsp;└── MonLivre/<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── chapters.json<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── audio/&nbsp;&nbsp;&nbsp;← tes enregistrements<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── export/&nbsp;&nbsp;← ton livre audio fini
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
                    🎙  Ma voix
                </div>
            """)
            chapter_title = gr.Textbox(
                label="Nom de ce chapitre",
                placeholder="ex : Le jardin de mon enfance, La rencontre de papy..."
            )
            audio_input = gr.Audio(
                sources=["microphone"],
                type="numpy",
                label="Appuie ici pour parler 🎤"
            )
            save_button = gr.Button("💾  Sauvegarder ce chapitre", variant="primary")
            status = gr.Textbox(
                label="Ce qui se passe...",
                interactive=False,
                elem_classes=["status-box"]
            )

            gr.HTML('<div style="height:24px"></div>')

            gr.HTML("""
                <div style="font-family:'Fraunces',serif; font-size:18px;
                            color:#f5efe6; font-weight:300; margin-bottom:16px;">
                    📦  Mon livre fini
                </div>
            """)
            export_button = gr.Button("🎉  Créer mon livre audio", variant="primary")
            export_status = gr.Textbox(
                label="Ton livre est prêt ?",
                interactive=False,
                elem_classes=["status-box"]
            )

        # ── Colonne droite : Chapitres + Preview ─────────────
        with gr.Column(scale=2):
            gr.HTML("""
                <div style="font-family:'Fraunces',serif; font-size:18px;
                            color:#f5efe6; font-weight:300; margin-bottom:16px;">
                    📋  Mes chapitres enregistrés
                </div>
            """)
            chapters_table = gr.DataFrame(
                headers=["N°", "Chapitre", "Durée"],
                datatype=["number", "str", "str"],
                interactive=False,
                label=None
            )

            with gr.Row():
                move_up_button     = gr.Button("⬆  Mettre avant")
                move_down_button   = gr.Button("⬇  Mettre après")
                reset_order_button = gr.Button("🔁  Ordre d'origine")
                refresh_button     = gr.Button("🔄  Actualiser")

            with gr.Row():
                delete_button = gr.Button(
                    "🗑  Supprimer le chapitre sélectionné",
                    elem_classes=["btn-delete"]
                )

            delete_status = gr.Textbox(
                label="Suppression...",
                interactive=False,
                elem_classes=["status-box"]
            )

            gr.HTML('<div style="height:16px"></div>')
            gr.HTML("""
                <div style="font-family:'Fraunces',serif; font-size:16px;
                            color:#f5efe6; font-weight:300; margin-bottom:8px;">
                    🎧  Écouter ce chapitre
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

    delete_button.click(
        fn=delete_chapter,
        inputs=selected_index,
        outputs=[delete_status, chapters_table, selected_index]
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


app.launch(inbrowser=True)