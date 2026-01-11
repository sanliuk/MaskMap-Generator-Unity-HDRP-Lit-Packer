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

- ✅ **Drag & Drop** for fast texture loading 🎯  
- ✅ **Invert channels** with a single click ⚡  
- ✅ **Automatic generation** of Mask Maps and Detail Maps 🎨  
- ✅ **Real-time previews** of loaded images 👀  
- ✅ **Custom resolution support** 📏  
- ✅ **One-click PNG export** 💾  
- ✅ **Fully compatible with Unity HDRP** for advanced PBR rendering 🎮  
- ✅ **Normal Map support**: Automatically extract X (A) and Y (G) for the Detail Map!  
- ✅ **Directly insert Detail Map into the Mask Map**  

---

## 🎨 Mask Map Channels  

| **Channel**  | **Content**                |  
|-------------|----------------------------|  
| **R (Red)**    | Metallic ⚙️               |  
| **G (Green)**  | Ambient Occlusion 🌿      |  
| **B (Blue)**   | Detail Map (Optional) 🔍  |  
| **A (Alpha)**  | Smoothness ✨             |  

> 💡 If an image is not loaded for a channel, a default white fill will be used.  

---

## 🏰 Installation & Setup  

1. Ensure you have **Python 3.x** installed 🐍
2. Install the required packages by running:
   ```sh
   pip install -r requirements.txt
   ```
   Or manually:
   ```sh
   pip install pillow tkinterdnd2
   ```
3. Run the script with:
   ```sh
   python MaskMapHDRP.py
   ```  

---

## 🎮 How to Use  

1. **Drag and drop or select** images for **R, G, B, and A** channels.  
2. *(Optional)* Invert channels if needed using the checkboxes.  
3. Set the **desired resolution**.  
4. Click **"Generate Mask Map"** to preview the result.  
5. Click **"Save Mask Map"** to export the final image!  
6. *(Optional)* Load a **Normal Map** to automatically extract X and Y channels for the Detail Map.  
7. *(Optional)* Insert the **Detail Map** directly into the Mask Map with one click.  
8. **Import the Mask Map into Unity** and use it in your HDRP material! 🏆  


![Unity Workflow](https://raw.githubusercontent.com/sanliuk/images/main/MaskMap4.png)

---

## 📌 Notes  

- If you want to **add a Detail Map**, you can generate it separately and insert it into the B channel of the Mask Map.  
- The tool supports **.png, .jpg, and .tga** formats.  
- **Normal Map loading** is supported for generating Detail Maps.  
- A **desaturation feature** helps you convert an image to grayscale directly from the interface.  

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
