import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, Button, Label, Frame, ttk

class PDFCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片转PDF")
        self.root.geometry("750x600")
        self.root.configure(bg="#f0f0f0")
        self.directory = ''
        self.files = []
        self.sort_by = tk.StringVar(value='name')
        self.default_filename = "newfile.pdf"

        # 文件列表框
        self.listbox_frame = Frame(root)
        self.listbox_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.file_listbox = Listbox(self.listbox_frame, selectmode=tk.SINGLE, width=60, activestyle="dotbox", font=("Arial", 10))
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条
        self.scrollbar = Scrollbar(self.listbox_frame, orient=tk.VERTICAL)
        self.scrollbar.config(command=self.file_listbox.yview)
        self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=self.scrollbar.set)

        # 控件区域
        self.control_frame = Frame(root, bg="#f0f0f0")
        self.control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 预览标签
        self.preview_label = Label(self.control_frame, text="图片预览", font=("Arial", 12), bg="#f0f0f0")
        self.preview_label.pack()

        # 预览窗口
        self.preview_canvas = tk.Canvas(self.control_frame, width=300, height=300, bg="#ffffff", relief="ridge", bd=2)
        self.preview_canvas.pack(pady=10)

        # 下拉菜单
        self.sort_label = Label(self.control_frame, text="排序方式:", font=("Arial", 10), bg="#f0f0f0")
        self.sort_label.pack(pady=5)
        self.sort_dropdown = ttk.Combobox(self.control_frame, textvariable=self.sort_by, values=['name', 'time'], state="readonly")
        self.sort_dropdown.pack(pady=5)
        self.sort_dropdown.bind("<<ComboboxSelected>>", self.sort_files)

        # 按钮
        Button(self.control_frame, text="选择文件夹", command=self.choose_directory, font=("Arial", 10), relief="groove").pack(pady=5)
        Button(self.control_frame, text="删除所选图片", command=self.delete_selected_image, font=("Arial", 10), relief="groove").pack(pady=5)
        Button(self.control_frame, text="清除所有图片", command=self.clear_all_images, font=("Arial", 10), relief="groove").pack(pady=5)
        Button(self.control_frame, text="生成PDF", command=self.generate_pdf, font=("Arial", 10), relief="groove").pack(pady=5)

        self.file_listbox.bind('<<ListboxSelect>>', self.on_select)
        self.file_listbox.bind('<B1-Motion>', self.drag)
        self.file_listbox.bind('<ButtonRelease-1>', self.drop)

        # 拖动数据
        self.drag_data = {"index": None}

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
        if sort_by == 'time':
            self.files.sort(key=lambda x: os.path.getmtime(os.path.join(self.directory, x)))
        else:
            self.files.sort()
        self.display_files()

    def display_files(self):
        self.file_listbox.delete(0, tk.END)
        for file in self.files:
            self.file_listbox.insert(tk.END, file)

    def on_select(self, event):
        if not self.files:
            return
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            selected_file = self.files[index]
            self.show_preview(selected_file)

    def show_preview(self, file):
        img_path = os.path.join(self.directory, file)
        img = Image.open(img_path)
        img.thumbnail((300, 300))
        img_tk = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(150, 150, image=img_tk, anchor=tk.CENTER)
        self.preview_canvas.image = img_tk  # 保持引用避免被垃圾回收

    def delete_selected_image(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "未选择图片")
            return
        index = selection[0]
        del self.files[index]
        self.display_files()
        self.preview_canvas.delete("all")

    def clear_all_images(self):
        if messagebox.askokcancel("清除所有图片", "确定要清除所有图片吗？"):
            self.files.clear()
            self.display_files()
            self.preview_canvas.delete("all")

    def drag(self, event):
        widget = event.widget
        index = widget.nearest(event.y)

        if self.drag_data["index"] is None:
            self.drag_data["index"] = index

        if index < len(self.files):
            widget.selection_clear(0, tk.END)
            widget.selection_set(index)

    def drop(self, event):
        if self.drag_data["index"] is None:
            return

        widget = event.widget
        drop_index = widget.nearest(event.y)

        if drop_index != self.drag_data["index"]:
            file = self.files.pop(self.drag_data["index"])
            self.files.insert(drop_index, file)
            self.display_files()

        self.drag_data["index"] = None

    def generate_pdf(self):
        if not self.files:
            messagebox.showwarning("警告", "没有图片生成PDF")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], initialfile=self.default_filename, title="选择保存地址和文件名")
        if not save_path:
            messagebox.showwarning("警告", "未选择保存位置，操作已取消")
            return

        create_pdf(self.files, self.directory, save_path)
        messagebox.showinfo("完成", f"PDF已生成: {save_path}")

def get_image_files(directory):
    return [f for f in os.listdir(directory) if f.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif'))]

def create_pdf(files, directory, output_path):
    images = []
    for file in files:
        img_path = os.path.join(directory, file)
        img = Image.open(img_path)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        images.append(img)
    
    images[0].save(output_path, save_all=True, append_images=images[1:])
    print(f"PDF已生成: {output_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFCreatorApp(root)
    root.mainloop()
