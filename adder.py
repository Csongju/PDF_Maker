import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from pypdf import PdfReader, PdfWriter


def parse_blanks(text, total):
    """
    '1-3(7),5' 형태의 문자열을 {페이지번호: 뒤에 넣을 빈 페이지 수} 딕셔너리로 변환
    괄호가 없으면 빈 페이지 1장
    """
    text = re.sub(r"\s+", "", text)  # 모든 공백 제거
    if not text:
        raise ValueError("페이지 번호를 입력하세요.")

    if not re.fullmatch(r"[0-9,\-()]+", text):
        raise ValueError("숫자, 쉼표(,), 대시(-), 괄호()만 사용할 수 있습니다.")

    blanks = {}
    for part in text.split(","):
        if part == "":
            raise ValueError("쉼표가 연속되었거나 맨 앞/뒤에 있습니다.")

        m = re.fullmatch(r"(\d+)(?:-(\d+))?(?:\((\d+)\))?", part)
        if not m:
            raise ValueError(f"잘못된 형식입니다: '{part}'")

        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        count = int(m.group(3)) if m.group(3) else 1

        if start > end:
            raise ValueError(f"범위의 시작이 끝보다 큽니다: '{part}'")
        if start < 1 or end > total:
            raise ValueError(f"'{part}'는 범위를 벗어났습니다. (이 PDF는 1~{total}쪽)")

        for n in range(start, end + 1):
            blanks[n] = count  # 같은 페이지를 또 지정하면 마지막 지정이 적용됨

    return blanks


def insert_blanks(pdf_path, page_text):
    """지정한 페이지 뒤에 빈 페이지를 넣어 '파일명_Blank.pdf'로 저장"""
    reader = PdfReader(pdf_path)
    total = len(reader.pages)
    blanks = parse_blanks(page_text, total)

    writer = PdfWriter()
    for i, page in enumerate(reader.pages, start=1):
        writer.add_page(page)

        # 이 페이지 뒤에 빈 페이지가 필요하면, 이 페이지와 같은 크기로 추가
        for _ in range(blanks.get(i, 0)):
            writer.add_blank_page(
                width=float(page.mediabox.width),
                height=float(page.mediabox.height),
            )

    base_dir = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    out_path = os.path.join(base_dir, f"{base_name}_Blank.pdf")

    with open(out_path, "wb") as f:
        writer.write(f)

    added = sum(blanks.values())
    return out_path, total, added


def run():
    path = path_entry.get().strip().strip('"')
    page_text = page_entry.get()

    if not path.lower().endswith(".pdf"):
        messagebox.showerror("차단", "PDF 파일(.pdf)만 처리할 수 있습니다.")
        return

    if not os.path.isfile(path):
        messagebox.showerror("오류", f"파일을 찾을 수 없습니다:\n{path}")
        return

    try:
        out_path, total, added = insert_blanks(path, page_text)
        messagebox.showinfo(
            "완료",
            f"원본 {total}쪽 + 빈 페이지 {added}장 = 총 {total + added}쪽\n\n{out_path}",
        )
    except ValueError as e:
        messagebox.showwarning("입력 오류", str(e))
    except Exception as e:
        messagebox.showerror("오류", str(e))


def browse():
    path = filedialog.askopenfilename(filetypes=[("PDF 파일", "*.pdf")])
    if path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, path)


root = tk.Tk()
root.title("PDF 빈 페이지 삽입기")
root.geometry("460x230")

tk.Label(root, text="PDF 파일 경로:").pack(pady=(12, 2))
frame = tk.Frame(root)
frame.pack()
path_entry = tk.Entry(frame, width=42)
path_entry.pack(side="left", padx=4)
tk.Button(frame, text="찾아보기", command=browse).pack(side="left")

tk.Label(root, text="빈 페이지를 넣을 쪽 (예: 1-3(7),5(2)):").pack(pady=(12, 2))
page_entry = tk.Entry(root, width=48)
page_entry.pack()

tk.Button(root, text="삽입 시작", command=run).pack(pady=14)

root.mainloop()