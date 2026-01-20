# Notion2Obsidian

**Author / 作者**: Li Ning

[English](#english) | [中文](#chinese)

<a name="english"></a>

## 🇬🇧 English

**Notion2Obsidian** is a powerful Python script designed to perfectly migrate Markdown notes exported from Notion to Obsidian.

It not only fixes image links and formatting issues but also automatically reconstructs header levels based on indentation and thoroughly eliminates vertical indentation lines in Obsidian, giving your notes a clean, standardized look.

### ✨ Key Features

*   **Smart Header Reconstruction**: Automatically converts Notion's indented lists into Obsidian Headers to preserve hierarchy without indentation.
    *   **Root (No indent)** -> `#### Header`
    *   **Level 1 (1 indent)** -> `##### Header`
    *   **Level 2+ (2+ indents)** -> `###### Header`
*   **Deep Layout Cleaning**:
    *   **Remove Vertical Lines**: Forces all content (headers, body, images) to be left-aligned, removing extra indentation that causes visual clutter in Obsidian.
    *   **List Marker Cleanup**: Automatically removes list markers (`-`, `*`, `1.`) after converting them to headers.
    *   **Empty Line Optimization**: Intelligently merges consecutive empty lines to keep the document compact.
*   **Image & Link Fixes**:
    *   **HEIC to JPG**: Automatically scans and converts HEIC images to JPG for better compatibility (requires `pillow-heif`).
    *   **Wiki-links**: Converts standard Markdown image links `![]()` to Obsidian's format `![[]]`.
    *   **Path Fix**: Removes path prefixes in links to adapt to current directory structure.
*   **Code Block Protection**: Smartly identifies ` ``` ` code blocks, ensuring code content formatting is preserved and not flattened.
*   **Non-Destructive**: Output is saved to a separate `Obsidian_Migration_Export` folder, ensuring your original data remains safe.

### 🛠️ Requirements

*   Python 3.6+
*   Dependencies: `Pillow`, `pillow-heif`

### 🚀 Quick Start (快速开始)

#### 1. Run the Script (运行脚本)

Simply run the script. It will **automatically detect and install** required dependencies (`Pillow`, `pillow-heif`) if they are missing.

直接运行脚本即可。如果有缺失的依赖库（如 `Pillow`, `pillow-heif`），脚本会**自动检测并安装**。

```bash
python Notion2Obsidian.py
```

#### 2. Enter Path (输入路径)

Enter your Notion export folder path when prompted.

根据提示输入您的 Notion 导出文件夹路径。

![Demo](demo.jpg)

#### 3. Check Results (查看结果)

After the script finishes, look for the **`Obsidian_Migration_Export`** folder created in the same directory as your source folder.

Simply drag this folder into your Obsidian vault!

脚本运行完成后，在源文件夹同级目录下查找生成的 **`Obsidian_Migration_Export`** 文件夹，将其拖入 Obsidian 即可！

## ⚙️ Configuration / 配置

Open `Notion2Obsidian.py` to adjust settings at the top:
打开 `Notion2Obsidian.py` 文件，可以在顶部调整配置项：

```python
# --- Configuration / 配置项 ---
HEIC_TO_JPG = True       # Enable HEIC to JPG conversion / 是否开启 HEIC 转 JPG
SPACE_PER_LEVEL = 4      # Spaces per indentation level / 定义多少个空格算一级缩进 (default/默认 4)
```

## 📄 License

MIT License

