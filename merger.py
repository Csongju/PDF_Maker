import os
import tkinter as tk
from tkinter import filedialog, messagebox
from pypdf import PdfReader, PdfWriter

file_list = []  # 합칠 PDF의 전체 경로를 순서대로 저장


def refresh_listbox(select_index=None):
    """file_list 내용을 목록 창에 다시 그림"""
    listbox.delete(0, tk.END)
    for i, p in enumerate(file_list, start=1):
        listbox.insert(tk.END, f"{i}. {p}")
    if select_index is not None and 0 <= select_index < len(file_list):
        listbox.selection_set(select_index)


def add_files():
    paths = filedialog.askopenfilenames(filetypes=[("PDF 파일", "*.pdf")])
    for p in paths:
        # PDF만 허용, 이미 있는 파일은 중복 추가하지 않음
        if p.lower().endswith(".pdf") and p not in file_list:
            file_list.append(p)
    refresh_listbox()


def remove_selected():
    sel = listbox.curselection()
    if not sel:
        return
    del file_list[sel[0]]
    refresh_listbox(min(sel[0], len(file_list) - 1))


def move_up():
    sel = listbox.curselection()
    if not sel or sel[0] == 0:
        return
    i = sel[0]
    file_list[i - 1], file_list[i] = file_list[i], file_list[i - 1]
    refresh_listbox(i - 1)


def move_down():
    sel = listbox.curselection()
    if not sel or sel[0] == len(file_list) - 1:
        return
    i = sel[0]
    file_list[i + 1], file_list[i] = file_list[i], file_list[i + 1]
    refresh_listbox(i + 1)


def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder)


def merge_pdfs():
    name = name_entry.get().strip()
    folder = folder_entry.get().strip().strip('"')

    # 1) 입력 검사
    if not file_list:
        messagebox.showwarning("입력 오류", "합칠 PDF를 추가하세요.")
        return
    if not name:
        messagebox.showwarning("입력 오류", "저장할 PDF 이름을 입력하세요.")
        return
    if not folder or not os.path.isdir(folder):
        messagebox.showwarning("입력 오류", "저장할 폴더 경로가 올바르지 않습니다.")
        return

    # 2) 이름 처리: .pdf가 없으면 붙이고, 파일명에 쓸 수 없는 문자 차단
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    if any(c in name for c in '\\/:*?"<>|'):
        messagebox.showwarning("입력 오류", '파일명에는 \\ / : * ? " < > | 문자를 쓸 수 없습니다.')
        return

    out_path = os.path.join(folder, name)

    # 3) 덮어쓰기 확인
    if os.path.exists(out_path):
        if not messagebox.askyesno("덮어쓰기", f"이미 같은 이름의 파일이 있습니다.\n덮어쓸까요?\n\n{out_path}"):
            return

    # 4) 합치기
    try:
        writer = PdfWriter()
        total_pages = 0
        for p in file_list:
            if not os.path.isfile(p):
                raise FileNotFoundError(f"파일을 찾을 수 없습니다:\n{p}")
            reader = PdfReader(p)
            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1

        with open(out_path, "wb") as f:
            writer.write(f)

        messagebox.showinfo(
            "완료",
            f"PDF {len(file_list)}개, 총 {total_pages}쪽을 합쳤습니다.\n\n{out_path}",
        )
    except Exception as e:
        messagebox.showerror("오류", str(e))


root = tk.Tk()
root.title("PDF 합치기")
root.geometry("640x520")

# --- 1. 합칠 PDF 목록 ---
tk.Label(root, text="1. 합칠 PDF 목록 (위에서 아래 순서대로 합쳐짐)").pack(pady=(12, 2))

list_frame = tk.Frame(root)
list_frame.pack(fill="both", expand=True, padx=12)

scroll = tk.Scrollbar(list_frame)
scroll.pack(side="right", fill="y")
listbox = tk.Listbox(list_frame, height=10, yscrollcommand=scroll.set, selectmode=tk.SINGLE)
listbox.pack(side="left", fill="both", expand=True)
scroll.config(command=listbox.yview)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=6)
tk.Button(btn_frame, text="찾아보기(추가)", command=add_files).pack(side="left", padx=3)
tk.Button(btn_frame, text="▲ 위로", command=move_up).pack(side="left", padx=3)
tk.Button(btn_frame, text="▼ 아래로", command=move_down).pack(side="left", padx=3)
tk.Button(btn_frame, text="선택 삭제", command=remove_selected).pack(side="left", padx=3)

# --- 2. 저장할 PDF 이름 ---
tk.Label(root, text="2. 합쳐서 나올 PDF 이름 (예: 합본  →  합본.pdf)").pack(pady=(10, 2))
name_entry = tk.Entry(root, width=60)
name_entry.pack()

# --- 3. 저장 경로 ---
tk.Label(root, text="3. 저장할 폴더 경로").pack(pady=(10, 2))
folder_frame = tk.Frame(root)
folder_frame.pack()
folder_entry = tk.Entry(folder_frame, width=52)
folder_entry.pack(side="left", padx=4)
tk.Button(folder_frame, text="폴더 선택", command=browse_folder).pack(side="left")

tk.Button(root, text="합치기 시작", command=merge_pdfs, height=2, width=20).pack(pady=16)

root.mainloop()