
import sys
import re
import shutil
import subprocess
import importlib.util
from pathlib import Path
from urllib.parse import unquote

def check_and_install_packages(packages):
    """
    检查并自动安装缺失的依赖库
    """
    for package_name, import_name in packages.items():
        if importlib.util.find_spec(import_name) is None:
            print(f"检测到缺失依赖库: {package_name}，正在自动安装...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                print(f"✅ {package_name} 安装成功！")
            except subprocess.CalledProcessError:
                print(f"❌ {package_name} 安装失败。请尝试手动运行: pip install {package_name}")
                sys.exit(1)

# 定义依赖映射 {PyPI名称: import名称}
REQUIRED_PACKAGES = {
    "Pillow": "PIL",
    "pillow-heif": "pillow_heif"
}

# 执行检查
check_and_install_packages(REQUIRED_PACKAGES)

# 依赖安装完成后再导入
from PIL import Image
from pillow_heif import register_heif_opener

# 注册 pillow_heif 以支持读取 HEIC 格式
register_heif_opener()

# --- 配置项 ---
HEIC_TO_JPG = True       # 是否开启 HEIC 转 JPG
SPACE_PER_LEVEL = 4      # 定义多少个空格算一级缩进 (调整为4，适应通常的 Tab/4空格缩进)

def convert_heic_to_jpg(folder_path):
    """
    扫描文件夹中的 .heic 文件，将其转换为 .jpg 格式并删除原文件。
    """
    if not HEIC_TO_JPG:
        return

    path = Path(folder_path)
    # 使用 set 去重，防止 Windows 下大小写敏感导致的重复匹配
    # 使用 rglob 递归查找子文件夹中的图片
    heic_files = set(list(path.rglob('*.heic')) + list(path.rglob('*.HEIC')))
    
    if heic_files:
        print(f"找到 {len(heic_files)} 个 HEIC 文件，开始转换...")
        for heic_file in heic_files:
            # 双重检查文件是否存在(防止重复处理或其他误删)
            if not heic_file.exists():
                continue
                
            try:
                jpg_file = heic_file.with_suffix('.jpg')
                with Image.open(heic_file) as img:
                    img.convert('RGB').save(jpg_file, "JPEG", quality=90)
                print(f"[转换成功] {heic_file.name} -> {jpg_file.name}")
                heic_file.unlink()
            except Exception as e:
                print(f"[错误] 转换 {heic_file.name} 失败: {e}")

def clean_filename(url_or_name):
    """通用文件名清理工具"""
    decoded = unquote(url_or_name)
    name = Path(decoded).name.strip()
    if name.lower().endswith('.heic'):
        name = Path(name).with_suffix('.jpg').name
    return name

def fix_line_links(line):
    """
    单行链接修复逻辑
    """
    # 1. 匹配被 ` 包裹的链接 (防止匹配到代码块内的，这里主要处理行内代码)
    code_wrapped_pattern = re.compile(r'`(!\[.*?\](?:\[.*?\]|\(.*?\)))`')
    # 2. 匹配标准图片链接
    link_pattern = re.compile(r'(?:!|)?\[(.*?)\]\((.*?\.(?:png|jpg|jpeg|gif|bmp|webp|heic))\)', re.IGNORECASE)
    # 3. 匹配裸露的 !Filename.png 文本
    bare_pattern = re.compile(r'^!([^\[\(\)\n]+\.(?:png|jpg|jpeg|gif|bmp|webp|heic))\s*$', re.IGNORECASE)
    # 4. 匹配已有的 Obsidian 链接
    obsidian_pattern = re.compile(r'!\[\[(.*?)\]\]')
    # 5. 双感叹号修复
    double_bang_pattern = re.compile(r'!+\s*(!\[\[)')

    # 逻辑应用
    line = code_wrapped_pattern.sub(lambda m: m.group(1), line)
    
    def convert_link(m):
        return f"![[{clean_filename(m.group(2))}]]"
    line = link_pattern.sub(convert_link, line)
    
    line = bare_pattern.sub(lambda m: f"![[{clean_filename(m.group(1))}]]", line)
    line = obsidian_pattern.sub(lambda m: f"![[{clean_filename(m.group(1))}]]", line)
    line = double_bang_pattern.sub('![[', line)
    
    return line

def process_file_content(content):
    """
    文档深度清洗与重构核心逻辑
    """
    lines = content.splitlines()
    new_lines = []
    
    # 状态标记
    in_code_block = False
    last_line_empty = False
    
    # 正则预编译
    code_fence_pattern = re.compile(r'^\s*```')
    header_pattern = re.compile(r'^\s*(#+)\s+(.*)')
    list_pattern = re.compile(r'^([ \t]*)([-*+]|\d+\.)\s+(.*)')
    image_pattern = re.compile(r'^\s*!')

    for line in lines:
        # --- 代码块保护逻辑 ---
        if code_fence_pattern.match(line):
            in_code_block = not in_code_block
            # 代码块的栅栏行本身也左对齐
            new_lines.append(line.lstrip())
            last_line_empty = False
            continue
            
        if in_code_block:
            # 代码块内部：完全保持原样 (包括缩进)
            new_lines.append(line)
            last_line_empty = False
            continue
            
        # --- 常规行清洗 ---
        stripped_line = line.rstrip()
        
        # 空行合并
        if not stripped_line:
            if not last_line_empty:
                new_lines.append("")
                last_line_empty = True
            continue 
        last_line_empty = False
        
        # 链接修复 (应用于所有非代码行)
        line_fixed = fix_line_links(stripped_line)
        
        # --- 标题与层级重构逻辑 ---
        
        # A. 现有标题: 1:1 映射, 强制左对齐
        h_match = header_pattern.match(line_fixed)
        if h_match:
            hashes = h_match.group(1)
            text = h_match.group(2)
            new_lines.append(f"{hashes} {text}")
            continue
            
        # B. 图片行: 强制左对齐 (不加标题)
        if image_pattern.match(line_fixed):
            new_lines.append(line_fixed.lstrip())
            continue
            
        # C. 列表项: 缩进 -> 标题 (核心逻辑)
        l_match = list_pattern.match(line_fixed)
        if l_match:
            indent_str = l_match.group(1)
            # marker = l_match.group(2) # 丢弃列表符
            content_text = l_match.group(3)
            
            # 计算空格数 (Tab=4空格)
            spaces = indent_str.count(' ') + indent_str.count('\t') * 4
            
            # 计算缩进层级 (向下取整)
            indent_level = int(spaces / SPACE_PER_LEVEL)
            
            # 映射逻辑 (调整: 从 Level 0 开始映射)
            if indent_level == 0:
                # 0层缩进 (0-3空格) -> 4级标题 (修复 Root 项不转换的问题)
                new_lines.append(f"#### {content_text}")
            elif indent_level == 1:
                # 1层缩进 (4-7空格) -> 5级标题
                new_lines.append(f"##### {content_text}")
            elif indent_level >= 2:
                # 2层及以上 -> 6级标题
                new_lines.append(f"###### {content_text}")
            continue

        # D. 普通文段: 强制左对齐
        # 这一步实现了 "消除垂直缩进线" 的要求
        new_lines.append(line_fixed.lstrip())

    return "\n".join(new_lines) + "\n"

def process_folder(source_path):
    """
    核心处理入口
    """
    source_root = Path(source_path).resolve()
    # 输出文件夹: Obsidian_Migration_Export
    dest_root = source_root.parent / "Obsidian_Migration_Export"
    
    if dest_root.exists():
        print(f"目标文件夹 {dest_root} 已存在，正在清空...")
        shutil.rmtree(dest_root)
    dest_root.mkdir()
    
    print(f"源目录: {source_root}")
    print(f"输出目录: {dest_root}")
    print("开始 Obsidian 最佳实践转换...\n")

    files = [p for p in source_root.rglob('*') if p.is_file()]
    
    for src_file in files:
        rel_path = src_file.relative_to(source_root)
        dest_file = dest_root / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        
        if src_file.suffix.lower() == '.md':
            try:
                content = src_file.read_text(encoding='utf-8')
                new_content = process_file_content(content)
                dest_file.write_text(new_content, encoding='utf-8')
                print(f"[已重构] {rel_path}")
            except Exception as e:
                print(f"[出错] {rel_path}: {e}")
        elif src_file.suffix.lower() in ['.heic', '.heif']:
             shutil.copy2(src_file, dest_file)
        else:
            shutil.copy2(src_file, dest_file)

    # 统一处理 HEIC 转 JPG
    convert_heic_to_jpg(dest_root)

def main():
    print("=== Notion2Obsidian 迁移导出助手 (Final) ===")
    
    target_dir = input("请输入通过 Notion 导出的源文件夹路径: ").strip()
    if not target_dir:
        input("路径为空，按回车退出...")
        return
    
    folder_path = Path(target_dir)
    if not folder_path.exists():
        print(f"错误: 路径 '{target_dir}' 不存在！")
        input("按回车键退出...")
        return
    
    process_folder(folder_path)
    
    print("-" * 30)
    print(f"\n✅ 全部完成！请查看 'Obsidian_Migration_Export' 文件夹。\n")
    input("按回车键退出程序...")

if __name__ == "__main__":
    main()
