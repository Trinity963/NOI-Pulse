#!/usr/bin/env python3
import os
import tkinter as tk
import json
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText


WORKSPACE = os.path.join(os.getcwd(), "engine")

SESSION_DIR = os.path.join(os.getcwd(), ".session")
os.makedirs(SESSION_DIR, exist_ok=True)


class TrinityCanvas(tk.Toplevel):

    def __init__(self):
        super().__init__()

        self.title("TrinityCanvas IDE")
        self.geometry("1200x750")
        self.configure(bg="#0e0014")

        self.tabs = {}
        self.active = None

        self._build_ui()
        self.load_file_tree()
        
        self.bind("<Control-s>", lambda e: self.save_current())
        self.protocol("WM_DELETE_WINDOW", self._shutdown)
        
        
    def _shutdown(self):
        self._write_auto_report()
        self.tabs.clear()
        self.destroy()

    def _write_auto_report(self):
        import json
        from datetime import datetime
        module_path = getattr(self, '_module_path', None)
        if not module_path:
            return
        notes_dir = os.path.join(module_path, 'notes')
        os.makedirs(notes_dir, exist_ok=True)
        app = getattr(self, '_app', None)
        if app:
            memory = getattr(app, 'memory', [])
            lines = [f"{r}: {m}" for r, m in memory[-20:]]
            summary = '\n'.join(lines) if lines else 'No session activity recorded.'
        else:
            summary = 'Canvas closed — no app memory available.'
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(notes_dir, f'{ts}_report.md')
        module_name = getattr(self, '_module_name', 'Unknown')
        with open(report_path, 'w') as f:
            f.write(f'# Module Report: {module_name}\n')
            f.write(f'**Generated:** {datetime.utcnow().isoformat()}\n\n')
            f.write('## Session Activity\n\n')
            f.write(summary + '\n')
        log_path = os.path.join(module_path, 'project_log.jsonl')
        with open(log_path, 'a') as f:
            f.write(json.dumps({'ts': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'), 'project': module_name, 'source': 'auto_shutdown', 'summary': f'Auto-report saved: {ts}_report.md', 'tags': ['auto_report']}) + '\n')
        print(f'[TrinityCanvas] Auto-report saved → {report_path}')

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self):

        root = tk.Frame(self, bg="#0e0014")
        root.pack(fill="both", expand=True)

        # LEFT PANEL
        left = tk.Frame(root, bg="#150020", width=260)
        left.pack(side="left", fill="y")

        self.tree = ttk.Treeview(left)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # RIGHT PANEL
        right = tk.Frame(root, bg="#0e0014")
        right.pack(side="left", fill="both", expand=True)

        # TAB BAR
        self.tab_bar = tk.Frame(right, bg="#150020")
        self.tab_bar.pack(fill="x")

        # EDITOR AREA
        self.editor_area = tk.Frame(right, bg="#0e0014")
        self.editor_area.pack(fill="both", expand=True)

        # TREE MENU
        self.tree_menu = tk.Menu(self, tearoff=0)
        self.tree_menu.add_command(label="Open", command=self._tree_open)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Rename", command=self._tree_rename)
        self.tree_menu.add_command(label="Delete", command=self._tree_delete)

        self.tree.bind("<Button-3>", self._show_tree_menu)

        # MENU BAR
        menu = tk.Menu(self)

        file_menu = tk.Menu(menu, tearoff=0)

        file_menu.add_command(label="New File", command=self.new_file)
        file_menu.add_command(label="Open File", command=self.open_file_dialog)
        file_menu.add_command(label="Save", command=self.save_current)
        file_menu.add_command(label="Save As", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Clear Session", command=self.clear_session)

        menu.add_cascade(label="File", menu=file_menu)

        self.config(menu=menu)

    # ---------------------------------------------------------
    # TREE MENU
    # ---------------------------------------------------------

    def _show_tree_menu(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)
        self.tree.focus(item)
        self._ctx_item = item
        self.tree_menu.post(event.x_root, event.y_root)

    def _tree_open(self):
        item = getattr(self, '_ctx_item', None) or self.tree.focus()
        values = self.tree.item(item, "values")
        if not values:
            if self.tree.get_children(item):
                self.tree.item(item, open=not self.tree.item(item, "open"))
            return
        path = values[0]
        if os.path.isfile(path):
            self.open_file(path)
        elif os.path.isdir(path):
            self.set_workspace(path, os.path.basename(path))

    def _tree_rename(self):
        item = getattr(self, '_ctx_item', None) or self.tree.focus()
        values = self.tree.item(item, "values")

        if not values:
            return

        old_path = values[0]

        new_name = simpledialog.askstring("Rename", "New filename:")

        if not new_name:
            return

        new_path = os.path.join(os.path.dirname(old_path), new_name)

        os.rename(old_path, new_path)

        self.load_file_tree()

    def _tree_delete(self):
        item = getattr(self, '_ctx_item', None) or self.tree.focus()
        values = self.tree.item(item, "values")

        if not values:
            return

        path = values[0]

        confirm = messagebox.askyesno("Delete", f"Delete {os.path.basename(path)} ?")

        if not confirm:
            return

        os.remove(path)

        self.load_file_tree()

    # ---------------------------------------------------------
    # FILE TREE
    # ---------------------------------------------------------

    def set_workspace(self, path, label=None):
        global WORKSPACE
        WORKSPACE = path
        os.makedirs(path, exist_ok=True)
        self._module_path = os.path.dirname(path) if os.path.basename(path) == 'build' else path
        self._module_name = label or os.path.basename(self._module_path)
        self.load_file_tree(label or os.path.basename(path))
        self.lift()

    def load_file_tree(self, label=None):
        self.tree.delete(*self.tree.get_children())
        display = label or os.path.basename(WORKSPACE) or "engine"
        root = self.tree.insert("", "end", text=display, open=True)
        self._build_tree(WORKSPACE, root)

    def _build_tree(self, path, parent):

        try:
            entries = sorted(os.listdir(path))
        except:
            return

        for item in entries:

            if item == "__pycache__" or item.endswith(".pyc"):
                continue

            full = os.path.join(path, item)

            if os.path.isdir(full):

                node = self.tree.insert(parent, "end", text=item, open=False)
                self._build_tree(full, node)

            else:

                self.tree.insert(parent, "end", text=item, values=[full])

    def _on_tree_select(self, event):

        item = self.tree.focus()

        values = self.tree.item(item, "values")

        if not values:
            return

        path = values[0]

        if os.path.isfile(path):
            self.open_file(path)

    # ---------------------------------------------------------
    # TAB SYSTEM
    # ---------------------------------------------------------

    def new_file(self):

        name = "untitled.py"
        self._open_tab(name, "")

    def open_file_dialog(self):

        path = filedialog.askopenfilename(initialdir=WORKSPACE)

        if path:
            self.open_file(path)

    def open_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        name = os.path.basename(path)

        IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"}
        AUDIO_EXTS = {".mp3", ".wav", ".flac", ".ogg", ".aac"}
        VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
        ARCHIVE_EXTS = {".zip", ".tar", ".gz", ".7z", ".rar", ".bz2"}
        BINARY_EXTS = {".exe", ".app", ".bin", ".dll", ".so"}

        try:
            if ext in IMAGE_EXTS:
                self._open_image_tab(name, path)
            elif ext == ".pdf":
                self._open_pdf_tab(name, path)
            elif ext in {".docx"}:
                self._open_docx_tab(name, path)
            elif ext in AUDIO_EXTS:
                self._open_audio_tab(name, path)
            elif ext in VIDEO_EXTS:
                self._open_video_tab(name, path)
            elif ext in ARCHIVE_EXTS:
                self._open_archive_tab(name, path)
            elif ext in BINARY_EXTS:
                self._open_binary_tab(name, path)
            else:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                self._open_tab(name, content, path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def _open_image_tab(self, name, path):
        from PIL import Image, ImageTk
        img = Image.open(path)
        img.thumbnail((900, 650))
        photo = ImageTk.PhotoImage(img)
        frame = tk.Frame(self.editor_area, bg="#120016")
        lbl = tk.Label(frame, image=photo, bg="#120016")
        lbl.image = photo
        lbl.pack(expand=True)
        info = tk.Label(frame, text=f"{name}  |  {img.size[0]}x{img.size[1]}  |  {os.path.getsize(path)//1024} KB",
                        bg="#120016", fg="#b347ff", font=("JetBrains Mono", 10))
        info.pack()
        self._open_widget_tab(name, frame, path)

    def _open_pdf_tab(self, name, path):
        try:
            import PyPDF2
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            text = f"[PDF read error: {e}]"
        self._open_tab(name, text or "[No text extracted]", path)

    def _open_docx_tab(self, name, path):
        try:
            import docx
            doc = docx.Document(path)
            text = "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            text = f"[DOCX read error: {e}]"
        self._open_tab(name, text or "[Empty document]", path)

    def _open_audio_tab(self, name, path):
        self._open_vlc_tab(name, path, mode="audio")

    def _open_video_tab(self, name, path):
        self._open_vlc_tab(name, path, mode="video")

    def _open_vlc_tab(self, name, path, mode="audio"):
        import vlc
        from mutagen import File as MutagenFile

        frame = tk.Frame(self.editor_area, bg="#0e0014")

        # --- Metadata ---
        try:
            meta = MutagenFile(path)
            duration = int(meta.info.length) if meta and hasattr(meta, "info") else 0
            mins, secs = divmod(duration, 60)
            meta_str = f"{name}  |  {os.path.getsize(path)//1024} KB  |  {mins}:{secs:02d}"
        except:
            meta_str = f"{name}  |  {os.path.getsize(path)//1024} KB"

        tk.Label(frame, text=meta_str, bg="#0e0014", fg="#b347ff",
                 font=("JetBrains Mono", 10)).pack(pady=(10,4))

        # --- Video surface (only for video) ---
        if mode == "video":
            video_frame = tk.Frame(frame, bg="#000000", width=800, height=450)
            video_frame.pack(pady=4)
            video_frame.pack_propagate(False)
        else:
            video_frame = None

        # --- VLC instance ---
        instance = vlc.Instance("--no-xlib", "--vout=x11", "--avcodec-hw=none")
        player = instance.media_player_new()
        media = instance.media_new(path)
        player.set_media(media)

        if video_frame:
            frame.update()
            player.set_xwindow(video_frame.winfo_id())

        # --- Progress bar ---
        progress_var = tk.DoubleVar()
        progress = tk.Scale(frame, variable=progress_var, from_=0, to=1000,
                            orient="horizontal", length=700,
                            bg="#0e0014", fg="#b347ff", troughcolor="#260033",
                            highlightthickness=0, showvalue=False)
        progress.pack(pady=6)

        # --- Time label ---
        time_label = tk.Label(frame, text="0:00 / 0:00", bg="#0e0014", fg="#888",
                              font=("JetBrains Mono", 10))
        time_label.pack()

        # --- Controls ---
        ctrl = tk.Frame(frame, bg="#0e0014")
        ctrl.pack(pady=8)

        def play():
            player.play()

        def pause():
            player.pause()

        def stop():
            player.pause()
            frame.after(100, lambda: (
                player.stop(),
                progress_var.set(0),
                time_label.config(text="0:00 / 0:00")
            ))

        def seek(val):
            if player.get_length() > 0:
                player.set_time(int(float(val) / 1000 * player.get_length()))

        progress.bind("<ButtonRelease-1>", lambda e: seek(progress_var.get()))

        btn_cfg = dict(bg="#260033", fg="#b347ff", font=("JetBrains Mono", 11, "bold"),
                       relief="ridge", padx=10)

        tk.Button(ctrl, text="▶ Play",  command=play,  **btn_cfg).pack(side="left", padx=4)
        tk.Button(ctrl, text="⏸ Pause", command=pause, **btn_cfg).pack(side="left", padx=4)
        tk.Button(ctrl, text="⏹ Stop",  command=stop,  **btn_cfg).pack(side="left", padx=4)

        # --- Volume ---
        vol_frame = tk.Frame(frame, bg="#0e0014")
        vol_frame.pack(pady=4)
        tk.Label(vol_frame, text="Vol:", bg="#0e0014", fg="#888",
                 font=("JetBrains Mono", 10)).pack(side="left")
        vol_var = tk.IntVar(value=80)
        player.audio_set_volume(80)
        vol_slider = tk.Scale(vol_frame, variable=vol_var, from_=0, to=100,
                              orient="horizontal", length=200,
                              bg="#0e0014", fg="#b347ff", troughcolor="#260033",
                              highlightthickness=0, showvalue=True,
                              command=lambda v: player.audio_set_volume(int(v)))
        vol_slider.pack(side="left", padx=6)

        # --- Ticker ---
        def _tick():
            if not frame.winfo_exists():
                return
            try:
                length = player.get_length()
                current = player.get_time()
                if length > 0:
                    progress_var.set(current / length * 1000)
                    cm, cs = divmod(current // 1000, 60)
                    lm, ls = divmod(length // 1000, 60)
                    time_label.config(text=f"{cm}:{cs:02d} / {lm}:{ls:02d}")
            except:
                pass
            frame.after(500, _tick)

        frame.after(500, _tick)
        frame._vlc_player = player

        self._open_widget_tab(name, frame, path)

    def _open_archive_tab(self, name, path):
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".zip":
                import zipfile
                with zipfile.ZipFile(path) as z:
                    contents = "\n".join(z.namelist())
            elif ext in {".tar", ".gz", ".bz2"}:
                import tarfile
                with tarfile.open(path) as t:
                    contents = "\n".join(t.getnames())
            else:
                contents = f"[Archive type {ext} — contents listing not supported]"
        except Exception as e:
            contents = f"[Archive read error: {e}]"
        self._open_tab(name, f"Archive: {name}\n{'='*40}\n{contents}", path)

    def _open_binary_tab(self, name, path):
        try:
            with open(path, "rb") as f:
                raw = f.read(512)
            hex_preview = " ".join(f"{b:02x}" for b in raw)
        except Exception as e:
            hex_preview = f"[Binary read error: {e}]"
        self._open_tab(name, f"Binary: {name}\nSize: {os.path.getsize(path)//1024} KB\n\nHex preview (512 bytes):\n{hex_preview}", path)

    def _open_widget_tab(self, name, widget, path=None):
        if name in self.tabs:
            self._switch_tab(name)
            return
        tab_frame = tk.Frame(self.tab_bar, bg="#260033")
        label = tk.Label(tab_frame, text=name, bg="#260033", fg="#b347ff")
        label.pack(side="left", padx=(6,2))
        close_btn = tk.Label(tab_frame, text=" × ", bg="#260033", fg="#ff66ff", cursor="hand2")
        close_btn.pack(side="right")
        tab_frame.pack(side="left", padx=4, pady=4)
        widget.tab_frame = tab_frame
        self.tabs[name] = {"tab": tab_frame, "editor": widget, "path": path, "widget": True}
        close_btn.bind("<Button-1>", lambda e, n=name: self._close_tab(n))
        tab_frame.bind("<Button-2>", lambda e, n=name: self._close_tab(n))
        self._switch_tab(name)

    def _open_tab(self, name, content, path=None):

        if name in self.tabs:
            self._switch_tab(name)
            return

        # --- TAB FRAME ---
        tab_frame = tk.Frame(self.tab_bar, bg="#260033")

        label = tk.Label(
            tab_frame,
            text=name,
            bg="#260033",
            fg="#b347ff"
        )
        label.pack(side="left", padx=(6,2))

        close_btn = tk.Label(
            tab_frame,
            text=" × ",
            bg="#260033",
            fg="#ff66ff",
            cursor="hand2"
        )
        close_btn.pack(side="right")

        tab_frame.pack(side="left", padx=4, pady=4)

        # --- EDITOR ---
        editor = ScrolledText(
            self.editor_area,
            bg="#120016",
            fg="#e0c8ff",
            insertbackground="white",
            font=("JetBrains Mono", 12)
        )

        editor.insert("end", content)

        # --- TAB DATA ---
        self.tabs[name] = {
            "tab": tab_frame,
            "editor": editor,
            "path": path
        }
 
        tab_frame.bind("<Button-2>", lambda e, n=name: self._close_tab(n))
       
        # --- CLOSE BUTTON ---
        close_btn.bind("<Button-1>", lambda e, n=name: self._close_tab(n))
        
        # --- SWITCH TO TAB ---
        self._switch_tab(name)
        
        
        
            

    def _switch_tab(self, name):
        for t in self.tabs.values():
            try:
                t["editor"].pack_forget()
            except:
                pass
        tab = self.tabs[name]
        editor = tab["editor"]
        if editor.winfo_exists():
            if tab.get("widget"):
                editor.pack(fill="both", expand=True)
            else:
                editor.pack(fill="both", expand=True)
        self.active = name
        

    def _close_tab(self, name):

        if name not in self.tabs:
            return

        tab = self.tabs[name]

        try:
            tab["editor"].pack_forget()
            tab["editor"].destroy()
        except:
            pass

        try:
            tab["tab"].destroy()
        except:
            pass

        del self.tabs[name]

        # activate another tab if one exists
        if self.tabs:
            next_tab = list(self.tabs.keys())[-1]
            self._switch_tab(next_tab)
        else:
            self.active = None
        

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    def save_current(self):
        if not self.active:
            return
        tab = self.tabs[self.active]
        if tab.get("widget"):
            return
        content = tab["editor"].get("1.0", "end")

        path = tab["path"]

        if not path:
            return self.save_as()

        with open(path, "w") as f:
            f.write(content)

    def save_as(self):

        if not self.active:
            return

        tab = self.tabs[self.active]

        content = tab["editor"].get("1.0", "end")

        path = filedialog.asksaveasfilename(
            initialdir=WORKSPACE,
            defaultextension=".py"
        )

        if path:

            with open(path, "w") as f:
                f.write(content)

            tab["path"] = path

    # ---------------------------------------------------------
    # SESSION
    # ---------------------------------------------------------

    def clear_session(self):

        for tab in self.tabs.values():

            try:
                tab["editor"].pack_forget()
            except:
                pass

            try:
                tab["btn"].destroy()
            except:
                pass

        self.tabs = {}
        self.active = None

# ---------------------------------------------------------
# MINI TRINI HOOK
# ---------------------------------------------------------

_canvas_instance = None

MODULES_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AI_Core", "trinity_canvas", "modules")


def create_module(name, app=None):
    import json
    from datetime import datetime
    module_path = os.path.join(MODULES_ROOT, name)
    for subfolder in ("artifacts", "build", "memory", "notes"):
        os.makedirs(os.path.join(module_path, subfolder), exist_ok=True)
    log_entry = {
        "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
        "project": name,
        "source": "auto_intent",
        "summary": f"Module initialized: {name}",
        "tags": ["module_init"]
    }
    log_path = os.path.join(module_path, "project_log.jsonl")
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    canvas = open_canvas(app)
    canvas.set_workspace(os.path.join(module_path, "build"), name)
    return module_path


def set_canvas_workspace(path, label=None):
    canvas = open_canvas()
    canvas.set_workspace(path, label)


def open_canvas(app=None):
    global _canvas_instance
    if _canvas_instance is None or not _canvas_instance.winfo_exists():
        _canvas_instance = TrinityCanvas()
    else:
        _canvas_instance.lift()
    if app is not None:
        _canvas_instance._app = app
    return _canvas_instance


def send_to_canvas(content, filename="output.py"):

    canvas = open_canvas()

    canvas._open_tab(filename, content)