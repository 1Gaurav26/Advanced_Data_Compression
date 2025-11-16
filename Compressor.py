import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
import json
import lzma

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_OK = True
except ImportError:
    DND_OK = False

JUNK_SUBSTRINGS = [
    "Messages and calls are end-to-end encrypted",
    "Only people in this chat can read, listen to, or share them",
    "This message was deleted",
]

CHAT_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2})\s*[\u202f ]?(am|pm|AM|PM)\s*-\s*(.*?):\s*(.*)$"
)

def normalize_line(s):
    return s.replace("\u202f", " ").replace("\u00a0", " ").strip()

def is_junk(msg):
    return any(j.lower() in msg.lower() for j in JUNK_SUBSTRINGS)

def format_chat(content):
    lines = content.splitlines()
    result = []
    current_date = None
    for line in lines:
        line = normalize_line(line)
        m = CHAT_PATTERN.match(line)
        if m:
            date, time, ampm, user, msg = m.groups()
            if is_junk(msg): continue
            if date != current_date:
                result.append({"date": date, "msgs": []})
                current_date = date
            result[-1]["msgs"].append({
                "time": f"{time} {ampm.lower()}",
                "user": user,
                "msg": msg
            })
        else:
            if result and result[-1]["msgs"]:
                result[-1]["msgs"][-1]["msg"] += " " + line
    return result

def motif_encode(chat_graph):
    motif_dict = {}
    motif_counter = 1
    encoded_graph = []
    for entry in chat_graph:
        date = entry["date"]
        date_msgs = []
        for m in entry["msgs"]:
            key = f"{m['user']}|||{m['msg']}"
            if key not in motif_dict:
                motif_dict[key] = f"$P{motif_counter}$"
                motif_counter += 1
            date_msgs.append({
                "time": m["time"],
                "user": m["user"],
                "pattern": motif_dict[key]
            })
        encoded_graph.append({"date": date, "msgs": date_msgs})
    return encoded_graph, motif_dict

def serialize_and_compress(graph, motif_dict):
    data = {"graph": graph, "dictionary": motif_dict}
    json_bytes = json.dumps(data, separators=(',',':')).encode("utf-8")
    return lzma.compress(json_bytes)

def compress_plain(content):
    return lzma.compress(content.encode("utf-8"))

def main_handle(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    chat_graph = format_chat(content)
    encoded_graph, motif_dict = motif_encode(chat_graph)
    motif_count = len(motif_dict)
    chat_count = sum(len(e['msgs']) for e in encoded_graph)

    # Smart auto-detect for repetition
    if motif_count > 0.9 * chat_count:
        print("Low repetition detected. Using plain text LZMA compression.")
        compressed = compress_plain(content)
        used_mode = "plain_lzma"
    else:
        compressed = serialize_and_compress(encoded_graph, motif_dict)
        used_mode = "motif_lzma"

    out_file = os.path.join(os.path.dirname(file_path), f"glampress_{used_mode}_compressed.lzma")
    with open(out_file, "wb") as f:
        f.write(compressed)

    actual_size = os.path.getsize(out_file)
    original_size = len(content.encode('utf-8'))
    saved_percent = (1 - actual_size / original_size) * 100 if original_size else 0

    msg = (f"GLaMpress {used_mode.replace('_','+').upper()} compression complete:\n{out_file}\n\n"
           f"Original size: {original_size} bytes\n"
           f"Compressed size: {actual_size} bytes\n"
           f"Space saved after compression: {saved_percent:.2f}%")
    messagebox.showinfo("Compression Result", msg)
    print(msg)

def main():
    if DND_OK:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    root.title("GLaMpress Optimized Compressor")
    root.geometry("500x300")
    label = tk.Label(root, text="Drag & Drop large chat .txt here\n(or click to select)", pady=40, relief="solid")
    label.pack(expand=True, fill="both", padx=20, pady=20)
    def on_drop(event):
        file_path = event.data.strip('{}')
        if os.path.isfile(file_path):
            main_handle(file_path)
    def on_click(event):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            main_handle(file_path)
    if DND_OK:
        label.drop_target_register(DND_FILES)
        label.dnd_bind("<<Drop>>", on_drop)
    label.bind("<Button-1>", on_click)
    root.mainloop()

if __name__ == "__main__":
    main()