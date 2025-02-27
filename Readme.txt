🎭 Mask Map HDRP Lit - Unity Shader Texture Packer

Welcome to Mask Map HDRP Lit - Unity Shader Texture Packer! 🎨🚀

This tool allows you to create a Mask Map compatible with Unity's High Definition Render Pipeline (HDRP) by combining different textures into a single RGBA image. All with a simple, modern, and intuitive graphical interface!

✨ Features

✅ Drag & Drop support for quick texture loading 🎯

✅ Invert channels if needed ⚡

✅ Automatic generation of Mask Map and Detail Map 🖼️

✅ Real-time previews of loaded images 👀

✅ Custom resolution support (set your desired size!) 📏

✅ Save the final Mask Map as a PNG file 💾

✅ Fully compatible with Unity HDRP for advanced PBR rendering 🎮

🖌️ Mask Map Channels

Channel

Content

R (Red)

Metallic ⚙️

G (Green)

Ambient Occlusion 🌿

B (Blue)

Detail Map (Optional) 🔍

A (Alpha)

Smoothness ✨

💡 If no image is loaded for a given channel, a default white fill is used.

🏗️ Installation & Setup

Make sure you have Python 3.x installed 🐍

Install the required packages by running:

pip install pillow tkinterdnd2

Launch the script with:

python mask_map_generator.py

🎮 How to Use

Drag and drop or select images for R, G, B, and A channels.

(Optional) Invert channels if needed using the checkboxes.

Set the desired resolution.

Click "Generate Mask Map" to see the preview.

Click "Save Mask Map" to export it!

Import it into Unity and use it in your HDRP material! 🏆

📌 Notes

If you want to add a Detail Map, you can generate a separate one and insert it into the B channel of the Mask Map.

The tool supports .png, .jpg, and .tga files.

If you load a Normal Map, the tool automatically extracts the X (A) and Y (G) channels for the Detail Map.

🚀 Contributions & Support

Found a bug? Want to suggest a feature? Open an Issue or a Pull Request on GitHub! 🎉

💬 For questions or support, feel free to reach out! 😊

🛠️ Made with ❤️ by San Liuk
