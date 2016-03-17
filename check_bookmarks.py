import subprocess, os, traceback, sys, shutil, PyPDF2, string
from PyPDF2 import PdfFileWriter, PdfFileReader

exclude = ['Cover', 'Title Page', 'Copyright Page', 'Contents']
PDF = '/Users/drlulz/Downloads/AnkiFlash-master/Pathophysiology of Disease Flashcards.pdf'

def page_id_to_num(pdf, pages=None, _result=None, _num_pages=None):

    if _result is None:
        _result = {}
        
    if pages is None:
        _num_pages = []
        pages = pdf.trailer["/Root"].getObject()["/Pages"].getObject()


    t = pages["/Type"]

    if t == "/Pages":
        for page in pages["/Kids"]:
            _result[page.idnum] = len(_num_pages)
            page_id_to_num(pdf, page.getObject(), _result, _num_pages)

    elif t == "/Page":
        _num_pages.append(1)

    return _result
    

def bookmarks(outlines, pg_id_num_map, result=None):

    if result is None:
        result = []

    if type(outlines) == list:
        for outline in outlines:
            result = bookmarks(outline, pg_id_num_map, result)

    elif type(outlines) == PyPDF2.pdf.Destination:
        result.append((pg_id_num_map[outlines.page.idnum]+1, outlines['/Title']))

    return result
    

PDF_IN = PdfFileReader(open(PDF, 'rb'))
pg_id_num_map = page_id_to_num(PDF_IN)

outlines = PDF_IN.getOutlines()
outlines = [item for item in outlines if not type(item) == list]
outlines = [item for item in outlines if not item['/Title'] in exclude]

bmrks = bookmarks(outlines, pg_id_num_map)
it = iter(bmrks[1:])

TOC = []

for x in bmrks:
    try:
        TOC.append( (x[0], (next(it)[0] - 1), x[1]) )
    except:
        pass
        
print TOC
