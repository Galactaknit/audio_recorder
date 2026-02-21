import gradio as gr
from pydub import AudioSegment
import os
import re
import json
from datetime import datetime
import subprocess
import sys


# ============================================================
#  Configuration
# ============================================================

ROOT_DIR = "livres"
os.makedirs(ROOT_DIR, exist_ok=True)

current_book  = None
CHAPTERS_LIST = []

IS_WINDOWS = sys.platform.startswith("win")


# ============================================================
#  CSS — Toutes les couleurs centralisées dans :root
# ============================================================


CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,300;400;600&display=swap');

:root {
    /* ── Fonds ── */
    --color-bg-page:      #ffffff;
    --color-bg-panel:     #f8f9fa;
    --color-bg-input:     #ffffff;
    --color-bg-subtle:    #f1f3f5;
    --color-bg-hover:     #e9ecef;

    /* ── Bordures ── */
    --color-border:       #dee2e6;
    --color-border-focus: #adb5bd;

    /* ── Textes ── */
    --color-text-main:    #212529;
    --color-text-soft:    #495057;
    --color-text-muted:   #868e96;

    /* ── Accent ── */
    --color-accent:        #3b82f6;
    --color-accent-hover:  #2563eb;
    --color-accent-light:  rgba(59,130,246,0.08);
    --color-accent-border: rgba(59,130,246,0.25);
    --color-accent-text:   #ffffff;

    /* ── Danger ── */
    --color-danger:        #dc2626;
    --color-danger-bg:     #fef2f2;
    --color-danger-border: #fecaca;

    /* ── Typographie ── */
    --font-display: 'Fraunces', serif;
    --font-mono:    'DM Mono', monospace;
}

/* ── Reset global ── */
*, *::before, *::after { box-sizing: border-box; }

body,
.gradio-container,
.gradio-container > *,
.dark, [data-theme] {
    background-color: var(--color-bg-page) !important;
    color: var(--color-text-main) !important;
    font-family: var(--font-mono) !important;
}

/* ── Titres ── */
h1, h2, h3 {
    font-family: var(--font-display) !important;
    font-weight: 300 !important;
    letter-spacing: -0.02em !important;
    color: var(--color-text-main) !important;
}

/* ── Labels ── */
label, span.svelte-1gfkfd6 {
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--color-text-soft) !important;
}

/* ── Inputs & Textareas ── */
input, textarea,
.gr-textbox input,
.gr-textbox textarea,
input[type="text"] {
    background: var(--color-bg-input) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 8px !important;
    color: var(--color-text-main) !important;
    font-family: var(--font-mono) !important;
    font-size: 13px !important;
}
input:focus, textarea:focus {
    border-color: var(--color-border-focus) !important;
    box-shadow: 0 0 0 2px var(--color-accent-light) !important;
    outline: none !important;
}

/* ── Dropdown ── */
.gr-dropdown, .gr-dropdown > div, select {
    background: var(--color-bg-input) !important;
    border: 1px solid var(--color-border) !important;
    color: var(--color-text-main) !important;
    font-family: var(--font-mono) !important;
    border-radius: 8px !important;
}

/* ── Boutons primaires ── */
button.primary, .gr-button.primary {
    background: var(--color-accent) !important;
    color: var(--color-accent-text) !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
    font-size: 12px !important;
    letter-spacing: 0.08em !important;
    font-weight: 500 !important;
    transition: background 0.2s ease, transform 0.15s ease !important;
}
button.primary:hover {
    background: var(--color-accent-hover) !important;
    transform: translateY(-1px) !important;
}

/* ── Boutons secondaires ── */
button.secondary, .gr-button, button {
    background: var(--color-bg-subtle) !important;
    color: var(--color-text-main) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
    font-size: 12px !important;
    letter-spacing: 0.05em !important;
    transition: border-color 0.2s, background 0.2s !important;
}
button.secondary:hover, .gr-button:hover, button:hover {
    background: var(--color-bg-hover) !important;
    border-color: var(--color-accent) !important;
}

/* ── Bouton supprimer ── */
.btn-delete button {
    background: var(--color-danger-bg) !important;
    color: var(--color-danger) !important;
    border: 1px solid var(--color-danger-border) !important;
}
.btn-delete button:hover {
    filter: brightness(0.95) !important;
    border-color: var(--color-danger) !important;
}

/* ── Panneaux / blocs ── */
.gr-panel, .gr-box, .gradio-container .prose {
    background: var(--color-bg-panel) !important;
    border-color: var(--color-border) !important;
}

/* ── Accordion ── */
.gr-accordion, details, details > summary {
    background: var(--color-bg-panel) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 10px !important;
    color: var(--color-text-main) !important;
}

/* ── Tableau ── */
table {
    background: var(--color-bg-panel) !important;
    border-collapse: collapse !important;
    width: 100% !important;
    font-family: var(--font-mono) !important;
    font-size: 13px !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
th {
    background: var(--color-bg-subtle) !important;
    color: var(--color-text-soft) !important;
    font-size: 10px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 10px 14px !important;
    border-bottom: 1px solid var(--color-border) !important;
}
td {
    padding: 10px 14px !important;
    border-bottom: 1px solid var(--color-bg-subtle) !important;
    color: var(--color-text-main) !important;
    background: var(--color-bg-panel) !important;
}
tr:hover td {
    background: var(--color-bg-hover) !important;
}

/* ── Status boxes ── */
.status-box textarea {
    background: var(--color-bg-subtle) !important;
    border: 1px solid var(--color-border) !important;
    color: var(--color-text-soft) !important;
    font-size: 12px !important;
    border-radius: 6px !important;
    font-style: italic !important;
}

/* ── Audio player ── */
.gr-audio, audio {
    background: var(--color-bg-panel) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 10px !important;
}

/* ── Badge livre actif ── */
.book-badge {
    display: inline-block;
    background: var(--color-accent-light);
    border: 1px solid var(--color-accent-border);
    border-radius: 6px;
    padding: 6px 14px;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--color-accent);
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}

/* ── Divider ── */
.divider {
    border: none;
    border-top: 1px solid var(--color-border);
    margin: 12px 0 16px 0;
}

/* ── Fonds Gradio (blocs, wrappers, prose, svelte) ── */
.block,
.block.padded,
.form,
.gap,
.contain,
.wrap,
.prose,
.gradio-container .block,
.gradio-container .form,
.gradio-container .gap,
[class*="block"],
[class*="wrap"],
[class*="prose"],
.svelte-1gfkfd6,
fieldset,
.label-wrap,
.component-wrapper {
    background-color: var(--color-bg-page) !important;
    border-color: var(--color-border) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--color-bg-page); }
::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--color-text-muted); }

/* ── Titres inline (gr.HTML) ── */
.section-title {
    font-family: var(--font-display);
    font-size: 18px;
    font-weight: 300;
    color: var(--color-text-main);
    margin-bottom: 16px;
}
.section-title-sm {
    font-family: var(--font-display);
    font-size: 16px;
    font-weight: 300;
    color: var(--color-text-main);
    margin: 16px 0 8px 0;
}
.app-title {
    font-family: var(--font-display);
    font-size: 32px;
    font-weight: 300;
    color: var(--color-text-main);
    letter-spacing: -0.02em;
    margin-bottom: 6px;
}
.app-subtitle {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--color-text-soft);
    letter-spacing: 0.15em;
    text-transform: uppercase;
}
.folder-tree {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--color-text-soft);
    line-height: 1.9;
    margin-top: 14px;
}
.folder-tree-title {
    color: var(--color-accent);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-size: 10px;
    margin-bottom: 6px;
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

def entry_path(e):  return e[0]
def entry_title(e): return e[1]
def entry_index(e): return e[2] if len(e) > 2 else 0

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

def book_dir(n):      return os.path.join(ROOT_DIR, n)
def audio_dir(n):     return os.path.join(book_dir(n), "audio")
def export_dir(n):    return os.path.join(book_dir(n), "export")
def chapters_file(n): return os.path.join(book_dir(n), "chapters.json")

def init_book_dirs(n):
    os.makedirs(audio_dir(n),  exist_ok=True)
    os.makedirs(export_dir(n), exist_ok=True)


# ============================================================
#  Gestion des livres
# ============================================================

def get_books_list():
    return [d for d in sorted(os.listdir(ROOT_DIR))
            if os.path.isdir(os.path.join(ROOT_DIR, d))]


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
    return '<div class="book-badge" style="color:var(--color-text-muted);border-color:var(--color-border);">Aucun livre ouvert pour l\'instant</div>'


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
    """
    FIX Windows :
    - On exporte d'abord en WAV (toujours disponible sans codec externe).
    - On convertit ensuite en AAC/M4A via ffmpeg si disponible,
      sinon on garde le WAV (Gradio et pydub le lisent parfaitement).
    - On utilise os.path pour les chemins (pas de slashes Unix hardcodés).
    """
    if current_book is None:
        return "⚠️  Choisis d'abord un livre dans le menu en haut !"
    if audio is None:
        return "⚠️  Tu n'as pas encore enregistré ta voix 🎤"

    try:
        timestamp     = datetime.now().strftime("%Y%m%d_%H%M%S")
        display_title = (chapter_title.strip() if chapter_title else "") or f"histoire_{timestamp}"
        safe_title    = sanitize_filename(display_title) or f"histoire_{timestamp}"

        dest_dir = audio_dir(current_book)

        # ── Cherche un nom de fichier libre ──────────────────
        def free_path(ext):
            p = os.path.join(dest_dir, f"{safe_title}.{ext}")
            c = 1
            while os.path.exists(p):
                p = os.path.join(dest_dir, f"{safe_title}_{c}.{ext}")
                c += 1
            return p

        sample_rate, data = audio
        audio_segment = AudioSegment(
            data.tobytes(),
            frame_rate=sample_rate,
            sample_width=data.dtype.itemsize,
            channels=1 if data.ndim == 1 else data.shape[1]
        )

        # ── Essaie M4A via ffmpeg, sinon fallback WAV ────────
        saved_path = None
        ffmpeg_ok  = False

        # Vérifie si ffmpeg est dispo
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            ffmpeg_ok = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            ffmpeg_ok = False

        if ffmpeg_ok:
            # Export WAV temporaire → convertit en M4A avec ffmpeg
            wav_tmp = free_path("tmp.wav")
            audio_segment.export(wav_tmp, format="wav")
            m4a_path = free_path("m4a")
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", wav_tmp,
                     "-c:a", "aac", "-b:a", "128k", m4a_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                os.remove(wav_tmp)
                saved_path = m4a_path
            except subprocess.CalledProcessError:
                # Conversion AAC échouée → garde le WAV
                os.rename(wav_tmp, free_path("wav"))
                saved_path = free_path("wav")
        else:
            # Pas de ffmpeg → WAV directement (pydub natif)
            wav_path = free_path("wav")
            audio_segment.export(wav_path, format="wav")
            saved_path = wav_path

        CHAPTERS_LIST.append([saved_path, display_title, len(CHAPTERS_LIST)])
        save_chapters_json(current_book, CHAPTERS_LIST)

        ext = os.path.splitext(saved_path)[1].upper()
        return f"✓  « {display_title} » a bien été enregistré {ext} 🌸"

    except Exception as ex:
        return f"❌  Quelque chose n'a pas fonctionné : {ex}"


def delete_chapter(selected_index):
    if selected_index is None:
        return "⚠️  Clique d'abord sur un chapitre dans la liste.", get_chapters_display(), None
    if current_book is None:
        return "⚠️  Aucun livre ouvert.", get_chapters_display(), None

    try:
        idx   = int(selected_index)
        entry = normalize_entry(CHAPTERS_LIST[idx])
        fp    = entry_path(entry)
        title = entry_title(entry)

        if os.path.exists(fp):
            os.remove(fp)

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
        entry = normalize_entry(e)
        fp    = entry_path(entry)
        title = entry_title(entry)

        if os.path.exists(fp):
            try:
                seg      = AudioSegment.from_file(fp)
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
    CHAPTERS_LIST[idx], CHAPTERS_LIST[idx - 1] = CHAPTERS_LIST[idx - 1], CHAPTERS_LIST[idx]
    save_chapters_json(current_book, CHAPTERS_LIST)
    return get_chapters_display(), idx - 1


def move_chapter_down(selected_index):
    if selected_index is None or current_book is None:
        return get_chapters_display(), selected_index
    idx = int(selected_index)
    if idx >= len(CHAPTERS_LIST) - 1:
        return get_chapters_display(), selected_index
    CHAPTERS_LIST[idx], CHAPTERS_LIST[idx + 1] = CHAPTERS_LIST[idx + 1], CHAPTERS_LIST[idx]
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
    idx = selection.index[0]
    fp  = entry_path(normalize_entry(CHAPTERS_LIST[idx]))
    return (fp, idx) if os.path.exists(fp) else (None, None)


# ============================================================
#  Export M4B
#  FIX Windows : le fichier concat.txt utilise des chemins
#  avec forward-slashes et guillemets doubles (syntaxe ffmpeg
#  sur Windows), et on passe shell=False avec liste d'args.
# ============================================================

def export_m4b():
    if current_book is None:
        return "⚠️  Ouvre d'abord un livre !"
    if not CHAPTERS_LIST:
        return "⚠️  Il n'y a encore aucun chapitre dans ce livre."

    try:
        out_audio  = audio_dir(current_book)
        out_export = export_dir(current_book)

        output_m4b = os.path.join(out_export, f"{current_book}.m4b")
        counter    = 1
        while os.path.exists(output_m4b):
            output_m4b = os.path.join(out_export, f"{current_book}{counter}.m4b")
            counter += 1

        concat_file   = os.path.join(out_audio, "concat.txt")
        metadata_file = os.path.join(out_audio, "metadata.txt")

        # ── concat.txt ──────────────────────────────────────
        # ffmpeg attend des forward-slashes même sur Windows,
        # et les chemins sont entourés de guillemets simples
        # SAUF si le chemin contient une apostrophe → on échappe
        # différemment selon l'OS.
        with open(concat_file, "w", encoding="utf-8") as f:
            for e in CHAPTERS_LIST:
                # Normalise en forward-slashes (ffmpeg les accepte partout)
                p = os.path.abspath(entry_path(normalize_entry(e))).replace("\\", "/")
                if IS_WINDOWS:
                    # Sur Windows, ffmpeg accepte les guillemets doubles
                    p_escaped = p.replace("'", "\\'")
                    f.write(f"file '{p_escaped}'\n")
                else:
                    p_escaped = p.replace("'", "'\\''")
                    f.write(f"file '{p_escaped}'\n")

        # ── metadata.txt ─────────────────────────────────────
        total_ms = 0
        with open(metadata_file, "w", encoding="utf-8") as f:
            f.write(";FFMETADATA1\n")
            for e in CHAPTERS_LIST:
                entry = normalize_entry(e)
                seg   = AudioSegment.from_file(entry_path(entry))
                dur   = int(seg.duration_seconds * 1000)
                t     = (entry_title(entry)
                         .replace("\\", "\\\\")
                         .replace("=",  "\\=")
                         .replace(";",  "\\;")
                         .replace("#",  "\\#")
                         .replace("\n", " "))
                f.write(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={total_ms}\nEND={total_ms+dur}\ntitle={t}\n")
                total_ms += dur

        # ── Appel ffmpeg (shell=False → pas de problème de quoting shell) ──
        subprocess.run(
            ["ffmpeg", "-y",
             "-f", "concat", "-safe", "0", "-i", concat_file,
             "-i", metadata_file,
             "-map_metadata", "1", "-c", "copy", output_m4b],
            check=True
        )
        return f"✓  Ton livre audio est prêt ! Tu le trouveras ici : {output_m4b} 🎉"

    except FileNotFoundError:
        return "❌  ffmpeg est introuvable. Installe-le depuis https://ffmpeg.org et ajoute-le au PATH."
    except Exception as ex:
        return f"❌  Quelque chose n'a pas fonctionné : {ex}"


# ============================================================
#  Interface Gradio
# ============================================================

with gr.Blocks(title="Studio de Mamie 🎧", css=CUSTOM_CSS, theme=gr.themes.Base()) as app:

    # ── En-tête ──────────────────────────────────────────────
    gr.HTML("""
        <div style="padding:32px 0 24px 0;">
            <div class="app-title">Studio de Mamie 🎧</div>
            <div class="app-subtitle">
                Enregistre ta voix · Crée tes histoires · Écoute ton livre
            </div>
        </div>
    """)

    # ── Gestion des livres ───────────────────────────────────
    with gr.Accordion("📚  Mes livres audio", open=False):
        book_badge = gr.HTML(_book_badge())
        gr.HTML('<div style="height:10px"></div>')

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
            <div class="folder-tree">
                <div class="folder-tree-title">Où sont sauvegardés tes fichiers</div>
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

        # ── Colonne gauche ───────────────────────────────────
        with gr.Column(scale=1):
            gr.HTML('<div class="section-title">🎙  Ma voix</div>')

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
            gr.HTML('<div class="section-title">📦  Mon livre fini</div>')

            export_button = gr.Button("🎉  Créer mon livre audio", variant="primary")
            export_status = gr.Textbox(
                label="Ton livre est prêt ?",
                interactive=False,
                elem_classes=["status-box"]
            )

        # ── Colonne droite ───────────────────────────────────
        with gr.Column(scale=2):
            gr.HTML('<div class="section-title">📋  Mes chapitres enregistrés</div>')

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

            gr.HTML('<div class="section-title-sm">🎧  Écouter ce chapitre</div>')
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