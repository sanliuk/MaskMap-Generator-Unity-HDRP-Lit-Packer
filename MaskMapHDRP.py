import tkinter as tk
from tkinter import filedialog, BooleanVar, ttk, Canvas
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk, ImageOps

def load_image(channel, filepath=None):
    if not filepath:
        filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.tga")])
    if filepath:
        img = Image.open(filepath).convert("L")
        images[channel] = img
        update_preview(channel)

def update_preview(channel):
    if images[channel]:
        img = images[channel]
        if invert_vars[channel].get():
            img = ImageOps.invert(img)
        img.thumbnail((150, 150))
        img_tk = ImageTk.PhotoImage(img)
        previews[channel].config(image=img_tk)
        previews[channel].image = img_tk

def clear_image(channel):
    images[channel] = None
    previews[channel].config(image='', text='Insert Image')

def evaluate_resolution(event=None):
    try:
        resolution_var.set(str(eval(resolution_var.get())))
    except:
        pass

def generate_mask_map():
    if None in [images["R"], images["G"], images["A"]]:
        status_label.config(text="⚠️ Select at least R, G, and A images!", fg=COLORS["accent_danger"])
        return
    
    size = (int(resolution_var.get()), int(resolution_var.get()))
    for key in images:
        if images[key]:
            img = images[key].resize(size)
            if invert_vars[key].get():
                img = ImageOps.invert(img)
            images[key] = img
        else:
            images[key] = Image.new("L", size, 255)  # Default white if missing
    
    global mask_map
    mask_map = Image.merge("RGBA", (images["R"], images["G"], images["B"], images["A"]))
    mask_map_preview = mask_map.copy()
    mask_map_preview.thumbnail((200, 200))
    img_tk = ImageTk.PhotoImage(mask_map_preview)
    mask_preview_label.config(image=img_tk)
    mask_preview_label.image = img_tk
    
    save_btn.pack(side="left", padx=5)
    status_label.config(text="✅ Mask Map Generated!", fg=COLORS["accent_success"])

def save_mask_map():
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png")])
    if save_path:
        mask_map.save(save_path)
        status_label.config(text=f"✅ Saved: {save_path}", fg=COLORS["accent_success"])

def on_mouse_scroll(event):
    canvas.yview_scroll(-1 * (event.delta // 120), "units")

def on_drop(event, channel):
    filepath = event.data
    load_image(channel, filepath)

def on_drop_detail(event, channel):
    filepath = event.data
    load_detail_image(channel, filepath)

def load_detail_image(channel, filepath=None):
    if not filepath:
        filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.tga")])
    if filepath:
        # Load Detail Albedo (R) as RGB to allow desaturation, others as grayscale
        if channel == "R":
            img = Image.open(filepath).convert("RGB")
        else:
            img = Image.open(filepath).convert("L")
        detail_images[channel] = img
        update_detail_preview(channel)

def update_detail_preview(channel):
    if detail_images[channel]:
        img = detail_images[channel].copy()
        # Convert to grayscale for preview if RGB (for invert to work)
        if img.mode == "RGB":
            preview_img = img.convert("L")
        else:
            preview_img = img
        if detail_invert_vars[channel].get():
            preview_img = ImageOps.invert(preview_img)
        preview_img.thumbnail((150, 150))
        img_tk = ImageTk.PhotoImage(preview_img)
        detail_previews[channel].config(image=img_tk)
        detail_previews[channel].image = img_tk

def clear_detail_image(channel):
    detail_images[channel] = None
    detail_previews[channel].config(image='', text='Insert Image')

def generate_detail_map():
    if None in [detail_images["R"], detail_images["G"], detail_images["B"], detail_images["A"]]:
        status_label.config(text="⚠️ Select R, G, B, and A images for detail map!", fg=COLORS["accent_danger"])
        return
    
    size = (int(detail_resolution_var.get()), int(detail_resolution_var.get()))
    for key in detail_images:
        if detail_images[key]:
            img = detail_images[key].resize(size)
            # Convert to grayscale if RGB (e.g., Detail Albedo)
            if img.mode == "RGB":
                img = img.convert("L")
            if detail_invert_vars[key].get():
                img = ImageOps.invert(img)
            detail_images[key] = img
        else:
            detail_images[key] = Image.new("L", size, 255)  # Default white if missing
    
    global detail_map
    detail_map = Image.merge("RGBA", (detail_images["R"], detail_images["G"], detail_images["B"], detail_images["A"]))
    detail_map_preview = detail_map.copy()
    detail_map_preview.thumbnail((200, 200))
    img_tk = ImageTk.PhotoImage(detail_map_preview)
    detail_map_preview_label.config(image=img_tk)
    detail_map_preview_label.image = img_tk
    
    # Show the button to save the detail map
    save_detail_btn.pack(side="left", padx=5)

    status_label.config(text="✅ Detail Map Generated!", fg=COLORS["accent_success"])

def save_detail_map():
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png")])
    if save_path:
        detail_map.save(save_path)
        status_label.config(text=f"✅ Saved: {save_path}", fg=COLORS["accent_success"])

def load_normal_map():
    filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.tga")])
    if filepath:
        img = Image.open(filepath).convert("RGB")
        detail_images["A"] = img.split()[0]  # Normal X
        detail_images["G"] = img.split()[1]  # Normal Y
        update_detail_preview("A")
        update_detail_preview("G")

def desaturate_image(channel):
    if detail_images[channel]:
        img = detail_images[channel]
        # Convert RGB to grayscale (desaturate)
        if img.mode == "RGB":
            img = img.convert("L")
        detail_images[channel] = img
        update_detail_preview(channel)

def clear_unpacked_images():
    for channel in unpacked_images:
        unpacked_images[channel] = None
        unpack_previews[channel].config(image='', text='No Image')
        unpack_save_buttons[channel].pack_forget()

def unpack_image():
    filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.png")])
    if filepath:
        img = Image.open(filepath).convert("RGBA")
        r, g, b, a = img.split()
        size = (int(unpack_resolution_var.get()), int(unpack_resolution_var.get()))
        unpacked_images["R"] = r.resize(size)
        unpacked_images["G"] = g.resize(size)
        unpacked_images["B"] = b.resize(size)
        unpacked_images["A"] = a.resize(size)
        update_unpack_previews()

def update_unpack_previews():
    for channel in unpacked_images:
        img = unpacked_images[channel].copy()
        img.thumbnail((150, 150))
        img_tk = ImageTk.PhotoImage(img)
        unpack_previews[channel].config(image=img_tk)
        unpack_previews[channel].image = img_tk
        unpack_save_buttons[channel].pack(side="left", padx=5)

def save_unpacked_image(channel):
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png")])
    if save_path:
        unpacked_images[channel].save(save_path)
        status_label.config(text=f"✅ Saved: {save_path}", fg=COLORS["accent_success"])

# ==================== MODERN UI CONFIGURATION ====================

# Color Palette
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
    "border": "#2d4a6f",
    "preview_bg": "#0a0a1a",
    "channel_r": "#ff5252",
    "channel_g": "#69f0ae",
    "channel_b": "#448aff",
    "channel_a": "#b388ff",
}

# Configure UI
root = TkinterDnD.Tk()
root.title("Mask Map Generator - Unity HDRP")
root.configure(bg=COLORS["bg_dark"])
root.geometry("700x800")
root.resizable(True, True)
root.minsize(650, 600)

# Try to set window icon (optional)
try:
    root.iconbitmap(default='')
except:
    pass

canvas = Canvas(root, bg=COLORS["bg_dark"], highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg=COLORS["bg_dark"])
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
canvas.bind_all("<MouseWheel>", on_mouse_scroll)

images = {"R": None, "G": None, "B": None, "A": None}
invert_vars = {channel: BooleanVar() for channel in images}
previews = {}

detail_images = {"R": None, "G": None, "B": None, "A": None}
detail_invert_vars = {channel: BooleanVar() for channel in detail_images}
detail_previews = {}

unpacked_images = {"R": None, "G": None, "B": None, "A": None}
unpack_previews = {}
unpack_save_buttons = {}

# Configure ttk styles
style = ttk.Style()
style.theme_use('clam')

# Frame styles
style.configure("Card.TFrame", background=COLORS["bg_card"])
style.configure("Dark.TFrame", background=COLORS["bg_dark"])

# Label styles
style.configure("TLabel", background=COLORS["bg_dark"], foreground=COLORS["text_secondary"], font=("Segoe UI", 10))
style.configure("Card.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_secondary"], font=("Segoe UI", 10))
style.configure("Title.TLabel", background=COLORS["bg_dark"], foreground=COLORS["text_primary"], font=("Segoe UI", 14, "bold"))
style.configure("CardTitle.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_primary"], font=("Segoe UI", 12, "bold"))
style.configure("Status.TLabel", background=COLORS["bg_dark"], foreground=COLORS["accent_success"], font=("Segoe UI", 10))

# Button styles
style.configure("Accent.TButton", background=COLORS["accent"], foreground="white", font=("Segoe UI", 10, "bold"), padding=(15, 8))
style.map("Accent.TButton", background=[("active", COLORS["accent_hover"]), ("pressed", COLORS["accent"])])

style.configure("Secondary.TButton", background=COLORS["bg_input"], foreground="white", font=("Segoe UI", 9), padding=(10, 5))
style.map("Secondary.TButton", background=[("active", COLORS["border"])])

style.configure("Danger.TButton", background=COLORS["accent_danger"], foreground="white", font=("Segoe UI", 9), padding=(10, 5))
style.map("Danger.TButton", background=[("active", "#ff6659")])

style.configure("Success.TButton", background=COLORS["accent_success"], foreground="white", font=("Segoe UI", 10, "bold"), padding=(15, 8))
style.map("Success.TButton", background=[("active", "#00e676")])

# Checkbutton styles
style.configure("Card.TCheckbutton", background=COLORS["bg_card"], foreground=COLORS["text_secondary"], font=("Segoe UI", 9))

# Entry styles
style.configure("TEntry", fieldbackground=COLORS["bg_input"], foreground="white", padding=5)

# Helper function to create section cards
def create_section_card(parent, title, row):
    """Create a styled card section with title"""
    card = tk.Frame(parent, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1)
    card.grid(row=row, column=0, columnspan=6, sticky="ew", padx=15, pady=10)

    title_label = tk.Label(card, text=title, bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                           font=("Segoe UI", 12, "bold"), anchor="w")
    title_label.pack(fill="x", padx=15, pady=(12, 8))

    separator = tk.Frame(card, bg=COLORS["border"], height=1)
    separator.pack(fill="x", padx=15)

    content = tk.Frame(card, bg=COLORS["bg_card"])
    content.pack(fill="both", expand=True, padx=15, pady=12)

    return content

# Helper function to create channel indicator
def create_channel_indicator(parent, channel):
    """Create a colored channel indicator"""
    color = COLORS[f"channel_{channel.lower()}"]
    indicator = tk.Frame(parent, bg=color, width=4, height=40)
    return indicator

# Helper function to create styled preview label
def create_preview_label(parent, text="Drop Image"):
    """Create a styled image preview label"""
    label = tk.Label(parent, text=text, bg=COLORS["preview_bg"], fg=COLORS["text_secondary"],
                     width=18, height=8, relief="flat", font=("Segoe UI", 9),
                     highlightbackground=COLORS["border"], highlightthickness=1)
    return label

# ==================== APP HEADER ====================
header_frame = tk.Frame(scrollable_frame, bg=COLORS["bg_dark"])
header_frame.grid(row=0, column=0, columnspan=6, sticky="ew", padx=15, pady=(15, 5))

app_title = tk.Label(header_frame, text="Mask Map Generator", bg=COLORS["bg_dark"],
                     fg=COLORS["text_primary"], font=("Segoe UI", 18, "bold"))
app_title.pack(side="left")

app_subtitle = tk.Label(header_frame, text="Unity HDRP", bg=COLORS["bg_dark"],
                        fg=COLORS["accent"], font=("Segoe UI", 12))
app_subtitle.pack(side="left", padx=(10, 0), pady=(5, 0))

# ==================== DETAIL MAP SECTION ====================
detail_card = create_section_card(scrollable_frame, "Detail Map", row=1)

# Load Normal Map button at the top of detail section
normal_map_btn = ttk.Button(detail_card, text="Load Normal Map", style="Accent.TButton", command=load_normal_map)
normal_map_btn.grid(row=0, column=0, columnspan=5, pady=(0, 15))

# Detail map channels
detail_channels = {"R": "Detail Albedo", "G": "Normal Y", "B": "Smoothness", "A": "Normal X"}
for i, (channel, name) in enumerate(detail_channels.items()):
    row_frame = tk.Frame(detail_card, bg=COLORS["bg_card"])
    row_frame.grid(row=i+1, column=0, columnspan=5, sticky="ew", pady=4)

    # Channel indicator
    indicator = create_channel_indicator(row_frame, channel)
    indicator.pack(side="left", fill="y", padx=(0, 10))

    # Channel name with colored letter
    name_frame = tk.Frame(row_frame, bg=COLORS["bg_card"])
    name_frame.pack(side="left", fill="y")

    channel_letter = tk.Label(name_frame, text=channel, bg=COLORS["bg_card"],
                              fg=COLORS[f"channel_{channel.lower()}"], font=("Segoe UI", 11, "bold"), width=2)
    channel_letter.pack(side="left")

    name_label = tk.Label(name_frame, text=name, bg=COLORS["bg_card"],
                          fg=COLORS["text_secondary"], font=("Segoe UI", 10), width=14, anchor="w")
    name_label.pack(side="left", padx=(5, 0))

    # Preview label
    preview_label = create_preview_label(row_frame)
    preview_label.pack(side="left", padx=10)
    preview_label.drop_target_register(DND_FILES)
    preview_label.dnd_bind('<<Drop>>', lambda e, c=channel: on_drop_detail(e, c))
    detail_previews[channel] = preview_label

    # Buttons frame
    btn_frame = tk.Frame(row_frame, bg=COLORS["bg_card"])
    btn_frame.pack(side="left", padx=5)

    chk = ttk.Checkbutton(btn_frame, text="Invert", variable=detail_invert_vars[channel],
                          style="Card.TCheckbutton", command=lambda c=channel: update_detail_preview(c))
    chk.pack(side="left", padx=2)

    clear_btn = ttk.Button(btn_frame, text="Clear", style="Secondary.TButton",
                           command=lambda c=channel: clear_detail_image(c))
    clear_btn.pack(side="left", padx=2)

    if channel == "R":
        desaturate_btn = ttk.Button(btn_frame, text="Desaturate", style="Secondary.TButton",
                                    command=lambda c=channel: desaturate_image(c))
        desaturate_btn.pack(side="left", padx=2)

# Detail resolution and generate section
detail_bottom = tk.Frame(detail_card, bg=COLORS["bg_card"])
detail_bottom.grid(row=6, column=0, columnspan=5, sticky="ew", pady=(15, 0))

res_label = tk.Label(detail_bottom, text="Resolution:", bg=COLORS["bg_card"],
                     fg=COLORS["text_secondary"], font=("Segoe UI", 10))
res_label.pack(side="left")

detail_resolution_var = tk.StringVar(value="1024")
detail_resolution_entry = tk.Entry(detail_bottom, textvariable=detail_resolution_var, width=8,
                                   bg=COLORS["bg_input"], fg="white", font=("Segoe UI", 10),
                                   relief="flat", insertbackground="white")
detail_resolution_entry.pack(side="left", padx=(5, 15))
detail_resolution_entry.bind("<Return>", evaluate_resolution)

generate_detail_btn = ttk.Button(detail_bottom, text="Generate Detail Map", style="Accent.TButton",
                                 command=generate_detail_map)
generate_detail_btn.pack(side="left", padx=5)

save_detail_btn = ttk.Button(detail_bottom, text="Save", style="Success.TButton", command=save_detail_map)
save_detail_btn.pack(side="left", padx=5)
save_detail_btn.pack_forget()

# Detail map preview
detail_preview_frame = tk.Frame(detail_card, bg=COLORS["bg_card"])
detail_preview_frame.grid(row=7, column=0, columnspan=5, pady=10)
detail_map_preview_label = tk.Label(detail_preview_frame, bg=COLORS["bg_card"])
detail_map_preview_label.pack()

# ==================== MASK MAP SECTION ====================
mask_card = create_section_card(scrollable_frame, "Mask Map", row=2)

# Mask map channels
mask_channels = {"R": "Metallic", "G": "Ambient Occlusion", "B": "Detail Mask", "A": "Smoothness"}
for i, (channel, name) in enumerate(mask_channels.items()):
    row_frame = tk.Frame(mask_card, bg=COLORS["bg_card"])
    row_frame.grid(row=i, column=0, columnspan=5, sticky="ew", pady=4)

    # Channel indicator
    indicator = create_channel_indicator(row_frame, channel)
    indicator.pack(side="left", fill="y", padx=(0, 10))

    # Channel name with colored letter
    name_frame = tk.Frame(row_frame, bg=COLORS["bg_card"])
    name_frame.pack(side="left", fill="y")

    channel_letter = tk.Label(name_frame, text=channel, bg=COLORS["bg_card"],
                              fg=COLORS[f"channel_{channel.lower()}"], font=("Segoe UI", 11, "bold"), width=2)
    channel_letter.pack(side="left")

    # Add (Optional) indicator for B channel
    display_name = name if channel != "B" else name + " (Opt)"
    name_label = tk.Label(name_frame, text=display_name, bg=COLORS["bg_card"],
                          fg=COLORS["text_secondary"], font=("Segoe UI", 10), width=16, anchor="w")
    name_label.pack(side="left", padx=(5, 0))

    # Preview label
    preview_label = create_preview_label(row_frame)
    preview_label.pack(side="left", padx=10)
    preview_label.drop_target_register(DND_FILES)
    preview_label.dnd_bind('<<Drop>>', lambda e, c=channel: on_drop(e, c))
    previews[channel] = preview_label

    # Buttons frame
    btn_frame = tk.Frame(row_frame, bg=COLORS["bg_card"])
    btn_frame.pack(side="left", padx=5)

    chk = ttk.Checkbutton(btn_frame, text="Invert", variable=invert_vars[channel],
                          style="Card.TCheckbutton", command=lambda c=channel: update_preview(c))
    chk.pack(side="left", padx=2)

    clear_btn = ttk.Button(btn_frame, text="Clear", style="Secondary.TButton",
                           command=lambda c=channel: clear_image(c))
    clear_btn.pack(side="left", padx=2)

# Mask resolution and generate section
mask_bottom = tk.Frame(mask_card, bg=COLORS["bg_card"])
mask_bottom.grid(row=5, column=0, columnspan=5, sticky="ew", pady=(15, 0))

res_label2 = tk.Label(mask_bottom, text="Resolution:", bg=COLORS["bg_card"],
                      fg=COLORS["text_secondary"], font=("Segoe UI", 10))
res_label2.pack(side="left")

resolution_var = tk.StringVar(value="1024")
resolution_entry = tk.Entry(mask_bottom, textvariable=resolution_var, width=8,
                            bg=COLORS["bg_input"], fg="white", font=("Segoe UI", 10),
                            relief="flat", insertbackground="white")
resolution_entry.pack(side="left", padx=(5, 15))
resolution_entry.bind("<Return>", evaluate_resolution)

generate_btn = ttk.Button(mask_bottom, text="Generate Mask Map", style="Accent.TButton",
                          command=generate_mask_map)
generate_btn.pack(side="left", padx=5)

save_btn = ttk.Button(mask_bottom, text="Save", style="Success.TButton", command=save_mask_map)
save_btn.pack(side="left", padx=5)
save_btn.pack_forget()

# Mask map preview
mask_preview_frame = tk.Frame(mask_card, bg=COLORS["bg_card"])
mask_preview_frame.grid(row=6, column=0, columnspan=5, pady=10)
mask_preview_label = tk.Label(mask_preview_frame, bg=COLORS["bg_card"])
mask_preview_label.pack()

# ==================== UNPACK SECTION ====================
unpack_card = create_section_card(scrollable_frame, "Unpack Image", row=3)

# Unpack controls
unpack_controls = tk.Frame(unpack_card, bg=COLORS["bg_card"])
unpack_controls.grid(row=0, column=0, columnspan=5, sticky="ew", pady=(0, 15))

load_unpack_btn = ttk.Button(unpack_controls, text="Load Image", style="Accent.TButton", command=unpack_image)
load_unpack_btn.pack(side="left", padx=(0, 10))

clear_unpack_btn = ttk.Button(unpack_controls, text="Clear All", style="Danger.TButton", command=clear_unpacked_images)
clear_unpack_btn.pack(side="left", padx=5)

res_label3 = tk.Label(unpack_controls, text="Resolution:", bg=COLORS["bg_card"],
                      fg=COLORS["text_secondary"], font=("Segoe UI", 10))
res_label3.pack(side="left", padx=(20, 5))

unpack_resolution_var = tk.StringVar(value="1024")
unpack_resolution_entry = tk.Entry(unpack_controls, textvariable=unpack_resolution_var, width=8,
                                   bg=COLORS["bg_input"], fg="white", font=("Segoe UI", 10),
                                   relief="flat", insertbackground="white")
unpack_resolution_entry.pack(side="left")

# Unpack previews
unpack_channels = {"R": "Red", "G": "Green", "B": "Blue", "A": "Alpha"}
for i, (channel, name) in enumerate(unpack_channels.items()):
    row_frame = tk.Frame(unpack_card, bg=COLORS["bg_card"])
    row_frame.grid(row=i+1, column=0, columnspan=5, sticky="ew", pady=4)

    # Channel indicator
    indicator = create_channel_indicator(row_frame, channel)
    indicator.pack(side="left", fill="y", padx=(0, 10))

    # Channel name
    name_frame = tk.Frame(row_frame, bg=COLORS["bg_card"])
    name_frame.pack(side="left", fill="y")

    channel_letter = tk.Label(name_frame, text=channel, bg=COLORS["bg_card"],
                              fg=COLORS[f"channel_{channel.lower()}"], font=("Segoe UI", 11, "bold"), width=2)
    channel_letter.pack(side="left")

    name_label = tk.Label(name_frame, text=name + " Channel", bg=COLORS["bg_card"],
                          fg=COLORS["text_secondary"], font=("Segoe UI", 10), width=14, anchor="w")
    name_label.pack(side="left", padx=(5, 0))

    # Preview label
    preview_label = create_preview_label(row_frame, text="No Image")
    preview_label.pack(side="left", padx=10)
    unpack_previews[channel] = preview_label

    # Save button
    save_btn = ttk.Button(row_frame, text="Save", style="Success.TButton",
                          command=lambda c=channel: save_unpacked_image(c))
    save_btn.pack(side="left", padx=5)
    save_btn.pack_forget()
    unpack_save_buttons[channel] = save_btn

# ==================== STATUS BAR ====================
status_frame = tk.Frame(scrollable_frame, bg=COLORS["bg_dark"])
status_frame.grid(row=4, column=0, columnspan=6, sticky="ew", padx=15, pady=(10, 20))

status_label = tk.Label(status_frame, text="Ready", bg=COLORS["bg_dark"],
                        fg=COLORS["text_secondary"], font=("Segoe UI", 10))
status_label.pack(side="left")

# ==================== FOOTER ====================
footer_frame = tk.Frame(scrollable_frame, bg=COLORS["bg_dark"])
footer_frame.grid(row=5, column=0, columnspan=6, sticky="ew", padx=15, pady=(0, 15))

footer_text = tk.Label(footer_frame, text="Unity HDRP Mask Map Generator", bg=COLORS["bg_dark"],
                       fg=COLORS["border"], font=("Segoe UI", 9))
footer_text.pack()

root.mainloop()
