import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from pypdf import PdfReader, PdfWriter


def parse_pages(text, total):
    """'1,3,5-7' 형태의 문자열을 [1, 3, 5, 6, 7] 리스트로 변환 (입력 순서 유지)"""
    text = re.sub(r"\s+", "", text)  # 모든 공백 제거
    if not text:
        raise ValueError("페이지 번호를 입력하세요.")

    if not re.fullmatch(r"[0-9,\-]+", text):
        raise ValueError("페이지 번호에는 숫자, 쉼표(,), 대시(-)만 사용할 수 있습니다.")

    pages = []
    for part in text.split(","):
        if part == "":
            raise ValueError("쉼표가 연속되었거나 맨 앞/뒤에 있습니다.")

        if "-" in part:
            pieces = part.split("-")
            if len(pieces) != 2 or pieces[0] == "" or pieces[1] == "":
                raise ValueError(f"잘못된 범위 형식입니다: '{part}'")
            start, end = int(pieces[0]), int(pieces[1])
            if start > end:
                raise ValueError(f"범위의 시작이 끝보다 큽니다: '{part}'")
            nums = range(start, end + 1)
        else:
            nums = [int(part)]

        for n in nums:
            if n < 1 or n > total:
                raise ValueError(f"{n}쪽은 범위를 벗어났습니다. (이 PDF는 1~{total}쪽)")
            pages.append(n)

    return pages


def extract_pages(pdf_path, page_text):
    """선택한 페이지만 합쳐서 '파일명_RE.pdf'로 저장하고 (저장경로, 페이지수) 반환"""
    reader = PdfReader(pdf_path)
    pages = parse_pages(page_text, len(reader.pages))

    writer = PdfWriter()
    for n in pages:
        writer.add_page(reader.pages[n - 1])  # 사용자 번호는 1부터, 리스트는 0부터

    base_dir = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    out_path = os.path.join(base_dir, f"{base_name}_RE.pdf")

    with open(out_path, "wb") as f:
        writer.write(f)

    return out_path, len(pages)


def run():
    path = path_entry.get().strip().strip('"')  # 경로 복사 시 붙는 따옴표 제거
    page_text = page_entry.get()

    # 1) 사전 차단: 확장자가 .pdf가 아니면 즉시 중단
    if not path.lower().endswith(".pdf"):
        messagebox.showerror("차단", "PDF 파일(.pdf)만 처리할 수 있습니다.")
        return

    # 2) 파일 존재 여부
    if not os.path.isfile(path):
        messagebox.showerror("오류", f"파일을 찾을 수 없습니다:\n{path}")
        return

    # 3) 실행
    try:
        out_path, count = extract_pages(path, page_text)
        messagebox.showinfo("완료", f"{count}페이지를 합쳐서 저장했습니다.\n\n{out_path}")
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
root.title("PDF 페이지 추출기")
root.geometry("460x210")

tk.Label(root, text="PDF 파일 경로:").pack(pady=(12, 2))
frame = tk.Frame(root)
frame.pack()
path_entry = tk.Entry(frame, width=42)
path_entry.pack(side="left", padx=4)
tk.Button(frame, text="찾아보기", command=browse).pack(side="left")

tk.Label(root, text="페이지 번호 (예: 1,3,5-7):").pack(pady=(12, 2))
page_entry = tk.Entry(root, width=48)
page_entry.pack()

tk.Button(root, text="추출 시작", command=run).pack(pady=14)

root.mainloop()