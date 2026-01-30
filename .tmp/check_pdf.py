from pypdf import PdfReader
import os
root = os.path.join('.', '.tmp', 'portfolio_extracted')
targets = ['portfolio_combined.pdf','portfolio_combined_with_legend.pdf','legend_page.pdf']
for name in targets:
    found = None
    for dirpath,_,files in os.walk(root):
        if name in files:
            found = os.path.join(dirpath,name)
            break
    if not found:
        print(f'MISSING::{name}')
        continue
    try:
        r = PdfReader(found)
        n = len(r.pages)
        text0 = r.pages[0].extract_text() or ''
        sample = ' '.join(text0.split())[:400]
        print(f'FILE::{name}::PATH::{found}::PAGES::{n}::SAMPLE::{sample}')
    except Exception as e:
        print(f'ERR::{name}::{e}')
