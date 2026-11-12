"""Mask Map Generator for Unity HDRP (Lit shader).

Packs grayscale textures into:
  - Mask Map:   R Metallic, G Ambient Occlusion, B Detail Mask, A Smoothness
  - Detail Map: R Albedo (desaturated), G Normal Y, B Smoothness, A Normal X
and unpacks any RGBA texture back into its four channels.
"""

__version__ = "1.1.0"  # must match the release tag (vX.Y.Z): the release workflow checks it

import json
import os
import re
import ssl
import threading
import traceback
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk, UnidentifiedImageError

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # drag & drop is optional: clicking a preview always works
    DND_FILES = TkinterDnD = None

try:
    import certifi
except ImportError:  # optional: CA bundle for Pythons that ship none (e.g. the frozen macOS app)
    certifi = None


# ==================== CONSTANTS ====================

GITHUB_REPO = "sanliuk/MaskMap-Generator-Unity-HDRP-Lit-Packer"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
UPDATE_TIMEOUT_S = 5

OPEN_TYPES = [
    ("Image files", "*.png *.jpg *.jpeg *.tga *.tif *.tiff *.bmp"),
    ("All files", "*.*"),
]
SAVE_TYPES = [("PNG", "*.png"), ("TGA", "*.tga"), ("TIFF", "*.tif")]
SAVE_FORMATS = {".png": "PNG", ".tga": "TGA", ".tif": "TIFF", ".tiff": "TIFF"}

RESOLUTIONS = ["Source", "256", "512", "1024", "2048", "4096", "8192"]
MAX_RESOLUTION = 16384
Image.MAX_IMAGE_PIXELS = MAX_RESOLUTION * MAX_RESOLUTION

PREVIEW_SIZE = 96
OUTPUT_PREVIEW_SIZE = 150
SOURCE_PREVIEW_SIZE = 200
FONT = "Segoe UI"

COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_card": "#16213e",
    "bg_input": "#0f3460",
    "accent": "#0078d4",
    "accent_hover": "#1e90ff",
    "accent_success": "#00c853",
    "accent_warning": "#ff9800",
    "accent_danger": "#e53935",
    "text_primary": "#ffffff",
    "text_secondary": "#b0b0b0",
    "text_muted": "#7a8aa6",
    "border": "#2d4a6f",
    "preview_bg": "#0a0a1a",
    "channel_r": "#ff5252",
    "channel_g": "#69f0ae",
    "channel_b": "#448aff",
    "channel_a": "#b388ff",
}

# (channel, name, hint, value used when no texture is loaded)
MASK_CHANNELS = [
    ("R", "Metallic", "Black = non-metal", 0.0),
    ("G", "Ambient Occlusion", "White = no occlusion", 1.0),
    ("B", "Detail Mask", "Where the Detail Map shows", 1.0),
    ("A", "Smoothness", "Roughness map? Tick Invert", 0.5),
]
DETAIL_CHANNELS = [
    ("R", "Detail Albedo", "Desaturated automatically", 0.5),
    ("G", "Normal Y", "Normal map green channel", 0.5),
    ("B", "Detail Smoothness", "0.5 = neutral", 0.5),
    ("A", "Normal X", "Normal map red channel", 0.5),
]
UNPACK_CHANNELS = [
    ("R", "Red", "Mask: Metallic · Detail: Albedo"),
    ("G", "Green", "Mask: AO · Detail: Normal Y"),
    ("B", "Blue", "Mask: Detail Mask · Detail: Smoothness"),
    ("A", "Alpha", "Mask: Smoothness · Detail: Normal X"),
]

# Hover help: what each channel does in the HDRP Lit shader
MASK_TIPS = {
    "R": "Metallic. White = metal, black = non-metal.\n"
         "Most real materials are either fully 0 or fully 1.",
    "G": "Ambient Occlusion. White = fully lit, dark = occluded cavities and creases.",
    "B": "Detail Mask: where the Detail Map is applied.\n"
         "White = full detail, black = none. Leave it empty (1) if you don't use a Detail Map.",
    "A": "Smoothness. White = glossy, black = rough.\n"
         "Most tools export Roughness: load it here and tick Invert.",
}
DETAIL_TIPS = {
    "R": "Detail albedo, desaturated automatically.\n"
         "0.5 grey = no change; lighter or darker values brighten or darken the base color.",
    "G": "Green channel of the detail normal map.\n"
         "Use 'Load Normal Map…' to fill Normal X and Normal Y at once.\n"
         "DirectX normal map? Tick Invert here.",
    "B": "Detail smoothness. 0.5 = no change, higher = smoother, lower = rougher.",
    "A": "Red channel of the detail normal map.\n"
         "Use 'Load Normal Map…' to fill Normal X and Normal Y at once.",
}
TIP_BROWSE = "Choose a texture file (PNG, JPG, TGA, TIFF, BMP; 8 or 16-bit)."
TIP_CLEAR = "Remove the texture. The 'If empty' value is used instead."
TIP_INVERT = "Invert the texture (black ↔ white).\nUse it to turn a Roughness map into Smoothness."
TIP_FILL = "Value used for this channel when no texture is loaded.\n0 = black, 1 = white."
TIP_RESOLUTION = ("Source keeps the size of your largest texture.\n"
                  "A number sets the longest side; non-square textures keep their proportions.")
TIP_GENERATE = "Pack the four channels into one RGBA texture and preview it."
TIP_SAVE = ("Save the result as PNG, TGA or TIFF.\n"
            "Available after Generate. Changing any input requires generating again.")
TIP_OUT_RGB = "Red, green and blue channels of the result."
TIP_OUT_ALPHA = "Alpha channel of the result, shown in grayscale."
TIP_NORMAL = ("Load a tangent-space normal map:\n"
              "red → Normal X (A), green → Normal Y (G).")
TIP_UNPACK_LOAD = "Load an RGBA texture (e.g. an existing Mask Map) to split into its four channels."
TIP_UNPACK_CLEAR = "Remove the loaded texture."
TIP_UNPACK_RES = "Size used when saving the channels. Source = original size."
TIP_SAVE_ALL = "Save all four channels into a folder as <name>_R/G/B/A.png."
TIP_SAVE_CHANNEL = "Save this channel as a grayscale image (PNG, TGA or TIFF)."


# ==================== IMAGE HELPERS (no UI) ====================

def to_gray(img):
    """Return an 8-bit grayscale copy. 16-bit and float data is scaled, not clipped."""
    if img.mode.startswith("I;16"):
        img = img.convert("I")
        return img.point(lambda v: v * (1 / 257) + 0.5).convert("L")
    if img.mode == "I":
        low, high = img.getextrema()
        if high > 255:  # 16-bit data stored in a 32-bit image
            return img.point(lambda v: v * (1 / 257) + 0.5).convert("L")
        return img.convert("L")
    if img.mode == "F":  # float data, expected range 0..1
        return img.point(lambda v: v * 255 + 0.5).convert("L")
    return img.convert("L")


def to_rgb(img):
    if img.mode.startswith("I") or img.mode == "F":
        return to_gray(img).convert("RGB")
    return img.convert("RGB")


def to_rgba(img):
    if img.mode.startswith("I") or img.mode == "F":
        return to_gray(img).convert("RGBA")
    return img.convert("RGBA")


def has_alpha(img):
    return img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)


def parse_resolution(text):
    """'Source' -> None (keep the source size), '2048' -> 2048."""
    text = text.strip()
    if text.lower() in ("", "source"):
        return None
    try:
        value = int(text)
    except ValueError:
        raise ValueError(f"Resolution must be a whole number or 'Source' (got '{text}').") from None
    if not 1 <= value <= MAX_RESOLUTION:
        raise ValueError(f"Resolution must be between 1 and {MAX_RESOLUTION}.")
    return value


def target_size(sources, resolution):
    """Output size: the largest source, optionally scaled so its longest side = resolution.
    Non-square textures keep their aspect ratio."""
    if sources:
        ref_w, ref_h = max((im.size for im in sources), key=lambda s: s[0] * s[1])
    elif resolution is None:
        raise ValueError("Load at least one texture, or pick a resolution instead of 'Source'.")
    else:
        return resolution, resolution
    if resolution is None:
        return ref_w, ref_h
    scale = resolution / max(ref_w, ref_h)
    return max(1, round(ref_w * scale)), max(1, round(ref_h * scale))


def pack_channels(sources, inverts, fills, resolution):
    """Merge four grayscale sources into one RGBA image.

    sources:  {"R": Image or None, ...}  - never modified
    inverts:  {"R": bool, ...}           - only applies to loaded textures
    fills:    {"R": 0..1, ...}           - value used for channels with no texture
    Returns (image, warning or None).
    """
    loaded = [im for im in sources.values() if im is not None]
    size = target_size(loaded, resolution)
    aspect = size[0] / size[1]
    stretched = any(abs(im.size[0] / im.size[1] - aspect) > 0.01 for im in loaded)

    bands = []
    for ch in "RGBA":
        src = sources[ch]
        if src is None:
            bands.append(Image.new("L", size, round(fills[ch] * 255)))
            continue
        band = src if src.size == size else src.resize(size, Image.Resampling.LANCZOS)
        if inverts[ch]:
            band = ImageOps.invert(band)
        bands.append(band)

    warning = "Some textures have a different aspect ratio and were stretched." if stretched else None
    return Image.merge("RGBA", bands), warning


def resize_to(img, resolution):
    size = target_size([img], resolution)
    return img if img.size == size else img.resize(size, Image.Resampling.LANCZOS)


def save_image(img, path):
    fmt = SAVE_FORMATS.get(os.path.splitext(path)[1].lower())
    if fmt is None:
        raise ValueError("Unsupported file type. Use .png, .tga or .tif.")
    img.save(path, format=fmt)


def base_name(path):
    """'C:/tex/Rock_Metallic.png' -> 'Rock' (drops the last _suffix)."""
    stem = os.path.splitext(os.path.basename(path))[0]
    head, sep, _ = stem.rpartition("_")
    return head if sep and head else stem


def shorten(text, limit=28):
    return text if len(text) <= limit else text[: limit - 1] + "…"


# ==================== UPDATE CHECK (no UI) ====================

def parse_version(text):
    """'v1.2.0' or '1.2.0' -> (1, 2, 0). Anything else (e.g. '1.2.0-beta') -> None."""
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (text or "").strip())
    return tuple(map(int, match.groups())) if match else None


def is_newer(tag, current=__version__):
    latest, running = parse_version(tag), parse_version(current)
    return bool(latest and running and latest > running)


def latest_release_tag():
    """Tag of the latest GitHub release (e.g. 'v1.2.0'), or None if it can't be checked.
    Meant for a background thread: never raises and never touches the UI."""
    try:
        context = ssl.create_default_context()
        if certifi:
            context.load_verify_locations(certifi.where())
        request = urllib.request.Request(LATEST_RELEASE_API, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"MaskMapGenerator/{__version__}",
        })
        with urllib.request.urlopen(request, timeout=UPDATE_TIMEOUT_S, context=context) as response:
            return json.load(response)["tag_name"]
    except Exception:  # offline, rate-limited, unexpected reply…: the check is best-effort
        return None


# ==================== UI WIDGETS ====================

class Tooltip:
    """Dark tooltip shown below a widget after a short hover."""

    DELAY_MS = 500

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self._after = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")
        widget.bind("<Button-1>", self._hide, add="+")  # <Button-1> bindings shadow <ButtonPress>

    def _schedule(self, _event=None):
        self._cancel()
        self._after = self.widget.after(self.DELAY_MS, self._show)

    def _cancel(self):
        if self._after:
            self.widget.after_cancel(self._after)
            self._after = None

    def _show(self):
        self._after = None
        if self._tip or not self.text or not self.widget.winfo_viewable():
            return
        tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.attributes("-topmost", True)
        tk.Label(tip, text=self.text, bg=COLORS["bg_input"], fg=COLORS["text_primary"],
                 font=(FONT, 9), justify="left", wraplength=340, padx=10, pady=6,
                 highlightthickness=1, highlightbackground=COLORS["accent"]).pack()
        tip.update_idletasks()
        # below the widget, kept inside the app window (works on any monitor)
        top = self.widget.winfo_toplevel()
        w, h = tip.winfo_reqwidth(), tip.winfo_reqheight()
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        x = max(top.winfo_rootx(), min(x, top.winfo_rootx() + top.winfo_width() - w))
        if y + h > top.winfo_rooty() + top.winfo_height():
            y = self.widget.winfo_rooty() - h - 4
        tip.wm_geometry(f"+{x}+{y}")
        self._tip = tip

    def _hide(self, _event=None):
        self._cancel()
        if self._tip:
            self._tip.destroy()
            self._tip = None


def add_tip(text, *widgets):
    for widget in widgets:
        Tooltip(widget, text)


class PreviewBox:
    """Fixed-size image preview. Optionally clickable and a drop target."""

    def __init__(self, parent, size, placeholder, on_click=None):
        self.size = size
        self.placeholder = placeholder
        self._photo = None
        self.frame = tk.Frame(parent, width=size, height=size, bg=COLORS["preview_bg"],
                              highlightthickness=1, highlightbackground=COLORS["border"])
        self.frame.pack_propagate(False)
        self.label = tk.Label(self.frame, text=placeholder, bg=COLORS["preview_bg"],
                              fg=COLORS["text_muted"], font=(FONT, 9), justify="center")
        self.label.pack(fill="both", expand=True)
        if on_click:
            self.label.config(cursor="hand2")
            self.label.bind("<Button-1>", lambda e: on_click())

    def show(self, img):
        thumb = img.copy()  # never shrink the caller's image
        thumb.thumbnail((self.size - 2, self.size - 2), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(thumb)
        self.label.config(image=self._photo, text="")

    def clear(self, text=None):
        self._photo = None
        self.label.config(image="", text=text if text is not None else self.placeholder)

    def highlight(self, on):
        self.frame.config(highlightbackground=COLORS["accent_hover"] if on else COLORS["border"])


def make_card(parent, title):
    """Card with a title bar. Returns (card, header, content)."""
    card = tk.Frame(parent, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1)
    header = tk.Frame(card, bg=COLORS["bg_card"])
    header.pack(fill="x", padx=15, pady=(10, 8))
    tk.Label(header, text=title, bg=COLORS["bg_card"], fg=COLORS["text_primary"],
             font=(FONT, 12, "bold")).pack(side="left")
    tk.Frame(card, bg=COLORS["border"], height=1).pack(fill="x", padx=15)
    content = tk.Frame(card, bg=COLORS["bg_card"])
    content.pack(fill="both", expand=True, padx=15, pady=12)
    return card, header, content


def channel_label(parent, row, channel, name, hint, tip=None):
    """Colored bar + channel letter + name/hint. Returns the info frame (for extra lines)."""
    color = COLORS[f"channel_{channel.lower()}"]
    tk.Frame(parent, bg=color, width=4).grid(row=row, column=0, sticky="ns", pady=4, padx=(0, 10))
    letter = tk.Label(parent, text=channel, bg=COLORS["bg_card"], fg=color,
                      font=(FONT, 13, "bold"), width=2)
    letter.grid(row=row, column=1)
    info = tk.Frame(parent, bg=COLORS["bg_card"])
    info.grid(row=row, column=2, sticky="w", padx=(4, 0))
    name_label = tk.Label(info, text=name, bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                          font=(FONT, 10, "bold"), anchor="w")
    name_label.pack(anchor="w")
    hint_label = tk.Label(info, text=hint, bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                          font=(FONT, 9), anchor="w")
    hint_label.pack(anchor="w")
    if tip:
        add_tip(tip, letter, name_label, hint_label)
    return info


class ChannelSlot:
    """One input channel: preview (click or drop to load), Browse, Clear, Invert, fill value."""

    def __init__(self, app, parent, row, channel, name, hint, fill, on_change, tip):
        self.app = app
        self.name = name
        self.on_change = on_change
        self.image = None  # 8-bit "L" source at full resolution; never modified
        self.path = None
        self.invert = tk.BooleanVar(value=False)
        self.fill = tk.StringVar(value=f"{fill:.2f}")
        self.fill.trace_add("write", lambda *_: self.on_change())

        info = channel_label(parent, row, channel, name, hint, tip)
        self.file_label = tk.Label(info, text="", bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                                   font=(FONT, 8), anchor="w", justify="left")
        self.file_label.pack(anchor="w")
        self.file_tip = Tooltip(self.file_label, "")  # full path of the loaded file

        self.preview = PreviewBox(parent, PREVIEW_SIZE, app.drop_hint, on_click=self.browse)
        self.preview.frame.grid(row=row, column=3, padx=12, pady=4)
        app.enable_drop(self.preview, self.load)
        add_tip(f"{tip}\n\n{app.drop_tip}", self.preview.label)

        controls = tk.Frame(parent, bg=COLORS["bg_card"])
        controls.grid(row=row, column=4, sticky="w")
        line1 = tk.Frame(controls, bg=COLORS["bg_card"])
        line1.pack(anchor="w", pady=(0, 6))
        browse_btn = ttk.Button(line1, text="Browse…", style="Secondary.TButton", command=self.browse)
        browse_btn.pack(side="left")
        self.clear_btn = ttk.Button(line1, text="Clear", style="Secondary.TButton", command=self.clear)
        self.clear_btn.pack(side="left", padx=(6, 0))

        line2 = tk.Frame(controls, bg=COLORS["bg_card"])
        line2.pack(anchor="w")
        self.invert_chk = ttk.Checkbutton(line2, text="Invert", variable=self.invert,
                                          style="Card.TCheckbutton", command=self._on_invert)
        self.invert_chk.pack(side="left")
        fill_label = tk.Label(line2, text="If empty:", bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                              font=(FONT, 9))
        fill_label.pack(side="left", padx=(12, 4))
        self.fill_spin = ttk.Spinbox(line2, from_=0.0, to=1.0, increment=0.05, format="%.2f",
                                     width=5, textvariable=self.fill)
        self.fill_spin.pack(side="left")

        add_tip(TIP_BROWSE, browse_btn)
        add_tip(TIP_CLEAR, self.clear_btn)
        add_tip(TIP_INVERT, self.invert_chk)
        add_tip(TIP_FILL, fill_label, self.fill_spin)
        self._update_state()

    def browse(self):
        path = filedialog.askopenfilename(parent=self.app.root, title=f"Select {self.name} texture",
                                          filetypes=OPEN_TYPES, initialdir=self.app.last_dir)
        if path:
            self.load([path])

    def load(self, paths):
        img = self.app.open_image(paths[0])
        if img is not None:
            self.set_image(to_gray(img), paths[0])
            self.app.status(f"Loaded {os.path.basename(paths[0])} into {self.name}.")

    def set_image(self, img, path, note=""):
        self.image, self.path = img, path
        w, h = img.size
        self.file_label.config(text=f"{shorten(os.path.basename(path) + note)}\n{w} × {h} px")
        self.file_tip.text = os.path.normpath(path)
        self._refresh()
        self._update_state()
        self.on_change()

    def clear(self):
        self.image = self.path = None
        self.file_label.config(text="")
        self.file_tip.text = ""
        self._refresh()
        self._update_state()
        self.on_change()

    def fill_value(self):
        try:
            value = float(self.fill.get().replace(",", "."))
        except ValueError:
            value = -1
        if not 0 <= value <= 1:
            raise ValueError(f"'If empty' value for {self.name} must be a number between 0 and 1.")
        return value

    def _on_invert(self):
        self._refresh()
        self.on_change()

    def _refresh(self):
        if self.image is None:
            self.preview.clear()
        else:
            self.preview.show(ImageOps.invert(self.image) if self.invert.get() else self.image)

    def _update_state(self):
        loaded = self.image is not None
        self.invert_chk.state(["!disabled"] if loaded else ["disabled"])
        self.clear_btn.state(["!disabled"] if loaded else ["disabled"])
        self.fill_spin.state(["disabled"] if loaded else ["!disabled"])


def resolution_picker(parent, tip, on_change=None):
    row = tk.Frame(parent, bg=COLORS["bg_card"])
    label = tk.Label(row, text="Resolution:", bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                     font=(FONT, 10))
    label.pack(side="left")
    var = tk.StringVar(value="Source")
    combo = ttk.Combobox(row, textvariable=var, values=RESOLUTIONS, width=8)
    combo.pack(side="left", padx=(6, 0))
    add_tip(tip, label, combo)
    if on_change:
        var.trace_add("write", lambda *_: on_change())
    return row, var


class PackSection:
    """A tab that packs four grayscale inputs into one RGBA texture."""

    def __init__(self, app, tab, title, output_stem, channels, tips, alpha_name, note):
        self.app = app
        self.title = title
        self.output_stem = output_stem
        self.result = None

        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        inputs_card, self.inputs_header, inputs = make_card(tab, "Inputs")
        inputs_card.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=12)
        inputs.columnconfigure(2, minsize=200)  # loading a file must not shift the controls
        self.slots = {}
        for i, (ch, name, hint, fill) in enumerate(channels):
            self.slots[ch] = ChannelSlot(app, inputs, i, ch, name, hint, fill, self.invalidate, tips[ch])
        tk.Label(inputs, text=note, bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=(FONT, 9),
                 justify="left", anchor="w").grid(row=len(channels), column=0, columnspan=5,
                                                  sticky="w", pady=(10, 0))

        out_card, _, out = make_card(tab, "Output")
        out_card.grid(row=0, column=1, sticky="nsew", padx=(8, 15), pady=12)
        res_row, self.resolution = resolution_picker(out, TIP_RESOLUTION, self.invalidate)
        res_row.pack(anchor="w")

        buttons = tk.Frame(out, bg=COLORS["bg_card"])
        buttons.pack(anchor="w", pady=(12, 12))
        generate_btn = ttk.Button(buttons, text=f"Generate {title}", style="Accent.TButton",
                                  command=self.generate)
        generate_btn.pack(side="left")
        self.save_btn = ttk.Button(buttons, text="Save…", style="Success.TButton", command=self.save)
        self.save_btn.pack(side="left", padx=(8, 0))
        self.save_btn.state(["disabled"])
        add_tip(TIP_GENERATE, generate_btn)
        add_tip(TIP_SAVE, self.save_btn)

        self.rgb_preview = self._output_preview(out, "RGB")
        self.alpha_preview = self._output_preview(out, f"Alpha · {alpha_name}")
        add_tip(TIP_OUT_RGB, self.rgb_preview.label)
        add_tip(TIP_OUT_ALPHA, self.alpha_preview.label)
        self.size_label = tk.Label(out, text="", bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                                   font=(FONT, 9))
        self.size_label.pack(anchor="w", pady=(6, 0))

    def _output_preview(self, parent, caption):
        tk.Label(parent, text=caption, bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 font=(FONT, 9)).pack(anchor="w", pady=(4, 2))
        box = PreviewBox(parent, OUTPUT_PREVIEW_SIZE, "Not generated")
        box.frame.pack(anchor="w")
        return box

    def invalidate(self):
        """Inputs changed: the last result no longer matches, so it can't be saved."""
        if self.result is None:
            return
        self.result = None
        self.save_btn.state(["disabled"])
        self.rgb_preview.clear()
        self.alpha_preview.clear()
        self.size_label.config(text="Inputs changed: generate again")

    def generate(self):
        try:
            resolution = parse_resolution(self.resolution.get())
            fills = {ch: slot.fill_value() for ch, slot in self.slots.items()}
            sources = {ch: slot.image for ch, slot in self.slots.items()}
            inverts = {ch: slot.invert.get() for ch, slot in self.slots.items()}
            result, warning = pack_channels(sources, inverts, fills, resolution)
        except ValueError as e:
            self.app.status(str(e), "error")
            return
        self.result = result
        self.rgb_preview.show(result.convert("RGB"))
        self.alpha_preview.show(result.getchannel("A"))
        self.save_btn.state(["!disabled"])
        w, h = result.size
        self.size_label.config(text=f"{w} × {h} px")
        if warning:
            self.app.status(f"{self.title} generated ({w}×{h}). {warning}", "warning")
        else:
            self.app.status(f"{self.title} generated ({w}×{h}). Click Save to export it.", "success")

    def save(self):
        if self.result is None:
            return
        first = next((s.path for s in self.slots.values() if s.path), None)
        name = f"{base_name(first)}_{self.output_stem}.png" if first else f"{self.output_stem}.png"
        path = self.app.ask_save_path(name, os.path.dirname(first) if first else None)
        if path and self.app.save(self.result, path):
            self.app.status(f"Saved {os.path.normpath(path)}", "success")


class UnpackSection:
    """A tab that splits an RGBA texture into four grayscale files."""

    def __init__(self, app, tab):
        self.app = app
        self.path = None
        self.channels = {ch: None for ch, _, _ in UNPACK_CHANNELS}

        src_card, _, src = make_card(tab, "Source")
        src_card.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=12)
        self.preview = PreviewBox(src, SOURCE_PREVIEW_SIZE, app.drop_hint + "\nan RGBA texture",
                                  on_click=self.browse)
        self.preview.frame.pack(anchor="w")
        app.enable_drop(self.preview, self.load)
        add_tip(f"{TIP_UNPACK_LOAD}\n\n{app.drop_tip}", self.preview.label)
        self.info = tk.Label(src, text="", bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                             font=(FONT, 9), justify="left", anchor="w", wraplength=SOURCE_PREVIEW_SIZE)
        self.info.pack(anchor="w", pady=(6, 10))
        buttons = tk.Frame(src, bg=COLORS["bg_card"])
        buttons.pack(anchor="w")
        load_btn = ttk.Button(buttons, text="Load Image…", style="Accent.TButton", command=self.browse)
        load_btn.pack(side="left")
        self.clear_btn = ttk.Button(buttons, text="Clear", style="Danger.TButton", command=self.clear)
        self.clear_btn.pack(side="left", padx=(8, 0))
        add_tip(TIP_UNPACK_LOAD, load_btn)
        add_tip(TIP_UNPACK_CLEAR, self.clear_btn)
        res_row, self.resolution = resolution_picker(src, TIP_UNPACK_RES)
        res_row.pack(anchor="w", pady=(14, 0))
        tk.Label(src, text="Applied when saving.", bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                 font=(FONT, 9)).pack(anchor="w")

        ch_card, ch_header, rows = make_card(tab, "Channels")
        ch_card.grid(row=0, column=1, sticky="nsew", padx=(8, 15), pady=12)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)
        self.save_all_btn = ttk.Button(ch_header, text="Save All…", style="Success.TButton",
                                       command=self.save_all)
        self.save_all_btn.pack(side="right")
        add_tip(TIP_SAVE_ALL, self.save_all_btn)

        self.previews, self.save_buttons = {}, {}
        for i, (ch, name, hint) in enumerate(UNPACK_CHANNELS):
            channel_label(rows, i, ch, name, hint)
            box = PreviewBox(rows, PREVIEW_SIZE, "—")
            box.frame.grid(row=i, column=3, padx=12, pady=4)
            btn = ttk.Button(rows, text="Save…", style="Secondary.TButton",
                             command=lambda c=ch: self.save_channel(c))
            btn.grid(row=i, column=4, sticky="w")
            add_tip(TIP_SAVE_CHANNEL, btn)
            self.previews[ch], self.save_buttons[ch] = box, btn
        self._update_state()

    def browse(self):
        path = filedialog.askopenfilename(parent=self.app.root, title="Select texture to unpack",
                                          filetypes=OPEN_TYPES, initialdir=self.app.last_dir)
        if path:
            self.load([path])

    def load(self, paths):
        img = self.app.open_image(paths[0])
        if img is None:
            return
        rgba = to_rgba(img)
        self.path = paths[0]
        self.channels = dict(zip("RGBA", rgba.split()))
        self.preview.show(rgba.convert("RGB"))
        for ch, band in self.channels.items():
            self.previews[ch].show(band)
        w, h = rgba.size
        alpha_note = "" if has_alpha(img) else "\nNo alpha channel: A is white."
        self.info.config(text=f"{os.path.basename(self.path)}\n{w} × {h} px · {img.mode}{alpha_note}")
        self._update_state()
        self.app.status(f"Unpacked {os.path.basename(self.path)}.")

    def clear(self):
        self.path = None
        self.channels = {ch: None for ch in self.channels}
        self.preview.clear()
        for box in self.previews.values():
            box.clear()
        self.info.config(text="")
        self._update_state()

    def _resolution(self):
        try:
            return parse_resolution(self.resolution.get())
        except ValueError as e:
            self.app.status(str(e), "error")
            raise

    def save_channel(self, ch):
        try:
            resolution = self._resolution()
        except ValueError:
            return
        path = self.app.ask_save_path(f"{base_name(self.path)}_{ch}.png", os.path.dirname(self.path))
        if path and self.app.save(resize_to(self.channels[ch], resolution), path):
            self.app.status(f"Saved {os.path.normpath(path)}", "success")

    def save_all(self):
        try:
            resolution = self._resolution()
        except ValueError:
            return
        folder = filedialog.askdirectory(parent=self.app.root, title="Save channels to folder",
                                         initialdir=os.path.dirname(self.path))
        if not folder:
            return
        stem = os.path.splitext(os.path.basename(self.path))[0]
        targets = {ch: os.path.join(folder, f"{stem}_{ch}.png") for ch in self.channels}
        existing = [os.path.basename(p) for p in targets.values() if os.path.exists(p)]
        if existing and not messagebox.askyesno(
                "Overwrite files?", "These files already exist:\n\n" + "\n".join(existing) +
                "\n\nOverwrite them?", parent=self.app.root):
            return
        for ch, path in targets.items():
            if not self.app.save(resize_to(self.channels[ch], resolution), path):
                return
        self.app.status(f"Saved 4 channels to {os.path.normpath(folder)}", "success")

    def _update_state(self):
        loaded = self.path is not None
        for btn in (self.clear_btn, self.save_all_btn, *self.save_buttons.values()):
            btn.state(["!disabled"] if loaded else ["disabled"])


# ==================== APP ====================

class App:
    def __init__(self):
        self.root, self.dnd = self._create_root()
        self.drop_hint = "Drop or click" if self.dnd else "Click to browse"
        self.drop_tip = "Drop a texture here or click to browse." if self.dnd else "Click to browse."
        self.last_dir = None

        root = self.root
        root.title("Mask Map Generator - Unity HDRP")
        root.configure(bg=COLORS["bg_dark"])
        root.geometry("940x700")
        root.minsize(880, 640)
        root.report_callback_exception = self._on_error
        self._setup_styles()

        self.header = header = tk.Frame(root, bg=COLORS["bg_dark"])
        header.pack(fill="x", padx=18, pady=(14, 6))
        tk.Label(header, text="Mask Map Generator", bg=COLORS["bg_dark"], fg=COLORS["text_primary"],
                 font=(FONT, 18, "bold")).pack(side="left")
        tk.Label(header, text="Unity HDRP Lit", bg=COLORS["bg_dark"], fg=COLORS["accent_hover"],
                 font=(FONT, 12)).pack(side="left", padx=(10, 0), pady=(5, 0))
        if not self.dnd:
            tk.Label(header, text="Drag & drop unavailable: click a preview to browse",
                     bg=COLORS["bg_dark"], fg=COLORS["accent_warning"], font=(FONT, 9)).pack(side="right")

        status_bar = tk.Frame(root, bg=COLORS["bg_card"])
        status_bar.pack(side="bottom", fill="x")
        tk.Label(status_bar, text=f"v{__version__}", bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                 font=(FONT, 9)).pack(side="right", padx=(0, 18))
        self.status_label = tk.Label(status_bar, text="Ready", bg=COLORS["bg_card"], anchor="w",
                                     fg=COLORS["text_secondary"], font=(FONT, 10))
        self.status_label.pack(fill="x", padx=18, pady=6)

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=3, pady=(4, 0))
        mask_tab, detail_tab, unpack_tab = (tk.Frame(notebook, bg=COLORS["bg_dark"]) for _ in range(3))
        notebook.add(mask_tab, text="Mask Map")
        notebook.add(detail_tab, text="Detail Map")
        notebook.add(unpack_tab, text="Unpack")

        PackSection(self, mask_tab, "Mask Map", "MaskMap", MASK_CHANNELS, MASK_TIPS, "Smoothness",
                    "Empty channels use their 'If empty' value (0–1).\n"
                    "In Unity, import with sRGB (Color Texture) OFF.")
        self.detail = PackSection(self, detail_tab, "Detail Map", "DetailMap", DETAIL_CHANNELS,
                                  DETAIL_TIPS, "Normal X",
                                  "Empty channels default to 0.5 = neutral (no effect).\n"
                                  "DirectX normal map? Tick Invert on Normal Y.")
        normal_btn = ttk.Button(self.detail.inputs_header, text="Load Normal Map…",
                                style="Secondary.TButton", command=self.browse_normal_map)
        normal_btn.pack(side="right")
        self.enable_drop(normal_btn, self.load_normal_map)
        add_tip(TIP_NORMAL + ("\nYou can also drop the file on this button." if self.dnd else ""), normal_btn)
        UnpackSection(self, unpack_tab)
        self._check_for_update()

    # ---------- setup ----------

    @staticmethod
    def _create_root():
        root = tk.Tk()
        if TkinterDnD is None:
            return root, False
        try:
            TkinterDnD._require(root)  # loads the native tkdnd library
            return root, True
        except Exception:  # e.g. no tkdnd binary for this platform
            return root, False

    def _setup_styles(self):
        c = COLORS
        style = ttk.Style()
        style.theme_use("clam")

        def flat_button(name, bg, hover, font_size=9, bold=False, padding=(10, 5)):
            style.configure(name, background=bg, foreground="white", bordercolor=bg, lightcolor=bg,
                            darkcolor=bg, focuscolor=bg, padding=padding,
                            font=(FONT, font_size, "bold" if bold else "normal"))
            style.map(name,
                      background=[("disabled", c["bg_card"]), ("pressed", bg), ("active", hover)],
                      bordercolor=[("disabled", c["border"]), ("active", hover)],
                      lightcolor=[("disabled", c["bg_card"]), ("active", hover)],
                      darkcolor=[("disabled", c["bg_card"]), ("active", hover)],
                      foreground=[("disabled", c["text_muted"])])

        flat_button("Accent.TButton", c["accent"], c["accent_hover"], 10, True, (15, 8))
        flat_button("Success.TButton", "#00a043", c["accent_success"], 10, True, (15, 8))
        flat_button("Secondary.TButton", c["bg_input"], c["border"])
        flat_button("Danger.TButton", c["accent_danger"], "#ff6659", 10, True, (15, 8))
        flat_button("Update.TButton", "#00a043", c["accent_success"], 9, True, (10, 4))

        style.configure("Card.TCheckbutton", background=c["bg_card"], foreground=c["text_secondary"],
                        font=(FONT, 9), indicatorbackground=c["bg_input"], indicatorforeground="white",
                        focuscolor=c["bg_card"])
        style.map("Card.TCheckbutton",
                  background=[("active", c["bg_card"])],
                  foreground=[("disabled", c["text_muted"]), ("active", "white")],
                  indicatorbackground=[("disabled", c["bg_card"]), ("selected", c["accent"])])

        for name in ("TSpinbox", "TCombobox"):
            style.configure(name, fieldbackground=c["bg_input"], background=c["bg_input"],
                            foreground="white", arrowcolor="white", bordercolor=c["border"],
                            lightcolor=c["bg_input"], darkcolor=c["bg_input"], insertcolor="white",
                            selectbackground=c["accent"], selectforeground="white")
            style.map(name,
                      fieldbackground=[("disabled", c["bg_card"]), ("readonly", c["bg_input"])],
                      foreground=[("disabled", c["text_muted"])],
                      arrowcolor=[("disabled", c["text_muted"])])
        self.root.option_add("*TCombobox*Listbox.background", c["bg_input"])
        self.root.option_add("*TCombobox*Listbox.foreground", "white")
        self.root.option_add("*TCombobox*Listbox.selectBackground", c["accent"])

        style.configure("TNotebook", background=c["bg_dark"], borderwidth=0, tabmargins=(15, 4, 15, 0),
                        bordercolor=c["bg_dark"], lightcolor=c["bg_dark"], darkcolor=c["bg_dark"])
        style.configure("TNotebook.Tab", background=c["bg_card"], foreground=c["text_secondary"],
                        padding=(20, 8), font=(FONT, 10, "bold"), bordercolor=c["border"],
                        lightcolor=c["bg_card"], focuscolor=c["bg_card"])
        style.map("TNotebook.Tab",
                  background=[("selected", c["accent"]), ("active", c["bg_input"])],
                  foreground=[("selected", "white"), ("active", "white")],
                  lightcolor=[("selected", c["accent"])],
                  focuscolor=[("selected", c["accent"])],
                  padding=[("selected", (20, 8))],  # clam shrinks the selected tab by default
                  expand=[("selected", (0, 0, 0, 0))])

    def enable_drop(self, target, on_files):
        """Make a widget (or a PreviewBox) accept dropped files."""
        if not self.dnd:
            return
        box = target if isinstance(target, PreviewBox) else None
        widgets = (box.frame, box.label) if box else (target,)

        def drop(event):
            if box:
                box.highlight(False)
            files = self.root.tk.splitlist(event.data)  # handles {paths with spaces}
            if files:
                on_files(list(files))
            return event.action

        def hover(on):
            def handler(event):
                if box:
                    box.highlight(on)
                return event.action
            return handler

        for widget in widgets:
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", drop)
            widget.dnd_bind("<<DropEnter>>", hover(True))
            widget.dnd_bind("<<DropLeave>>", hover(False))

    # ---------- update check ----------

    def _check_for_update(self):
        """Ask GitHub for the latest release in the background (Tk is polled from the main
        thread only); if it is newer than this version, show an Update button in the header."""
        result = []
        worker = threading.Thread(target=lambda: result.append(latest_release_tag()), daemon=True)
        worker.start()

        def poll():
            if worker.is_alive():
                self.root.after(250, poll)
            elif result and is_newer(result[0]):
                self._show_update(result[0])

        self.root.after(250, poll)

    def _show_update(self, tag):
        button = ttk.Button(self.header, text=f"⬆ Update available: {tag}", style="Update.TButton",
                            command=lambda: webbrowser.open(RELEASES_URL))
        button.pack(side="right")
        add_tip(f"Version {tag} is available (you have v{__version__}).\n"
                "Click to open the download page, then replace this app with the new file.", button)

    # ---------- shared actions ----------

    def open_image(self, path):
        """Fully load an image (closing the file). Shows an error and returns None on failure."""
        try:
            with Image.open(path) as img:
                img.load()
                loaded = img.copy() if img.mode != "P" else img.convert("RGBA" if has_alpha(img) else "RGB")
        except UnidentifiedImageError:
            self.status(f"Could not open {os.path.basename(path)}: not a supported image file.", "error")
            return None
        except (OSError, ValueError, Image.DecompressionBombError) as e:
            self.status(f"Could not open {os.path.basename(path)}: {e}", "error")
            return None
        self.last_dir = os.path.dirname(path)
        return loaded

    def ask_save_path(self, initialfile, initialdir=None):
        file_type = tk.StringVar(value=SAVE_TYPES[0][0])
        path = filedialog.asksaveasfilename(parent=self.root, title="Save texture", filetypes=SAVE_TYPES,
                                            initialfile=initialfile, initialdir=initialdir or self.last_dir,
                                            typevariable=file_type)
        if not path:
            return None
        if os.path.splitext(path)[1].lower() not in SAVE_FORMATS:
            pattern = dict(SAVE_TYPES).get(file_type.get(), "*.png")
            path += pattern[1:]
        return path

    def save(self, img, path):
        try:
            save_image(img, path)
        except (OSError, ValueError) as e:
            self.status(f"Could not save {os.path.basename(path)}: {e}", "error")
            messagebox.showerror("Save failed", str(e), parent=self.root)
            return False
        self.last_dir = os.path.dirname(path)
        return True

    def browse_normal_map(self):
        path = filedialog.askopenfilename(parent=self.root, title="Select detail normal map",
                                          filetypes=OPEN_TYPES, initialdir=self.last_dir)
        if path:
            self.load_normal_map([path])

    def load_normal_map(self, paths):
        img = self.open_image(paths[0])
        if img is None:
            return
        red, green, _ = to_rgb(img).split()
        self.detail.slots["A"].set_image(red, paths[0], " (R)")
        self.detail.slots["G"].set_image(green, paths[0], " (G)")
        self.status("Normal map loaded: red → Normal X (A), green → Normal Y (G).")

    def status(self, text, kind="info"):
        color = {"info": "text_secondary", "success": "accent_success",
                 "warning": "accent_warning", "error": "accent_danger"}[kind]
        prefix = {"success": "✓ ", "warning": "⚠ ", "error": "✕ "}.get(kind, "")
        self.status_label.config(text=prefix + text, fg=COLORS[color])

    def _on_error(self, exc_type, exc, tb):
        traceback.print_exception(exc_type, exc, tb)
        self.status(f"Unexpected error: {exc}", "error")
        messagebox.showerror("Unexpected error", f"{exc_type.__name__}: {exc}", parent=self.root)

    def run(self):
        self.root.mainloop()


def main():
    App().run()


if __name__ == "__main__":
    main()
