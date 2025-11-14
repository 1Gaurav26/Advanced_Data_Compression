import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import lzma
import json
import threading

def decompress_file(file_path):
    try:
        with open(file_path, "rb") as f:
            compressed = f.read()
        json_bytes = lzma.decompress(compressed)
        try:
            # Try motif decoding (dictionary+graph)
            pack = json.loads(json_bytes.decode("utf-8"))
            if "graph" in pack and "dictionary" in pack:
                graph, motif_dict = pack["graph"], pack["dictionary"]
                rev_dict = {v: k for k, v in motif_dict.items()}
                reconstructed = []
                for entry in graph:
                    date = entry["date"]
                    for m in entry["msgs"]:
                        key = rev_dict.get(m["pattern"], "UNKNOWN|||")
                        if "|||" in key:
                            user, msg = key.split('|||', 1)
                        else:
                            user, msg = "UNKNOWN", key
                        reconstructed.append(f"{date} {m['time']} {user}: {msg}")
                output_path = file_path.replace(".lzma", "_motif_restored.txt")
                with open(output_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write("\n".join(reconstructed))
                print(f"Restored motif file saved at {output_path}")
                return output_path
            else:
                raise Exception("Motif fields not found")
        except Exception:
            # Fallback: plain text compression
            plain_text = json_bytes.decode("utf-8")
            output_path = file_path.replace(".lzma", "_plain_restored.txt")
            with open(output_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(plain_text)
            print(f"Restored plain text file saved at {output_path}")
            return output_path
    except Exception as e:
        print(f"Error during decompression: {e}")
        return None

def drop(event):
    file_path = event.data.strip('{}')
    label.config(text="Decompressing... please wait.")
    def work():
        output_file = decompress_file(file_path)
        if output_file:
            label.after(0, lambda: label.config(text=f"Decompressed file saved at:\n{output_file}"))
        else:
            label.after(0, lambda: label.config(text="Decompression failed. See console for error."))
    threading.Thread(target=work, daemon=True).start()

root = TkinterDnD.Tk()
root.title("GLaMpress Optimized Decompressor")
root.geometry("500x300")
label = tk.Label(root, text="Drag & Drop GLaMpress .lzma file here", width=50, height=10, bg='lightblue')
label.pack(padx=20, pady=20)
label.drop_target_register(DND_FILES)
label.dnd_bind("<<Drop>>", drop)

root.mainloop()

