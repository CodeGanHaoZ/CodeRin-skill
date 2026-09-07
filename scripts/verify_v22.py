#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 加粗安全扫描器（严格版 V2.2+）

与基础版的区别：扫描前会剔除代码块（```）和行内代码（`），
只对真正会被渲染的正文做检测，避免示例代码中的反面教材造成误报。

用法：
    python verify_v22.py                       # 自动定位 ../examples 下的示例文章
    python verify_v22.py <file1.md> [file2.md] # 扫描指定文件
"""
import re
import sys
import pathlib

DANGER = ['%', '"', '\u201c', '\u201d', '\\']


def resolve_targets(args):
    if args:
        return [pathlib.Path(a) for a in args]

    example_dir = pathlib.Path(__file__).resolve().parent.parent / 'examples'
    if example_dir.is_dir():
        targets = sorted(example_dir.glob('*.md'))
        if targets:
            return targets

    print('[提示] 未指定文件且未找到 examples/ 目录，请传入文件路径。')
    print('用法: python verify_v22.py <file.md>')
    return []


def strip_code(content):
    """剔除代码块与行内代码，只保留渲染正文。"""
    clean = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    clean = re.sub(r'`[^`\n]*`', '', clean)
    return clean


def scan_file(path):
    content = path.read_text(encoding='utf-8')
    clean = strip_code(content)

    bolds = re.findall(r'\*\*([^*]+)\*\*', clean)
    bad = [b for b in bolds if any(ch in b for ch in DANGER)]
    strongs = re.findall(r'<strong>([^<]+)</strong>', clean)

    cn_quote = [s for s in strongs if '\u201c' in s or '\u201d' in s]
    en_quote = [s for s in strongs if '"' in s]
    pct = [s for s in strongs if '%' in s]

    return bolds, bad, strongs, cn_quote, en_quote, pct


def main():
    targets = resolve_targets(sys.argv[1:])
    if not targets:
        sys.exit(1)

    total_bad = 0
    for target in targets:
        if not target.exists():
            print(f'[跳过] 文件不存在: {target}')
            continue

        bolds, bad, strongs, cn, en, pct = scan_file(target)

        print(f'\n=== {target.name}（排除代码块/行内代码）===')
        if bad:
            print(f'[FAIL] 正文中 {len(bad)} 处含危险字符的 ** 加粗:')
            for item in bad:
                print(f'   -> {item[:60]}')
            total_bad += len(bad)
        else:
            print(f'[PASS] 正文 {len(bolds)} 处 ** 加粗均干净')

        print(f'[INFO] <strong> 接管 {len(strongs)} 处'
              f'（中文引号 {len(cn)} / 英文引号 {len(en)} / 百分号 {len(pct)}）')

    print('\n' + '=' * 40)
    if total_bad:
        print(f'总计: 发现 {total_bad} 处危险模式，请替换为 <strong> 标签')
        sys.exit(1)

    print('总计: 正文危险模式 0 处 [PASS]')


if __name__ == '__main__':
    main()
