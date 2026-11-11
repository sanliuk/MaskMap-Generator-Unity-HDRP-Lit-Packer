# 🎯 Mask Map HDRP Lit - Unity Shader Texture Packer  

Welcome to **Mask Map HDRP Lit - Unity Shader Texture Packer**! 🎨🚀  

This tool allows you to create a **Mask Map** compatible with **Unity's High Definition Render Pipeline (HDRP)** by combining different textures into a single RGBA image. Now with a modern, intuitive UI and advanced new features!  

![Mask Map Generator Screenshot](https://raw.githubusercontent.com/sanliuk/images/main/MaskMap1.png)  
![Mask Map Generator Screenshot](https://raw.githubusercontent.com/sanliuk/images/main/MaskMap2.png)  

---

## 🖥️ Unity Workflow  

![Unity Workflow](https://raw.githubusercontent.com/sanliuk/images/main/MaskMap3.png)  

From Unity's documentation: [Mask Map and Detail Map](https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@10.2/manual/Mask-Map-and-Detail-Map.html)  

---

## ✨ Features & Updates  

- ✅ **Three tabs**: Mask Map, Detail Map and Unpack. Everything fits on one screen 🗂️  
- ✅ **Drag & Drop** or **click a preview / Browse…** to load textures 🎯  
- ✅ **Invert channels** with a single click (e.g. Roughness → Smoothness) ⚡  
- ✅ **Tooltips** on every control explain what each channel does in HDRP 💬  
- ✅ **"If empty" value per channel**: no need to create a black texture for non-metals 🎚️  
- ✅ **Real-time previews**, with RGB and Alpha shown separately 👀  
- ✅ **Keeps the source resolution** by default, or pick 256 – 8192. Non-square textures keep their aspect ratio 📏  
- ✅ **Export to PNG, TGA or TIFF** 💾  
- ✅ **16-bit textures** (e.g. from Substance or Blender) are converted correctly  
- ✅ **Normal Map support**: automatically extracts X (A) and Y (G) for the Detail Map  
- ✅ **Unpack** any RGBA texture into its four channels, one by one or all at once  
- ✅ **Fully compatible with Unity HDRP** for advanced PBR rendering 🎮  

---

## 🎨 Mask Map Channels  

| **Channel**  | **Content**                | **If empty (default)** |  
|-------------|----------------------------|------------------------|  
| **R (Red)**    | Metallic ⚙️               | 0 (non-metal)          |  
| **G (Green)**  | Ambient Occlusion 🌿      | 1 (no occlusion)       |  
| **B (Blue)**   | Detail Mask 🔍 (where the Detail Map is applied) | 1 (everywhere) |  
| **A (Alpha)**  | Smoothness ✨ (invert a Roughness map) | 0.5        |  

> 💡 The **B channel is the Detail Mask**, not the Detail Map itself. The Detail Map is a separate texture that goes into the material's *Detail Map* slot.  

## 🧩 Detail Map Channels  

| **Channel**  | **Content**                       | **If empty (default)** |  
|-------------|-----------------------------------|------------------------|  
| **R (Red)**    | Albedo (desaturated automatically) | 0.5 (neutral)       |  
| **G (Green)**  | Normal Y                          | 0.5 (flat)             |  
| **B (Blue)**   | Smoothness                        | 0.5 (neutral)          |  
| **A (Alpha)**  | Normal X                          | 0.5 (flat)             |  

> 💡 Every "If empty" value can be changed in the app (0 – 1).  

---

## 📥 Download (No Python Required)

Download the standalone executable for your platform:

| Platform | Download |
|----------|----------|
| **Windows** | [MaskMapGenerator.exe](https://github.com/sanliuk/MaskMap-Generator-Unity-HDRP-Lit-Packer/releases/latest) |
| **macOS** | [MaskMapGenerator.app](https://github.com/sanliuk/MaskMap-Generator-Unity-HDRP-Lit-Packer/releases/latest) |

> 💡 Just download and run - no installation required!

---

## 🏰 Installation & Setup (From Source)

If you prefer to run from source code:

1. Ensure you have **Python 3.x** installed 🐍
2. Install the required packages:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the application:
   ```sh
   python MaskMapHDRP.py
   ```

---

## 🔨 Building Executables

To build standalone executables yourself:

1. Install PyInstaller:
   ```sh
   pip install pyinstaller
   ```
2. Run the build script:
   ```sh
   python build.py
   ```
3. Find your executable in the `dist/` folder

---

## 🎮 How to Use  

1. Open the **Mask Map** tab.  
2. **Drag and drop** a texture onto a channel preview, or **click the preview / Browse…** to select it.  
3. *(Optional)* Tick **Invert** where needed. For example, a **Roughness** map must be inverted to become **Smoothness**.  
4. *(Optional)* For channels without a texture, set the **If empty** value (e.g. Metallic = 0 for non-metallic materials).  
5. Pick the **Resolution**. **Source** keeps the size of your textures.  
6. Click **Generate Mask Map**, check the RGB and Alpha previews, then click **Save…** (PNG, TGA or TIFF).  
7. *(Optional)* In the **Detail Map** tab, use **Load Normal Map…** to fill Normal X and Normal Y automatically. For a DirectX normal map, tick **Invert** on Normal Y.  
8. *(Optional)* Use the **Unpack** tab to split an existing RGBA texture back into its channels.  
9. **Import the textures into Unity** (see below) and use them in your HDRP Lit material! 🏆  


![Unity Workflow](https://raw.githubusercontent.com/sanliuk/images/main/MaskMap4.png)

---

## 🧰 Importing in Unity  

For both the Mask Map and the Detail Map, in the texture **Import Settings**:  

- **sRGB (Color Texture): OFF**. These are data textures, not colors. With sRGB on, AO, metallic and smoothness come out wrong.  
- **Alpha Is Transparency: OFF**. Smoothness/Normal X live in the alpha channel and must not be treated as transparency.  
- Compression: **High Quality (BC7)** is recommended to keep the alpha channel clean.  

---

## 📌 Notes  

- Supported input formats: **.png, .jpg, .jpeg, .tga, .tif, .tiff, .bmp** (8-bit and 16-bit).  
- Output formats: **.png, .tga, .tif**.  
- Textures of different sizes are resized to the output resolution. If their aspect ratios differ, the app warns you that they were stretched.  
- Changing any input after generating disables **Save…** until you generate again, so you never export an outdated map.  
- If drag & drop is not available on your system, clicking the previews always works.  

---

## 🚀 Contributions & Support  

Found a bug? Have a feature suggestion? Open an **Issue** or a **Pull Request** on GitHub! 🎉  

💬 For any questions or support, feel free to reach out! 😊  

---

## 💬 Join Our Community!  

Need help or want to learn more about **game development** and **3D modeling**?  
Join our **Discord community** for support, discussions, and exclusive tutorials! 🎮🔥  

[![Join our Discord](https://img.shields.io/badge/Join%20us%20on-Discord-5865F2?logo=discord&logoColor=white)](https://discord.com/invite/8GBkm252cS)  

---

### 🛠️ Created with ❤️ by San Liuk
🚨 For important stuff, contact me at: [info@sanliuk.com](mailto:info@sanliuk.com) ✉️
