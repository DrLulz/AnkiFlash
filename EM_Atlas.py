#!/usr/local/bin/python

####################################################################
# DrLulz Mar-2016
# Dependencies = PyPDF2, Anki, Ghostscript
# All paths are OS X


import subprocess, os, traceback, sys, shutil, re, time
from PyPDF2 import PdfFileWriter, PdfFileReader
from anki import Collection as aopen
from PIL import Image

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage

    
####################################################################
# OPTIONS & SETUP --------------------------------------------------



# STATIC -----------------------------------------------------------

# Ghostscript path, if in PATH set to "gs"
GHOSTSCRIPTCMD = "/usr/local/bin/gs"

TMP_DIR  = '/tmp/flashcards/'
IMG_DIR  = '/tmp/flashcards/img/'
CRD_DIR  = '/tmp/flashcards/cards/'
EXT      = ['.jpg','.png']

# Full path to pdf to be processed
PDF_DIR = '/Users/drlulz/Downloads/AnkiFlash-master/The Atlas of Emergency Medicine Flashcards.pdf'

# Path to your Anki collection
aPATH   = "/Users/drlulz/Documents/Anki/DrLulz/collection.anki2"



# DYNAMIC ----------------------------------------------------------
start = 10
#end   = 11
end   = 537

# Name for new Anki deck
SUBSECTION  = 'The Atlas of Emergency Medicine'
DECK_NAME   = 'Flashcards::{}'.format(SUBSECTION)
#TAGS        = SUBSECTION.replace(' ', '-')


PARITY = (int(start) - 1) % 2


####################################################################
# MAIN -------------------------------------------------------------

def group(lst, n):
    for i in range(0, len(lst), n):
        val = lst[i:i+n]
        if len(val) == n:
            yield tuple(val)


def rm_files(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception, e:
            print e


def get_index(l, index, value):
    for pos,t in enumerate(l):
        if value in t[index]:
            return pos
    raise ValueError("list.index(x): x not in list")


def flash_theme(name, mm):
    abspath = os.path.abspath(__file__)
    
    path  = os.path.dirname(abspath) + '/template/EM_Atlas'
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



def make_card(FRONT_IMG, ANSWER, ANS_IMG, BACK_IMG):

        col = aopen(aPATH)
        mm  = col.models
        dm  = col.decks
    
        col.media.addFile(FRONT_IMG.decode('utf-8'))
        col.media.addFile(ANS_IMG.decode('utf-8'))
        
        if BACK_IMG:
            col.media.addFile(BACK_IMG.decode('utf-8'))

        mname = 'EM-Atlas'
        dname = DECK_NAME

        did = dm.id(dname)
        dm.select(did)

        model = mm.byName(mname)
        if model is None:
            model = flash_theme(mname, mm)

        model['did'] = did
        mm.save(model)
        mm.setCurrent(model)

        card            = col.newNote()
        card['Note ID'] = str(card.id)
        card['Front']   = u'<img src="%s">' % os.path.basename(FRONT_IMG)
        if BACK_IMG:
            card['Back']= u'<span class="highlight" style="font-weight: bold; color:#FFFFFF">&nbsp;' + ANSWER + u'&nbsp;</span>' + u'<img src="%s">' % os.path.basename(BACK_IMG)
        else:
            card['Back']= u'<span class="highlight" style="font-weight: bold; color:#FFFFFF">&nbsp;' + ANSWER + u'&nbsp;</span>'
        card['B Note']  = u'<img src="%s">' % os.path.basename(ANS_IMG)
        card.tags       = [ANSWER.replace(' ', '-')]

        col.addNote(card)
        col.save()
        col.close()



def process_front(PDF_IN):
    
    def get_bboxes(pg):
        # LEFT, LOWER, RIGHT, UPPER
        bboxes = []
        for obj in pg:
            if isinstance(obj, LTFigure):
                bboxes.append( obj.bbox )
        return sorted(bboxes, key=lambda x: x[0])

    with open(PDF_IN, 'rb') as f:
        p = PDFParser(f)
        d = PDFDocument(p)

        r = PDFResourceManager()
        l = LAParams()
        v = PDFPageAggregator(r, laparams=l)
        i = PDFPageInterpreter(r, v)

        for page in PDFPage.create_pages(d):
            i.process_page(page)
            pg = v.get_result()
            bb = get_bboxes(pg)


    def crop(PDF_IN, bb):
        #pdfcrop --bbox "LEFT LOWER RIGHT UPPER" input.pdf ouput.pdf
        
        cropped = []
        
        for j, b in enumerate(bb):
            base, name_ext = os.path.split(PDF_IN)
            name, ext = os.path.splitext(name_ext)
            PDF_OUT = os.path.join(IMG_DIR, '{}-{}{}'.format(name, j, ext))
        
            LEFT, LOWER, RIGHT, UPPER = b
            bbox = '{} {} {} {}'.format(LEFT, LOWER, RIGHT, UPPER)
        
            cmd = ['/usr/texbin/pdfcrop', '--gscmd', '/usr/local/bin/gs', '--pdftexcmd', '/usr/texbin/pdftex', '--bbox', bbox, PDF_IN, PDF_OUT]
            sp = subprocess.Popen(args=cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print 'Cropped:: {}'.format(PDF_OUT)
            cropped.append(PDF_OUT)
        
        return cropped
        
    

    cropped_pdfs = crop(PDF_IN, bb)
    time.sleep(5)
    
    def pdf_to_png(file_list):
        
        converted = []
        
        for FILE_IN in file_list:
            # /usr/local/bin/gs -q -dNOPAUSE -dBATCH -sDEVICE=pngalpha -r150 -sOutputFile=

            base, name_ext = os.path.split(FILE_IN)
            name, ext = os.path.splitext(name_ext)
            
            FILE_OUT = os.path.join(IMG_DIR, '{}.png'.format(name))
            
            cmd = ['/usr/local/bin/gs', '-dNOPAUSE', '-dBATCH', '-sDEVICE=pngalpha', '-r150', '-sOutputFile={}'.format(FILE_OUT), FILE_IN]
            sp = subprocess.Popen(args=cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print 'Converted:: {}'.format(FILE_OUT)
            converted.append(FILE_OUT)
        
        return converted
    
    
    cropped_pngs = pdf_to_png(sorted(cropped_pdfs))
    time.sleep(5)
    
    def combine_pngs(pngs):
        

        imgs = []
        for img_path in pngs:
            img = Image.open(img_path)
            imgs.append( (img_path, img.size) )

        fmax = max(imgs, key = lambda t: t[1][1])
        hmax = fmax[1][1]
        wtot = sum([wh[0] for path, wh in imgs])
        wtot = wtot + ((len(imgs)-1)*30)
    
        result = Image.new('RGBA', (wtot, hmax))

        for i, img in enumerate(sorted(imgs)):

            im = Image.open(img[0])

            if i == 0:
                x, y = 0, 0        
                w, h = img[1]
                if h < hmax:
                    y = (hmax-h)/2
                result.paste(im, (x, y, x + w, y + h))

            else:
                x = (x+30) + w 
                y = 0
                w, h = img[1]
                if h < hmax:
                    y = (hmax-h)/2
                result.paste(im, (x, y, x + w, y + h))


            base, name_ext = os.path.split(PDF_IN)
            name, ext = os.path.splitext(name_ext)
    
            NEW_IMG = os.path.join(CRD_DIR, '{}-QUESTION.png'.format(name))
            result.save(NEW_IMG, 'PNG')
            
        return NEW_IMG
    
    
    return combine_pngs(cropped_pngs)



def process_back(PDF_IN):
    
    
    def get_bboxes(pg):
        # LEFT, LOWER, RIGHT, UPPER
        
        bimage = []
        bboxes = []
        
        for obj in pg:
            if isinstance(obj, LTFigure):
                bimage.append( obj.bbox )
                
            if isinstance(obj, LTTextBox) or isinstance(obj, LTTextLine):
                bboxes.append( (obj.get_text(), obj.bbox) )
        
        if bimage:
            return sorted(bimage, key=lambda x: x[0]), bboxes
        else:
            return None, bboxes


    with open(PDF_IN, 'rb') as f:
        p = PDFParser(f)
        d = PDFDocument(p)

        r = PDFResourceManager()
        l = LAParams()
        v = PDFPageAggregator(r, laparams=l)
        i = PDFPageInterpreter(r, v)

        for page in PDFPage.create_pages(d):
            i.process_page(page)
            pg = v.get_result()
            bimg, bb = get_bboxes(pg)
    


    def crop_imgs(PDF_IN, bb):
        #pdfcrop --bbox "LEFT LOWER RIGHT UPPER" input.pdf ouput.pdf
        
        cropped = []
        
        for j, b in enumerate(bb):
            base, name_ext = os.path.split(PDF_IN)
            name, ext = os.path.splitext(name_ext)
            PDF_OUT = os.path.join(IMG_DIR, '{}-{}{}'.format(name, j, ext))
        
            LEFT, LOWER, RIGHT, UPPER = b
            bbox = '{} {} {} {}'.format(LEFT, LOWER, RIGHT, UPPER)
        
            cmd = ['/usr/texbin/pdfcrop', '--gscmd', '/usr/local/bin/gs', '--pdftexcmd', '/usr/texbin/pdftex', '--bbox', bbox, PDF_IN, PDF_OUT]
            sp = subprocess.Popen(args=cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print 'Cropped:: {}'.format(PDF_OUT)
            cropped.append(PDF_OUT)
        
        return cropped
        
    

    if bimg:
        cropped_pdfs = crop_imgs(PDF_IN, bimg)
    else:
        cropped_pdfs = None

    time.sleep(5)
    

    def pdf_to_png(file_list):
        
        converted = []
        
        for FILE_IN in file_list:
            # /usr/local/bin/gs -q -dNOPAUSE -dBATCH -sDEVICE=pngalpha -r150 -sOutputFile=

            base, name_ext = os.path.split(FILE_IN)
            name, ext = os.path.splitext(name_ext)
            
            FILE_OUT = os.path.join(IMG_DIR, '{}.png'.format(name))
            
            cmd = ['/usr/local/bin/gs', '-dNOPAUSE', '-dBATCH', '-sDEVICE=pngalpha', '-dTextAlphaBits=4', '-r300', '-sOutputFile={}'.format(FILE_OUT), FILE_IN]
            sp = subprocess.Popen(args=cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print 'Converted:: {}'.format(FILE_OUT)
            converted.append(FILE_OUT)
        
        return converted
    

    if cropped_pdfs:
        cropped_pngs = pdf_to_png(sorted(cropped_pdfs))
    else:
        cropped_pngs = None

    time.sleep(5)
    
    def combine_pngs(pngs):

        imgs = []
        for img_path in pngs:
            img = Image.open(img_path)
            imgs.append( (img_path, img.size) )

        fmax = max(imgs, key = lambda t: t[1][1])
        hmax = fmax[1][1]
        wtot = sum([wh[0] for path, wh in imgs])
        wtot = wtot + ((len(imgs)-1)*30)
    
        result = Image.new('RGBA', (wtot, hmax))

        for i, img in enumerate(sorted(imgs)):

            im = Image.open(img[0])

            if i == 0:
                x, y = 0, 0        
                w, h = img[1]
                if h < hmax:
                    y = (hmax-h)/2
                result.paste(im, (x, y, x + w, y + h))

            else:
                x = (x+30) + w 
                y = 0
                w, h = img[1]
                if h < hmax:
                    y = (hmax-h)/2
                result.paste(im, (x, y, x + w, y + h))


            base, name_ext = os.path.split(PDF_IN)
            name, ext = os.path.splitext(name_ext)
    
            PNG_OUT = os.path.join(CRD_DIR, '{}-ANS-IMAGE.png'.format(name))
            result.save(PNG_OUT, 'PNG')
            
        return PNG_OUT
    
    
    if cropped_pngs:
        back_image = combine_pngs(cropped_pngs)
    else:
        back_image = None



    def extract_ans(PDF_IN, BBOXES):
        
        if ('contributor:' in BBOXES[-2][0]) or ('contributor:' in BBOXES[-1][0]):
            credits = get_index(BBOXES, 0, 'contributor:')
            content = BBOXES[1:credits]

        elif ('permission' in BBOXES[-2][0]) or ('permission' in BBOXES[-1][0]):
            credits = get_index(BBOXES, 0, 'permission')
            content = BBOXES[1:credits]
        else:
            content = BBOXES[1:]
            

        top = content[0][1]
        bot = content[-1][1]

        LEFT  = round(bot[0]) - 5
        LOWER = round(bot[1]) - 5
        RIGHT = round(top[2]) + 5
        UPPER = round(top[3]) + 3
    
        I = PdfFileReader(file(PDF_IN, 'rb'))
        O = PdfFileWriter()
        n = I.getNumPages()

        for i in range(n):
            pg = I.getPage(i)
            pg.cropBox.lowerLeft  = (LEFT,  LOWER)
            pg.cropBox.upperRight = (RIGHT, UPPER)
            O.addPage(pg)

        base, name_ext = os.path.split(PDF_IN)
        name, ext = os.path.splitext(name_ext)
        
        PDF_OUT = os.path.join(IMG_DIR, '{}-ANSWER.pdf'.format(name))
    
        output = file(PDF_OUT, 'wb')
        O.write(output)
        output.close()
    
        return PDF_OUT



    def ans_to_png(PDF_IN):
    
        if not os.path.isfile(PDF_IN):
            print "'%s' is not a file. Skip." % PDF_IN
    

        base, name_ext = os.path.split(PDF_IN)
        name, ext = os.path.splitext(name_ext)
        PNG_OUT   = os.path.join(CRD_DIR, '{}.png'.format(name))
 
        arglist = [GHOSTSCRIPTCMD,
                  "-dBATCH",
                  "-dNOPAUSE",
                  "-dUseCropBox",
                  "-dTextAlphaBits=4",
                  "-sOutputFile=%s" % PNG_OUT,
                  "-sDEVICE=png16m",
                  "-dDownScaleFactor=1",
                  "-r300",
                  PDF_IN]

        sp = subprocess.Popen(args=arglist, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return PNG_OUT

    
    answer  = bb[0][0]
    ans_png = ans_to_png(extract_ans(PDF_IN, bb))
    time.sleep(5)
    
    if back_image:
        return answer, ans_png, back_image
    else:
        return answer, ans_png, None





def page_extract():

    PDF_IN = PdfFileReader(open(PDF_DIR, 'rb'))
    
    cards = []
    for i in range(int(start) - 1, int(end)):

        output = PdfFileWriter()
        output.addPage(PDF_IN.getPage(i))
        
        base, name_ext = os.path.split(PDF_DIR)
        name, ext      = os.path.splitext(name_ext)
        PDF_OUT        = '{}{}'.format(TMP_DIR, '{}-{}{}'.format(name, i, ext))
        
        with open(PDF_OUT, 'wb') as outputStream:
            output.write(outputStream)
        
        if (i % 2) == PARITY:
            card = ()
            FRONT_IMG = process_front(PDF_OUT)
            card = card + (FRONT_IMG,)
            rm_files(IMG_DIR)
            os.remove(PDF_OUT)
        else:
            ANSWER, ANS_IMG, BACK_IMG = process_back(PDF_OUT)
            card = card + (ANSWER, ANS_IMG, BACK_IMG)
            cards.append(card)
            rm_files(IMG_DIR)
            os.remove(PDF_OUT)


    for card in cards:
        FRONT_IMG, ANSWER, ANS_IMG, BACK_IMG = card
        make_card(FRONT_IMG, ANSWER, ANS_IMG, BACK_IMG)
        print 'making card: {!r}'.format(ANSWER)

    rm_files(CRD_DIR)





def main():

    if not os.path.isdir(TMP_DIR):
        os.mkdir(TMP_DIR)

    if not os.path.isdir(IMG_DIR):
        os.mkdir(IMG_DIR)
    
    if not os.path.isdir(CRD_DIR):
        os.mkdir(CRD_DIR)
        
    page_extract()
    
    shutil.rmtree(TMP_DIR)
    

if __name__ == "__main__":
    main()
    
