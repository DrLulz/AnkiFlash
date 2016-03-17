############################################################################################
#  This script creates Anki decks from a web application.
#  DrLulz Mar-2016
############################################################################################

class IM:
    import os, sys, wget, ntpath, unicodedata, codecs, linecache, time
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.action_chains import ActionChains
    from operator import itemgetter
    from bs4 import BeautifulSoup as bs
    #from anki import Collection as aopen
    
    from Quartz.CoreGraphics import CGEventCreateMouseEvent
    from Quartz.CoreGraphics import CGEventPost
    from Quartz.CoreGraphics import kCGEventMouseMoved
    from Quartz.CoreGraphics import kCGEventLeftMouseDown
    from Quartz.CoreGraphics import kCGEventLeftMouseUp
    from Quartz.CoreGraphics import kCGMouseButtonLeft
    from Quartz.CoreGraphics import kCGHIDEventTap
    from Quartz.CoreGraphics import CGEventCreateScrollWheelEvent
    
    
    
    def __init__(self, _user_, _pass_):
        self._user_ = _user_
        self._pass_ = _pass_
        self.driver = self.webdriver.Firefox()
        self.wait   = self.WebDriverWait(self.driver, 10)
        self.action = self.webdriver.ActionChains(self.driver)
        
        
        
    def login(self):
        
        try:
            self.driver.get('https://flashcards.acponline.org/login')
            #self.driver.maximize_window()
            self.driver.set_window_position(0, 0)
            #self.driver.set_window_size(1024, 768)
            self.driver.set_window_size(1024, 2000)
            
            _user = self.driver.find_element_by_xpath('//*[(@id = "username")]')
            _pass = self.driver.find_element_by_xpath('//*[(@id = "password")]')
            
            _user.send_keys(self._user_)
            _pass.send_keys(self._pass_)
            
            login = self.driver.find_element_by_xpath('//*[(@type = "submit")]')
            login.submit()
    
            IM_essentials = self.wait.until(self.EC.element_to_be_clickable((self.By.LINK_TEXT,'IM Essentials Flashcards')))
            IM_essentials.click()
            
            self.load_sections()
        except:
            self.error()
            
    
    
    def load_sections(self):
        try:
            source = self.driver.find_element_by_css_selector('ul.decks')
            html   = source.get_attribute('innerHTML')

            soup = self.bs(html, 'html.parser')

            result = []
            groups = soup.findAll('li', {'class' : 'deck-group'})
            for group in groups:
                title     = group.find('div', {'class' : 'subspecialty'}).text
                sections  = group.findAll('li', {'class' : 'chapter'})
                subtitles = tuple( (section.findChildren()[0].text, int(section.findChildren()[1].text), section.get('data-chapter-id')) for section in sections if not 'All Chapters' in section.findChildren()[0].text )
                result.append( ((title, group.get('id')), subtitles) )

            self.iter_sections(result)
        except:
            self.error()
        
        
        
    def click_xpath(self, _xpath_):
        _xpath = self.wait.until(self.EC.element_to_be_clickable((self.By.XPATH, _xpath_)))
        
        loca = _xpath.location # {'y': 202, 'x': 165}
        size = _xpath.size # {'width': 77, 'height': 22}
#        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#        self.driver.execute_script("window.scrollTo(0, {})".format(loca['y']))
        self.scroll_wheel_down((loca['y']-50))
        self.time.sleep(1)
        
        _xpath.click()



    def iter_sections(self, sections):
        try:
            
            for x, section in enumerate(sections):
                
                for y, subsection in enumerate(section[1]):

                    z = x + y
                    
                    section_id = self.wait.until(self.EC.element_to_be_clickable((self.By.ID, section[0][1])))
                    section_id.click()
                    

                    self.click_xpath('//*[(@data-chapter-id = "{}")]'.format(subsection[2]))
#                    self.click_text(subsection[0])
                    
                
                    start_button = self.wait.until(self.EC.element_to_be_clickable((self.By.CLASS_NAME, 'start-deck')))
                    start_button.click()

                    if not z:                    
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '.start .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '.switch .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '.right .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '.wrong .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '.menu .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '.menu-display .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '#back-to-deck .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '#favorite .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '#mark-correct .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '#mark-incorrect .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '#previous-card .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '#next-card .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '#related-link .next'))).click()
                        self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '.done .next'))).click()
                    

                    cards = self.get_cards(subsection[1], z)
                
                    print 'section\t\t= {}\nsubsection\t= {} ({})\n\n'.format(section[0], subsection, len(cards))

                    self.make_cards(section[0][0], subsection[0], cards)
                    
                    self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '.icon-arrow-slim-left-circle'))).click()
#                    self.mouseclick(50, 503)
#                    self.driver.refresh()
#                    self.wait.until(self.EC.element_to_be_clickable((self.By.ID, section[0][1]))).click()
        except:
            self.error()
            

                
    def get_cards(self, number, z):

        n = 0 if z != 0 else 1
        try:
            cards = []
            
            for i in range(number+n):
                
                self.wait.until(self.EC.element_to_be_clickable((self.By.CSS_SELECTOR, '#card')))
                source = self.driver.find_element_by_css_selector('#card')
                html   = source.get_attribute('innerHTML')

                soup  = self.bs(html, 'html.parser')            
                sides = soup.findAll('div', {'class' : 'content'})
                
                card = (sides[0], sides[1])

                if not card in cards:
                    cards.append(card)


#                el = self.driver.find_element_by_css_selector('.next-card.card-navigate')
#                self.driver.execute_script('arguments[0].click()', el)
#                self.driver.execute_script("document.getElementsByClassName('next-card')[0].click()")
                self.mouseclick(850, 700)
                self.time.sleep(1)

            
            return cards

        except:
            self.error()
        


    def make_cards(self, section, subsection, cards):
        from anki import Collection as aopen
        
        try:

            #print [(card[0].encode('UTF-8'), card[1].encode('UTF-8')) for card in cards]
            
            for card in cards:
                print 'SECTION: {}\nSUBSECTION: {}'.format(section, subsection)
    
                col = aopen('/Users/drlulz/Documents/Anki/DrLulz/collection.anki2')
                mm  = col.models
                dm  = col.decks

#                col.media.addFile(card_front.decode('utf-8'))

                mname = 'AnkiFlash-IME'
                dname = 'Flashcards' + '::' + 'IM Essentials::{}::{}'.format(section, subsection)

                did = dm.id(dname)
                dm.select(did)

                model = mm.byName(mname)
                if model is None:
                    model = self.flash_theme(mname, mm)

                model['did'] = did
                mm.save(model)
                mm.setCurrent(model)


                FRONT = u''.join(unicode(i) for i in card[0])
                BACK  = u''.join(unicode(i) for i in card[1])
            
                card            = col.newNote()
                card['Note ID'] = str(card.id)
                card['Front']   = FRONT
                card['Back']    = BACK
                card.tags       = [subsection.replace(' ', '-')]

                col.addNote(card)
                col.save()
                col.close()

        except:
            self.error()



    def flash_theme(self, name, mm):
    
        abspath = self.os.path.abspath(__file__)

        path  = self.os.path.dirname(abspath) + '/template'
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
    

    def exists_css_sel(self, css_selector):
        try:
            self.driver.find_element_by_css_selector(css_selector)
        except self.NoSuchElementException:
            return False
        return True
        
    def exists_xpath(self, xpath):
        try:
            self.driver.find_element_by_xpath(xpath)
        except self.NoSuchElementException:
            return False
        return True
        
    def mouseEvent(self, type, posx, posy):
            theEvent = self.CGEventCreateMouseEvent(
                        None, 
                        type, 
                        (posx,posy), 
                        self.kCGMouseButtonLeft)
            self.CGEventPost(self.kCGHIDEventTap, theEvent)
            
    def mouseclick(self, posx, posy):
        self.mouseEvent(self.kCGEventMouseMoved, posx, posy)
        self.mouseEvent(self.kCGEventLeftMouseDown, posx, posy)
        self.mouseEvent(self.kCGEventLeftMouseUp, posx, posy)
        
    def scroll_wheel_up(self, num_times):
        for _ in xrange(num_times):
            event = self.CGEventCreateScrollWheelEvent(None, 0, 1, 1)
            self.CGEventPost(self.kCGHIDEventTap, event)

    def scroll_wheel_down(self, num_times):
        for _ in xrange(num_times):
            event = self.CGEventCreateScrollWheelEvent(None, 0, 1, -1)
            self.CGEventPost(self.kCGHIDEventTap, event)
                        
    def error(self):
        exc_type, exc_obj, tb = self.sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        self.linecache.checkcache(filename)
        line = self.linecache.getline(filename, lineno, f.f_globals)
        print 'LINE: {}'.format(lineno)
        print 'CODE: {}'.format(line.strip())
        print 'ERROR: {}'.format(exc_obj)
        self.sys.exit()


if __name__ == '__main__':
    
    _user_ = ''
    _pass_ = ''
    
    im = IM(_user_, _pass_)
    im.login()