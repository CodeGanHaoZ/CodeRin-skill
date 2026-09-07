#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 加粗安全扫描器（基础版）

用途：扫描 Markdown 文件中的 `**加粗**` 语法，检测是否包含会导致
微信公众号等非标准渲染器解析失败的危险字符。

用法：
    python verify_bold.py                       # 自动定位 ../examples 下的示例文章
    python verify_bold.py <file1.md> [file2.md] # 扫描指定文件

危险字符：% 、英文引号 " 、中文引号 " " 、反斜杠 \
"""
import re
import sys
import pathlib

# 危险字符清单
DANGER = ['%', '"', '\u201c', '\u201d', '\\']


def resolve_targets(args):
    """解析待扫描文件：优先命令行参数，否则自动定位示例目录。"""
    if args:
        return [pathlib.Path(a) for a in args]

    example_dir = pathlib.Path(__file__).resolve().parent.parent / 'examples'
    if example_dir.is_dir():
        targets = sorted(example_dir.glob('*.md'))
        if targets:
            return targets

    print('[提示] 未指定文件且未找到 examples/ 目录，请传入文件路径。')
    print('用法: python verify_bold.py <file.md>')
    return []


def strip_code(content):
    """剔除代码块与行内代码，只保留渲染正文。"""
    clean = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    return re.sub(r'`[^`\n]*`', '', clean)


def code_only(content):
    """提取代码块与行内代码内容（用于识别教学用的反面示例）。"""
    blocks = re.findall(r'```.*?```', content, flags=re.DOTALL)
    inline = re.findall(r'`[^`\n]*`', strip_code(content))
    return '\n'.join(blocks) + '\n' + '\n'.join(inline)


def scan_file(path):
    """扫描单个文件。返回 (加粗总数, 正文危险项, 代码块内危险项, strong 标签数)。"""
    content = path.read_text(encoding='utf-8')

    bolds = re.findall(r'\*\*([^*]+)\*\*', content)
    strongs = re.findall(r'<strong>([^<]+)</strong>', content)

    # 正文（会被渲染的部分）
    prose_bolds = re.findall(r'\*\*([^*]+)\*\*', strip_code(content))
    prose_bad = [b for b in prose_bolds if any(ch in b for ch in DANGER)]

    # 代码块内（教学用的反面示例，不参与渲染）
    code_bad = [b for b in re.findall(r'\*\*([^*]+)\*\*', code_only(content))
                if any(ch in b for ch in DANGER)]

    return len(bolds), prose_bad, code_bad, len(strongs)


def main():
    targets = resolve_targets(sys.argv[1:])
    if not targets:
        sys.exit(1)

    total_bad = 0
    for target in targets:
        if not target.exists():
            print(f'[跳过] 文件不存在: {target}')
            continue

        count, prose_bad, code_bad, strong_count = scan_file(target)
        name = target.name

        print(f'\n=== {name} ===')
        if prose_bad:
            print(f'[FAIL] 正文 {len(prose_bad)} 处含危险字符的 ** 加粗:')
            for item in prose_bad:
                print(f'   -> {item[:60]}')
            total_bad += len(prose_bad)
        else:
            print(f'[PASS] 正文 {count} 处 ** 加粗内容均干净')

        if code_bad:
            print(f'[INFO] 代码块内另有 {len(code_bad)} 处（教学用反面示例，不参与渲染，无需处理）')

        print(f'[INFO] <strong> 标签接管 {strong_count} 处')

    print('\n' + '=' * 40)
    if total_bad:
        print(f'总计: 正文发现 {total_bad} 处危险模式，请替换为 <strong> 标签')
        sys.exit(1)

    print('总计: 正文危险模式 0 处 [PASS]')


if __name__ == '__main__':
    main()
