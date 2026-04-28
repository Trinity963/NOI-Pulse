# core/triggers_canvas.py
from core.triggers import Trigger
from core.context import Context

class CanvasTrigger(Trigger):
    """
    Fires when a file is dropped onto the canvas.
    Injects canvas context and file path into the flow context.
    """
    def __init__(self, canvas_context=None, file_path=None):
        self.canvas_context = canvas_context or {}
        self.file_path = file_path or ""

    def fire(self, callback):
        ctx = Context()
        ctx.set("trigger", "canvas_drop")
        ctx.set("file_path", self.file_path)
        ctx.set("canvas_context", self.canvas_context)
        # Build a readable summary for the LLM prompt
        summaries = []
        for name, info in self.canvas_context.items():
            t = info.get("type", "?")
            if t == "image":
                summaries.append(f"{name}: image {info.get('width')}x{info.get('height')}px, {info.get('size_kb')}KB")
            elif t == "text":
                summaries.append(f"{name}: text file, {info.get('lines')} lines\n{info.get('description','')}")
            elif t == "pdf":
                summaries.append(f"{name}: PDF, {info.get('pages')} pages\n{info.get('description','')}")
            elif t == "docx":
                summaries.append(f"{name}: Word doc, {info.get('paragraphs')} paragraphs\n{info.get('description','')}")
            elif t == "archive":
                summaries.append(f"{name}: archive, {info.get('file_count')} files")
            else:
                summaries.append(f"{name}: {t}")
        prompt = "A file was dropped on the canvas.\n\n" + "\n---\n".join(summaries) + "\n\nBriefly describe what you see and offer one useful action."
        ctx.set("prompt", prompt)
        callback(ctx)
