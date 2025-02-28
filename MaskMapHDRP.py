import tkinter as tk
from tkinter import filedialog, BooleanVar, ttk, Canvas
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk, ImageOps, ImageEnhance

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
        status_label.config(text="⚠️ Select at least R, G, and A images!", foreground="red")
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
    
    save_btn.grid()
    status_label.config(text="✅ Mask Map Generated!", foreground="green")

def save_mask_map():
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png")])
    if save_path:
        mask_map.save(save_path)
        status_label.config(text=f"✅ Saved: {save_path}", foreground="green")

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
        img = Image.open(filepath).convert("L")
        detail_images[channel] = img
        update_detail_preview(channel)

def update_detail_preview(channel):
    if detail_images[channel]:
        img = detail_images[channel]
        if detail_invert_vars[channel].get():
            img = ImageOps.invert(img)
        img.thumbnail((150, 150))
        img_tk = ImageTk.PhotoImage(img)
        detail_previews[channel].config(image=img_tk)
        detail_previews[channel].image = img_tk

def clear_detail_image(channel):
    detail_images[channel] = None
    detail_previews[channel].config(image='', text='Insert Image')

def generate_detail_map():
    if None in [detail_images["R"], detail_images["G"], detail_images["B"], detail_images["A"]]:
        status_label.config(text="⚠️ Select R, G, B, and A images for detail map!", foreground="red")
        return
    
    size = (int(resolution_var.get()), int(resolution_var.get()))
    for key in detail_images:
        if detail_images[key]:
            img = detail_images[key].resize(size)
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
    
    # Show the button to insert the detail map into the mask map
    insert_detail_btn.grid()
    
    status_label.config(text="✅ Detail Map Generated!", foreground="green")

def insert_detail_map():
    global detail_map
    images["B"] = detail_map
    update_preview("B")
    insert_detail_btn.grid_remove()

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
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0)  # Desaturate the image
        detail_images[channel] = img
        update_detail_preview(channel)

# Configure UI
root = TkinterDnD.Tk()
root.title("Mask Map Generator")
root.configure(bg="#232323")  # Dark gray background
root.geometry("600x700")
root.resizable(True, True)

canvas = Canvas(root, bg="#232323")  # Dark gray background
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas, style="Dark.TFrame", padding=15)
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

style = ttk.Style()
style.configure("Dark.TFrame", background="#232323")  # Dark gray background
style.configure("TLabel", background="#232323", foreground="#C0C0C0")  # Dark gray background
style.configure("TButton", background="#007BFF", foreground="black", font=("Arial", 10, "bold"))
style.map("TButton", background=[("active", "#0056b3")])
style.configure("TCheckbutton", background="#232323", foreground="#C0C0C0")  # Dark gray background

# Load detail normal map button
normal_map_btn = ttk.Button(scrollable_frame, text="Load Detail Normal Map", style="TButton", command=load_normal_map)
normal_map_btn.grid(row=0, column=0, columnspan=3, pady=10)

# Detail map section title
ttk.Label(scrollable_frame, text="Detail Map", style="TLabel", font=("Arial", 12, "bold")).grid(row=1, column=0, columnspan=8, pady=(0, 10))

for i, (channel, name) in enumerate({"R": "Detail Albedo", "G": "Detail Normal Y", "B": "Detail Smoothness", "A": "Detail Normal X"}.items()):
    ttk.Label(scrollable_frame, text=name, style="TLabel").grid(row=i+2, column=0, padx=5, pady=5, sticky="W")
    
    preview_label = tk.Label(scrollable_frame, text="Insert Image", bg="#444444", width=20, height=10)
    preview_label.grid(row=i+2, column=1, padx=5, pady=5)
    preview_label.drop_target_register(DND_FILES)
    preview_label.dnd_bind('<<Drop>>', lambda e, c=channel: on_drop_detail(e, c))
    detail_previews[channel] = preview_label
    
    chk = ttk.Checkbutton(scrollable_frame, text="Invert", variable=detail_invert_vars[channel], style="TCheckbutton", command=lambda c=channel: update_detail_preview(c))
    chk.grid(row=i+2, column=2, padx=5, pady=5)
    
    clear_btn = ttk.Button(scrollable_frame, text="Clear", style="TButton", command=lambda c=channel: clear_detail_image(c))
    clear_btn.grid(row=i+2, column=3, padx=5, pady=5)
    
    if channel == "R":  # Add desaturate button only for Detail Albedo
        desaturate_btn = ttk.Button(scrollable_frame, text="Desaturate", style="TButton", command=lambda c=channel: desaturate_image(c))
        desaturate_btn.grid(row=i+2, column=4, padx=5, pady=5)

# Generate detail map button
generate_detail_btn = ttk.Button(scrollable_frame, text="Generate Detail Map", style="TButton", command=generate_detail_map)
generate_detail_btn.grid(row=6, column=0, columnspan=3, pady=10)

# Detail map preview label
detail_map_preview_label = ttk.Label(scrollable_frame, style="TLabel")
detail_map_preview_label.grid(row=7, column=1, padx=5, pady=5)

# Insert detail map button
insert_detail_btn = ttk.Button(scrollable_frame, text="Insert Detail Map", style="TButton", command=insert_detail_map)
insert_detail_btn.grid(row=8, column=0, columnspan=3, pady=10)
insert_detail_btn.grid_remove()

# Mask map section title
ttk.Label(scrollable_frame, text="Mask Map", style="TLabel", font=("Arial", 12, "bold")).grid(row=9, column=0, columnspan=4, pady=(0, 10))

for i, (channel, name) in enumerate({"R": "Metallic", "G": "AO", "B": "Detail Map (Optional)", "A": "Smoothness"}.items()):
    ttk.Label(scrollable_frame, text=name, style="TLabel").grid(row=i+10, column=0, padx=5, pady=5, sticky="W")
    
    preview_label = tk.Label(scrollable_frame, text="Insert Image", bg="#444444", width=20, height=10)
    preview_label.grid(row=i+10, column=1, padx=5, pady=5)
    preview_label.drop_target_register(DND_FILES)
    preview_label.dnd_bind('<<Drop>>', lambda e, c=channel: on_drop(e, c))
    previews[channel] = preview_label
    
    chk = ttk.Checkbutton(scrollable_frame, text="Invert", variable=invert_vars[channel], style="TCheckbutton", command=lambda c=channel: update_preview(c))
    chk.grid(row=i+10, column=2, padx=5, pady=5)
    
    clear_btn = ttk.Button(scrollable_frame, text="Clear", style="TButton", command=lambda c=channel: clear_image(c))
    clear_btn.grid(row=i+10, column=3, padx=5, pady=5)

# Resolution label and entry
resolution_label = ttk.Label(scrollable_frame, text="Resolution:", style="TLabel")
resolution_label.grid(row=14, column=0, padx=5, pady=5, sticky="W")
resolution_var = tk.StringVar(value="1024")
resolution_entry = ttk.Entry(scrollable_frame, textvariable=resolution_var, width=10)
resolution_entry.grid(row=14, column=1, padx=5, pady=5)
resolution_entry.bind("<Return>", evaluate_resolution)

# Generate mask map button
generate_btn = ttk.Button(scrollable_frame, text="Generate Mask Map", style="TButton", command=generate_mask_map)
generate_btn.grid(row=15, column=0, columnspan=3, pady=10)

# Mask map preview label
mask_preview_label = ttk.Label(scrollable_frame, style="TLabel")
mask_preview_label.grid(row=16, column=1, padx=5, pady=5)

# Save mask map button
save_btn = ttk.Button(scrollable_frame, text="Save Mask Map", style="TButton", command=save_mask_map)
save_btn.grid(row=17, column=0, columnspan=3, pady=10)
save_btn.grid_remove()

# Status label
status_label = ttk.Label(scrollable_frame, text="", style="TLabel")
status_label.grid(row=18, column=0, columnspan=3, pady=5)

root.mainloop()
