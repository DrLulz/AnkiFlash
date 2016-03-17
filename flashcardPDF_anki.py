#!/usr/local/bin/python
# encoding: utf-8

####################################################################
# DrLulz Aug-2015
# Dependencies = PyPDF2, Anki, Ghostscript
# All paths are OS X


import subprocess, os, traceback, sys, shutil, PyPDF2, string
from PyPDF2 import PdfFileWriter, PdfFileReader
from anki import Collection as aopen

####################################################################
# OPTIONS & SETUP --------------------------------------------------

# Ghostscript path, if in PATH set to "gs"
GHOSTSCRIPTCMD = "/usr/local/bin/gs"

TMP_DIR = '/tmp/flashcards/'

# Full path to pdf to be processed
PDF_DIR = '/Users/drlulz/Desktop/tmp/Medical_Dx_Tx_Flashcards.pdf'

# Start and End page
start   = '12'
end     = '15'

# Path to your Anki collection
aPATH       = "/Users/drlulz/Documents/Anki/drlulz/collection.anki2"

# Name for new Anki deck
DECK_NAME   = 'Medical Dx Tx'

####################################################################

def group(lst, n):
    for i in range(0, len(lst), n):
        val = lst[i:i+n]
        if len(val) == n:
            yield tuple(val)


# ------------------------------------------------------------------
# ------------------------------------------------------------------
# Create new Anki theme geared towards pdf flashcards

def flash_theme(name, mm):
    abspath = os.path.abspath(__file__)
    
    path  = os.path.dirname(abspath) + '/template'
    f = path + '/front.txt'
    c = path + '/css.txt'
    b = path + '/back.txt'

    with open(f, 'r') as ft, open(c, 'r') as ct, open (b, 'r') as bt:
        ftemp = ft.read()
        css   = ct.read()
        btemp = bt.read()

    m  = mm.new(name)

    fld = mm.newField('Note ID'); mm.addField(m, fld)
    fld = mm.newField('Front');   mm.addField(m, fld)
    fld = mm.newField('F Note');  mm.addField(m, fld)
    fld = mm.newField('Back');    mm.addField(m, fld)
    fld = mm.newField('B Note');  mm.addField(m, fld)
    fld = mm.newField('class');   mm.addField(m, fld)
    fld = mm.newField('Noty');    mm.addField(m, fld)
    fld = mm.newField('http');    mm.addField(m, fld)
    fld = mm.newField('video');   mm.addField(m, fld)

    m['css'] = css

    t = mm.newTemplate('Card 1')
    t['qfmt'] = ftemp
    t['afmt'] = btemp
    mm.addTemplate(m, t)
    
    mm.add(m)
    return m


# ------------------------------------------------------------------
# ------------------------------------------------------------------
# Make Anki cards

def make_cards(card_front, card_back, tags):

    col = aopen(aPATH)
    mm  = col.models
    dm  = col.decks
    
    col.media.addFile(card_front.decode('utf-8'))
    col.media.addFile(card_back.decode('utf-8'))    

    mname = 'AnkiFlash'
    dname = 'Flashcards' + '::' + DECK_NAME

    did = dm.id(dname)
    dm.select(did)

    model = mm.byName(mname)
    if model is None:
        model = flash_theme(mname, mm)

    model['did'] = did
    mm.save(model)
    mm.setCurrent(model)

    card            = col.newNote()
    card['Front']   = u'<img src="%s">' % os.path.basename(card_front)
    card['Back']    = u'<img src="%s">' % os.path.basename(card_back)
    card.tags       = [tags]
    
    col.addNote(card)
    col.save()
    col.close()


# ------------------------------------------------------------------
# ------------------------------------------------------------------
# Convert single pdf's to png's

def gs_pdf_to_png(pdf):
    
    if not os.path.isfile(pdf):
        print "'%s' is not a file. Skip." % pdf
    
    name, ext = os.path.splitext(pdf)
 
    try:    
        # http://ghostscript.com/doc/current/Devices.htm#File_formats
        # http://www.gnu.org/software/ghostscript/devices.html
        # http://ghostscript.com/doc/current/Use.htm#Options
        arglist = [GHOSTSCRIPTCMD,
                  "-dBATCH",
                  "-dNOPAUSE",
                  "-dUseCropBox",
                  "-sOutputFile=%s.png" % name,
                  "-sDEVICE=png16m",
                  "-dDownScaleFactor=3",
                  "-r500",
                  pdf]
        print "Running command:\n%s" % ' '.join(arglist)
    
        sp = subprocess.Popen(
            args=arglist,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    
    except OSError:
        sys.exit("Error executing Ghostscript ('%s'). Is it in your PATH?" % GHOSTSCRIPTCMD)
    except:
        print "Error while running Ghostscript subprocess. Traceback:"
        print "Traceback:\n%s"%traceback.format_exc()
 
    stdout, stderr = sp.communicate()
    print "Ghostscript stdout:\n'%s'" % stdout    
    if stderr:
        print "Ghostscript stderr:\n'%s'" % stderr
    
    return name + '.png'
 

# ------------------------------------------------------------------
# ------------------------------------------------------------------
# Find closest bookmark

def closest(index, num):
    for n in reversed(index):
        if n[0] <= num:
            s = n[1]
            return ''.join([i for i in reduce(lambda s,c: s.replace(c, ''), \
            string.punctuation, s) if not i.isdigit()]).lstrip(' ').replace(' ', '-')


# ------------------------------------------------------------------
# ------------------------------------------------------------------
# Create Bookmark List

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



# ------------------------------------------------------------------
# ------------------------------------------------------------------
# Extract single pdf's from PDF_DIR using start/end pages

def page_extract():

    PDF_IN = PdfFileReader(open(PDF_DIR, 'rb'))
    
    pg_id_num_map = page_id_to_num(PDF_IN)
    outlines = PDF_IN.getOutlines()
    bmrks = bookmarks(outlines, pg_id_num_map)

    png_list = []

    for i in range(int(start) - 1, int(end)):

        output = PdfFileWriter()
        output.addPage(PDF_IN.getPage(i))
        
        base, name_ext = os.path.split(PDF_DIR)
        name, ext      = os.path.splitext(name_ext)
        PDF_OUT        = '{}{}'.format(TMP_DIR, '{}-{}{}'.format(name, str(i).zfill(6), ext))
        
        with open(PDF_OUT, 'wb') as outputStream:
            output.write(outputStream)
        
        png_list.append(gs_pdf_to_png(PDF_OUT))
        png_list.append(closest(bmrks, i+1))
        os.remove(PDF_OUT)
    

    png_list = group(png_list, 4)
    for tup in png_list:
        make_cards(tup[0], tup[2], tup[3])
        print "Current Tag Processed: " + tup[3]




def main():

    if not os.path.isdir(TMP_DIR):
        os.mkdir(TMP_DIR)
        
    page_extract()
    
    shutil.rmtree(TMP_DIR)
    

if __name__ == "__main__":
    main()
