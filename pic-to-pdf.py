import os
import re
import io
import ctypes
from PIL import Image, ImageTk
import img2pdf
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# 启用高 DPI 感知，避免界面模糊（Windows）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

FONT = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_HEADER = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 10, "bold")
BG = "#f5f5f5"
FG = "#333333"
FG_SECONDARY = "#888888"
FG_LABEL = "#555555"
ACCENT = "#4a7eb5"
BORDER = "#dddddd"


class PDFCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片转PDF")
        self.root.geometry("820x660")
        self.root.minsize(920, 1080)
        self.root.configure(bg=BG)

        self.directory = ''
        self.files = []
        self.sort_by = tk.StringVar(value='按文件名称')
        self.sort_reverse = tk.BooleanVar(value=False)
        self.default_filename = "newfile.pdf"
        self.drag_data = {}

        # 配置 ttk 样式
        style = ttk.Style()
        style.theme_use("vista")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG, font=FONT)
        style.configure("TButton", font=FONT, padding=(14, 4))
        style.configure("Primary.TButton", font=FONT_BOLD)
        style.configure("TCheckbutton", background=BG, font=FONT)
        style.configure("TCombobox", font=FONT, padding=(4, 2))
        style.configure("Horizontal.TScale", background=BG)
        style.configure("StatusBar.TLabel", background="#e8e8e8", foreground=FG, font=FONT_SMALL)
        style.configure("Header.TLabel", font=FONT_HEADER, background=BG, foreground=FG)
        style.configure("Hint.TLabel", font=FONT_SMALL, background=BG, foreground=FG_SECONDARY)
        style.configure("Info.TLabel", font=FONT_SMALL, background=BG, foreground=FG_SECONDARY)

        # ---- 主布局 ----
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # ---- 左侧：文件列表 ----
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        list_header = ttk.Frame(left_frame)
        list_header.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(list_header, text="图片列表", style="Header.TLabel").pack(side=tk.LEFT)
        self.count_label = ttk.Label(list_header, text="0 张", style="Info.TLabel")
        self.count_label.pack(side=tk.LEFT, padx=(8, 0))

        self.listbox_frame = ttk.Frame(left_frame)
        self.listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.file_listbox = tk.Listbox(self.listbox_frame, selectmode=tk.SINGLE,
                                       activestyle="dotbox", font=FONT,
                                       relief="flat", bd=0, highlightthickness=1,
                                       highlightcolor=BORDER, highlightbackground=BORDER,
                                       bg="#ffffff", fg=FG, selectbackground="#d0e0f0",
                                       selectforeground=FG)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL,
                                  command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # 拖拽预览指示线
        self.drag_indicator = tk.Frame(self.listbox_frame, height=3, bg=ACCENT)
        self.drag_indicator.place_forget()

        ttk.Label(left_frame, text="拖拽行可调整顺序", style="Hint.TLabel").pack(anchor="w", pady=(4, 0))

        # ---- 右侧：控制面板 ----
        right_frame = ttk.Frame(main_frame, width=290)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        right_frame.pack_propagate(False)

        # ---- 预览 ----
        preview_header = ttk.Frame(right_frame)
        preview_header.pack(fill=tk.X)
        ttk.Label(preview_header, text="预览", style="Header.TLabel").pack(side=tk.LEFT)
        self.image_info_label = ttk.Label(preview_header, text="", style="Info.TLabel")
        self.image_info_label.pack(side=tk.RIGHT)

        self.preview_canvas = tk.Canvas(right_frame, width=270, height=220,
                                        bg="#ffffff", bd=0, highlightthickness=1,
                                        highlightcolor=BORDER, highlightbackground=BORDER)
        self.preview_canvas.pack(fill=tk.X, pady=(4, 10))

        # ---- 排序 ----
        ttk.Separator(right_frame, orient="horizontal").pack(fill=tk.X, pady=(0, 8))

        sort_row = ttk.Frame(right_frame)
        sort_row.pack(fill=tk.X)
        ttk.Label(sort_row, text="排序方式").pack(side=tk.LEFT)
        self.sort_dropdown = ttk.Combobox(sort_row, textvariable=self.sort_by,
                                          values=['按文件名称', '按修改时间'],
                                          state="readonly", width=20)
        self.sort_dropdown.pack(side=tk.RIGHT)
        self.sort_dropdown.bind("<<ComboboxSelected>>", self.sort_files)

        self.reverse_check = ttk.Checkbutton(right_frame, text="倒序排列",
                                              variable=self.sort_reverse,
                                              command=self.sort_files)
        self.reverse_check.pack(fill=tk.X, pady=(4, 0))

        # ---- 操作按钮 ----
        ttk.Separator(right_frame, orient="horizontal").pack(fill=tk.X, pady=(10, 10))

        ttk.Button(right_frame, text="选择文件夹", command=self.choose_directory).pack(fill=tk.X, pady=3)
        ttk.Button(right_frame, text="删除所选图片", command=self.delete_selected_image).pack(fill=tk.X, pady=3)
        ttk.Button(right_frame, text="清空列表", command=self.clear_all_images).pack(fill=tk.X, pady=3)

        self.generate_btn = ttk.Button(right_frame, text="生成 PDF",
                                       command=self.generate_pdf, style="Primary.TButton")
        self.generate_btn.pack(fill=tk.X, pady=(12, 8))

        # ---- 进度 ----
        self.progress_bar = ttk.Progressbar(right_frame, orient="horizontal",
                                            mode="determinate")
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(right_frame, text="", style="Info.TLabel")
        self.progress_label.pack(fill=tk.X)

        # ---- 状态栏 ----
        self.status_bar = ttk.Label(root, text="就绪 — 0 张图片", style="StatusBar.TLabel")
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipadx=10, ipady=3)

        # ---- 事件绑定 ----
        self.file_listbox.bind('<<ListboxSelect>>', self.on_select)
        self.file_listbox.bind('<B1-Motion>', self.on_drag_motion)
        self.file_listbox.bind('<ButtonPress-1>', self.on_drag_start)
        self.file_listbox.bind('<ButtonRelease-1>', self.on_drag_end)

    # ======================== 界面方法 ========================

    def update_count_and_status(self):
        count = len(self.files)
        self.count_label.config(text=f"{count} 张")
        self.status_bar.config(text=f"共 {count} 张图片" if count else "就绪 — 0 张图片")

    def choose_directory(self):
        self.directory = filedialog.askdirectory(title="选择包含图片的文件夹")
        if not self.directory:
            return
        self.load_images()

    def load_images(self):
        self.files = get_image_files(self.directory)
        self.sort_files()

    def sort_files(self, event=None):
        sort_by = self.sort_by.get()
        reverse = self.sort_reverse.get()
        if sort_by == '按修改时间':
            self.files.sort(key=lambda x: os.path.getmtime(
                os.path.join(self.directory, x)), reverse=reverse)
        else:
            self.files.sort(key=natural_key, reverse=reverse)
        self.display_files()

    def display_files(self):
        self.file_listbox.delete(0, tk.END)
        for file in self.files:
            self.file_listbox.insert(tk.END, file)
        self.update_count_and_status()

    def on_select(self, event):
        if not self.files:
            return
        selection = event.widget.curselection()
        if selection:
            self.show_preview(self.files[selection[0]])

    def show_preview(self, file):
        img_path = os.path.join(self.directory, file)
        try:
            img = Image.open(img_path)
            self.image_info_label.config(text=f"{img.width} x {img.height}")
            preview = img.copy()
            preview.thumbnail((270, 220), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(preview)
            self.preview_canvas.delete("all")
            cx, cy = 270 // 2, 220 // 2
            self.preview_canvas.create_image(cx, cy, image=img_tk, anchor=tk.CENTER)
            self.preview_canvas.image = img_tk
        except Exception:
            self.preview_canvas.delete("all")
            self.image_info_label.config(text="")

    def delete_selected_image(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一张图片")
            return
        del self.files[selection[0]]
        self.display_files()
        self.preview_canvas.delete("all")
        self.image_info_label.config(text="")

    def clear_all_images(self):
        if not self.files:
            return
        if messagebox.askokcancel("清空列表", "确定要清除所有图片吗？"):
            self.files.clear()
            self.display_files()
            self.preview_canvas.delete("all")
            self.image_info_label.config(text="")

    # ======================== 拖拽排序（含预览线） ========================

    def on_drag_start(self, event):
        widget = event.widget
        index = widget.nearest(event.y)
        if index < len(self.files):
            self.drag_data["source_index"] = index
            widget.selection_clear(0, tk.END)
            widget.selection_set(index)

    def on_drag_motion(self, event):
        if self.drag_data.get("source_index") is None:
            return
        widget = event.widget
        total = len(self.files)
        if total == 0:
            return
        index = max(0, min(widget.nearest(event.y), total - 1))
        bbox = widget.bbox(index)
        if bbox is None:
            self.drag_data["target_index"] = total
            self._place_indicator(widget, total)
            return
        if event.y < bbox[1] + bbox[3] / 2:
            target = index
        else:
            target = index + 1
        self.drag_data["target_index"] = target
        self._place_indicator(widget, target)
        widget.see(index)

    def on_drag_end(self, event):
        self.drag_indicator.place_forget()
        source = self.drag_data.get("source_index")
        target = self.drag_data.get("target_index")
        if source is None or target is None or source == target or source == target - 1:
            self.drag_data.clear()
            return
        if target > source:
            target -= 1
        file = self.files.pop(source)
        self.files.insert(target, file)
        self.display_files()
        self.drag_data.clear()

    def _place_indicator(self, widget, target_index):
        total = len(self.files)
        if target_index >= total:
            if total > 0:
                last_bbox = widget.bbox(tk.END)
                y = last_bbox[1] + last_bbox[3] if last_bbox else 0
            else:
                y = 0
        elif target_index <= 0:
            first_bbox = widget.bbox(0)
            y = first_bbox[1] if first_bbox else 0
        else:
            item_bbox = widget.bbox(target_index)
            y = item_bbox[1] if item_bbox else 0
        self.drag_indicator.place(x=2, y=y, width=widget.winfo_width() - 4, height=3)
        self.drag_indicator.lift()

    # ======================== PDF 生成 ========================

    def generate_pdf(self):
        if not self.files:
            messagebox.showwarning("提示", "没有可转换的图片")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=self.default_filename,
            title="保存PDF文件"
        )
        if not save_path:
            return
        self.generate_btn.config(state=tk.DISABLED, text="正在生成...")
        self.progress_bar['value'] = 0
        self.root.update_idletasks()
        success = create_pdf(self.files, self.directory, save_path,
                             self.progress_bar, self.progress_label)
        self.generate_btn.config(state=tk.NORMAL, text="生成 PDF")
        self.progress_label.config(text="")
        if success:
            opendir = messagebox.askyesno("完成",
                                          f"PDF 已成功生成\n{save_path}\n\n是否打开所在文件夹？")
            if opendir:
                os.startfile(os.path.dirname(save_path))


# ======================== 工具函数 ========================

def natural_key(text):
    """自然数排序键：将 'img10.jpg' 拆分为 ['img', 10, '.jpg']，
    使得排序结果为 1, 2, 10 而非 1, 10, 2。"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]


def get_image_files(directory):
    extensions = ('png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp', 'tiff', 'tif')
    return sorted([f for f in os.listdir(directory)
                   if f.lower().endswith(extensions)], key=natural_key)


def create_pdf(files, directory, output_path, progress_bar, progress_label):
    images = []
    try:
        for i, file in enumerate(files):
            progress_label.config(text=f"处理中: {file}")
            img_path = os.path.join(directory, file)
            try:
                img = Image.open(img_path)
                if img.mode == 'RGBA':
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)
            except Exception as e:
                messagebox.showerror("错误", f"无法处理文件: {file}\n{e}")
                continue
            progress_bar['value'] = i + 1
            progress_bar.update_idletasks()
        if not images:
            messagebox.showerror("错误", "没有可处理的图片")
            return False
        progress_label.config(text="正在写入 PDF...")
        # 使用 img2pdf 替代 Pillow 内置的 PDF 保存，
        # 避免 Pillow 对 RGB 图像强制 JPEG 编码（DCTDecode）导致的问题
        image_bytes = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            image_bytes.append(buf.getvalue())
        with open(output_path, 'wb') as f:
            f.write(img2pdf.convert(image_bytes))
        return True
    except Exception as e:
        messagebox.showerror("错误", f"PDF 生成失败:\n{e}")
        return False


if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.tk.call('tk', 'scaling', root.winfo_fpixels('1i') / 72)
    except Exception:
        pass
    app = PDFCreatorApp(root)
    root.mainloop()
