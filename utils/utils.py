import os
import shutil


def copy_repaired_files(source_root, destination_root):
    """
    遍历 source_root 中所有 project/commit_x 目录，读取其中的 repaired_ids.txt，
    找到每个需要保留的 id，提取该 id 目录下的:
      - before/ 子目录（若存在）
      - 所有 *_antipattern.json 文件
    然后将这些内容复制到 destination_root 中，保持原始目录结构。
    参数:
    - source_root (str): 源目录根路径，例如 /data/Anti-PatternRAG/
    - destination_root (str): 目标目录根路径，用于保存提取出的文件结构

    示例结构:
    source_root/
        └── project1/
            └── commit_1/
                ├── 12345/
                │   └── something_antipattern.json
                ├── 23456/
                └── repaired_ids.txt  ← 内容如：12345

    输出结构:
    destination_root/
        └── project1/
            └── commit_1/
                └── 12345/
                    ├── before/
                    └── *_antipattern.json
    """
    for project_name in os.listdir(source_root):
        project_path = os.path.join(source_root, project_name)
        if not os.path.isdir(project_path):
            continue

        for commit_name in os.listdir(project_path):
            commit_path = os.path.join(project_path, commit_name)
            if not os.path.isdir(commit_path):
                continue

            # repaired_ids.txt 文件路径
            repaired_ids_file = os.path.join(commit_path, "repaired_ids.txt")
            if not os.path.isfile(repaired_ids_file):
                print(f"[跳过] 缺失 repaired_ids.txt: {repaired_ids_file}")
                continue

            # 读取需要处理的 ID 列表
            with open(repaired_ids_file, "r") as f:
                repaired_ids = {line.strip() for line in f if line.strip()}

            for item_name in os.listdir(commit_path):
                item_path = os.path.join(commit_path, item_name)

                if os.path.isdir(item_path) and item_name in repaired_ids:
                    id_dir = item_path
                    relative_base = os.path.relpath(id_dir, source_root)
                    dest_id_base = os.path.join(destination_root, relative_base)

                    # ✅ 1. 复制 before 子目录（如果存在）
                    before_dir = os.path.join(id_dir, "before")
                    if os.path.isdir(before_dir):
                        dest_before_dir = os.path.join(dest_id_base, "before")
                        os.makedirs(os.path.dirname(dest_before_dir), exist_ok=True)
                        shutil.copytree(before_dir, dest_before_dir, dirs_exist_ok=True)

                    # ✅ 2. 复制 *_antipattern.json 文件（如果存在）
                    for file in os.listdir(id_dir):
                        if file.endswith("_antipattern.json"):
                            src_file = os.path.join(id_dir, file)
                            dst_file = os.path.join(dest_id_base, file)
                            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                            shutil.copy2(src_file, dst_file)

            print(f"[处理完成] {commit_path}")

    print("✅ 所有文件处理完毕。")


if __name__ == "__main__":
    source_root = "/Users/moncheri/Downloads/main/重构/反模式修复数据集构建/extract_antipatterns_and_repair/CH/apache"
    destination_root = "/Users/moncheri/Downloads/main/重构/反模式修复数据集构建/RefactorRAG/Anti-PatternRAG/data/CH"
    copy_repaired_files(source_root, destination_root)
