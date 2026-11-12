# Changelog

## Unreleased

### ✨ New
- **Update notice.** At startup the app checks GitHub for a newer release; if there is one, an **Update available** button appears at the top right and opens the download page. Nothing is installed automatically, and the check is skipped silently when offline.
- The version number is shown at the bottom right.

## v1.1.0 - New UI, bug fixes and macOS build

### 🐛 Fixes
- **The Mask Map can now be saved.** The Save button was never shown after "Generate Mask Map".
- **Full-resolution output.** Loaded textures were shrunk to a 150 px preview, so the Mask Map was an upscaled thumbnail.
- Generating twice with **Invert** no longer cancels the inversion.
- Drag & drop works with folders and files that contain **spaces**.
- **16-bit textures** (Substance, Blender…) are converted correctly instead of turning white.
- Non-square textures keep their aspect ratio; invalid resolutions show a message instead of failing silently.
- Errors are now always visible (status bar or dialog).

### ✨ New
- Redesigned UI with three tabs: **Mask Map**, **Detail Map**, **Unpack**. No more scrolling.
- **Click a preview or Browse…** to load textures (drag & drop still works).
- **"If empty" value** per channel: e.g. Metallic = 0 without creating a black texture.
- **Tooltips** on every control, explaining what each channel does in HDRP.
- Resolution **Source** keeps your texture size (or pick 256 – 8192).
- Export to **PNG, TGA or TIFF**, with a suggested file name (`Rock_Metallic.png` → `Rock_MaskMap.png`).
- Output preview shows **RGB and Alpha** separately.
- Detail Map channels default to neutral 0.5; DirectX normal maps: tick Invert on Normal Y.
- Unpack keeps the source resolution and adds **Save All**.
- **macOS build** (Apple Silicon). It's new: feedback is welcome!

### 📦 Downloads
- **Windows**: `MaskMapGenerator.exe`
- **macOS** (Apple Silicon): `MaskMapGenerator-macOS.zip`. The app is not signed: right-click → **Open** on first launch. If macOS says it is damaged, run `xattr -cr MaskMapGenerator.app`.

In Unity, import the generated maps with **sRGB (Color Texture) OFF** and **Alpha Is Transparency OFF**.

## v1.0.0 - Initial Release

- Generate Mask Maps (Metallic, AO, Detail Mask, Smoothness)
- Generate Detail Maps (Albedo, Normal X/Y, Smoothness)
- Unpack existing textures into channels
- Windows executable
