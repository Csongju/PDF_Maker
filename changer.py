import os
import tkinter as tk
from tkinter import filedialog, messagebox

import win32com.client
import pythoncom

WORD_EXT = (".doc", ".docx")
PPT_EXT = (".ppt", ".pptx")


def find_targets(folder):
    """폴더 안(하위 폴더 제외)의 Word/PPT 파일 목록 반환. 임시파일(~$...)은 제외"""
    word_files, ppt_files = [], []
    for name in sorted(os.listdir(folder)):
        full = os.path.join(folder, name)
        if not os.path.isfile(full) or name.startswith("~$"):
            continue
        low = name.lower()
        if low.endswith(WORD_EXT):
            word_files.append(full)
        elif low.endswith(PPT_EXT):
            ppt_files.append(full)
    return word_files, ppt_files


def convert_word(word_files, results):
    if not word_files:
        return
    app = win32com.client.DispatchEx("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0
    try:
        for src in word_files:
            out = os.path.splitext(src)[0] + ".pdf"
            doc = None
            try:
                doc = app.Documents.Open(os.path.abspath(src), ReadOnly=True)
                doc.ExportAsFixedFormat(os.path.abspath(out), 17)  # 17 = PDF
                results.append((src, True, ""))
            except Exception as e:
                results.append((src, False, str(e)))
            finally:
                if doc is not None:
                    doc.Close(False)
    finally:
        app.Quit()


def convert_ppt(ppt_files, results):
    if not ppt_files:
        return
    app = win32com.client.DispatchEx("PowerPoint.Application")
    try:
        for src in ppt_files:
            out = os.path.splitext(src)[0] + ".pdf"
            pres = None
            try:
                # ReadOnly=True, Untitled=False, WithWindow=False
                pres = app.Presentations.Open(os.path.abspath(src), True, False, False)
                pres.SaveAs(os.path.abspath(out), 32)  # 32 = PDF
                results.append((src, True, ""))
            except Exception as e:
                results.append((src, False, str(e)))
            finally:
                if pres is not None:
                    pres.Close()
    finally:
        app.Quit()


def run():
    folder = folder_entry.get().strip().strip('"')

    if not folder or not os.path.isdir(folder):
        messagebox.showwarning("입력 오류", "폴더 경로가 올바르지 않습니다.")
        return

    word_files, ppt_files = find_targets(folder)
    if not word_files and not ppt_files:
        messagebox.showinfo("알림", "이 폴더에는 Word/PPT 파일이 없습니다.")
        return

    # 같은 이름의 PDF가 이미 있으면 덮어쓰기 확인
    existing = [
        f for f in word_files + ppt_files
        if os.path.exists(os.path.splitext(f)[0] + ".pdf")
    ]
    if existing:
        if not messagebox.askyesno(
            "덮어쓰기",
            f"같은 이름의 PDF가 이미 있는 파일이 {len(existing)}개 있습니다.\n덮어쓸까요?",
        ):
            return

    status.config(text="변환 중... 잠시만 기다려 주세요.")
    root.update()

    results = []
    pythoncom.CoInitialize()
    try:
        convert_word(word_files, results)
        convert_ppt(ppt_files, results)
    except Exception as e:
        messagebox.showerror(
            "오류",
            f"Office 실행에 실패했습니다. Word/PowerPoint가 설치되어 있는지 확인하세요.\n\n{e}",
        )
        status.config(text="")
        return
    finally:
        pythoncom.CoUninitialize()

    ok = [r for r in results if r[1]]
    fail = [r for r in results if not r[1]]

    msg = f"성공 {len(ok)}개 / 실패 {len(fail)}개"
    if fail:
        msg += "\n\n[실패한 파일]\n" + "\n".join(
            f"- {os.path.basename(s)}: {err}" for s, _, err in fail
        )
    status.config(text="")
    messagebox.showinfo("완료", msg)


def browse():
    folder = filedialog.askdirectory()
    if folder:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder)


root = tk.Tk()
root.title("Word/PPT → PDF 변환기")
root.geometry("480x180")

tk.Label(root, text="변환할 폴더 경로:").pack(pady=(14, 2))
frame = tk.Frame(root)
frame.pack()
folder_entry = tk.Entry(frame, width=44)
folder_entry.pack(side="left", padx=4)
tk.Button(frame, text="폴더 선택", command=browse).pack(side="left")

tk.Button(root, text="변환 시작", command=run, width=16, height=2).pack(pady=12)
status = tk.Label(root, text="")
status.pack()

root.mainloop()