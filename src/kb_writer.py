"""
Kebalikan dari kb_parser.py: mengubah daftar KBEntry kembali jadi teks file
knowledge base dengan format yang sama (kategori + KB-XXX + Pertanyaan/
Jawaban/Keywords), supaya panel admin bisa menyimpan perubahan tanpa
merusak struktur file aslinya.

Entry dikelompokkan ulang berdasarkan kategori (urutan kemunculan pertama
kategori tetap dijaga), jadi hasilnya tetap rapi meski entry baru ditambah
di posisi mana pun.
"""

from __future__ import annotations
import os
import re
import shutil
from datetime import datetime
from collections import OrderedDict
from kb_parser import KBEntry

MAX_BACKUPS = 20


def _backup_dir(filepath: str) -> str:
    d = os.path.join(os.path.dirname(filepath), "backups")
    os.makedirs(d, exist_ok=True)
    return d


def format_kb_file(entries: list[KBEntry]) -> str:
    groups: "OrderedDict[str, list[KBEntry]]" = OrderedDict()
    for entry in entries:
        groups.setdefault(entry.category, []).append(entry)

    lines: list[str] = []
    for idx, (category, group_entries) in enumerate(groups.items(), start=1):
        lines.append(f"## KATEGORI {idx}: {category}\n")
        for entry in group_entries:
            lines.append(f"### {entry.id}: {entry.title}\n")
            lines.append("**Pertanyaan:**")
            for q in entry.questions:
                lines.append(f"- {q}")
            lines.append("")
            lines.append("**Jawaban:**")
            lines.append(entry.answer)
            lines.append("")
            lines.append(f"**Keywords:** {', '.join(entry.keywords)}")
            lines.append("")

    return "\n".join(lines)


def save_kb_file(filepath: str, entries: list[KBEntry]) -> None:
    backup_file(filepath)
    text = format_kb_file(entries)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)


def backup_file(filepath: str) -> str | None:
    if not os.path.isfile(filepath):
        return None

    backup_dir = _backup_dir(filepath)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    backup_path = os.path.join(backup_dir, f"{base_name}_{timestamp}.txt")
    shutil.copy2(filepath, backup_path)

    _prune_old_backups(backup_dir, base_name)
    return backup_path


def _prune_old_backups(backup_dir: str, base_name: str) -> None:
    files = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith(base_name) and f.endswith(".txt")],
        reverse=True,
    )
    for old_file in files[MAX_BACKUPS:]:
        try:
            os.remove(os.path.join(backup_dir, old_file))
        except OSError:
            pass


def list_backups(filepath: str) -> list[dict]:
    backup_dir = _backup_dir(filepath)
    base_name = os.path.splitext(os.path.basename(filepath))[0]

    files = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith(base_name) and f.endswith(".txt")],
        reverse=True,
    )

    result = []
    for f in files:
        full_path = os.path.join(backup_dir, f)
        mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
        result.append({
            "filename": f,
            "path": full_path,
            "waktu": mtime.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return result


def restore_backup(filepath: str, backup_path: str) -> None:
    backup_file(filepath)
    shutil.copy2(backup_path, filepath)


def next_kb_id(entries: list[KBEntry]) -> str:
    if not entries:
        return "KB-001"

    numbers = []
    width = 3
    for e in entries:
        m = re.match(r"KB-(\d+)", e.id)
        if m:
            numbers.append(int(m.group(1)))
            width = max(width, len(m.group(1)))

    next_num = (max(numbers) + 1) if numbers else 1
    return f"KB-{str(next_num).zfill(width)}"
