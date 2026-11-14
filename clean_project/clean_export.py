import os
import shutil

# 1. 定义需要彻底排除的臃肿目录
EXCLUDE_DIRS = {
    'reports', 'runs', 'venv', '.venv', 'node_modules', 
    '.git', '__pycache__', '.idea', 'dist', 'build'
}

# 2. 定义允许保留的文件后缀（只留代码和配置）
INCLUDE_EXTS = {'.py', '.json', '.yaml', '.yml', '.ini', '.toml', '.md', '.txt'}

src_dir = '.'
dest_dir = './clean_project'

# 如果已存在旧的 clean_project，先清空重新生成
if os.path.exists(dest_dir):
    shutil.rmtree(dest_dir)

print("正在过滤并复制纯代码文件...")

count = 0
for root, dirs, files in os.walk(src_dir):
    # 动态裁剪掉不需要遍历的目录，节省时间
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
    
    # 计算目标文件夹的相对路径
    rel_path = os.path.relpath(root, src_dir)
    target_sub_dir = os.path.join(dest_dir, rel_path) if rel_path != '.' else dest_dir

    for file in files:
        ext = os.path.splitext(file)[1].lower()
        # 仅复制符合条件的代码和配置文件
        if ext in INCLUDE_EXTS:
            os.makedirs(target_sub_dir, exist_ok=True)
            src_file = os.path.join(root, file)
            dest_file = os.path.join(target_sub_dir, file)
            shutil.copy2(src_file, dest_file)
            count += 1

print(f"清理完成！成功提取了 {count} 个代码与配置文件，已生成到本地的 `clean_project` 文件夹中。")