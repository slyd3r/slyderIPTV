#!/usr/bin/env python
# -*- coding: utf-8 -*-

from resources.lib.modules.addon import Addon
from resources.lib.modules import control,client,webutils,convert
import re,sys,os,urlparse,xbmcgui,xbmcplugin

addon = Addon('plugin.video.laliga', sys.argv)
addon_handle = int(sys.argv[1])

if not os.path.exists(control.dataPath):
    os.mkdir(control.dataPath)

AddonPath = addon.get_path()
IconPath = os.path.join(AddonPath, "resources/media/")
fanart = os.path.join(AddonPath + "/fanart.jpg")

def icon_path(filename):
    if 'http://' in filename:
        return filename
    return os.path.join(IconPath, filename)

class info():
    def __init__(self,ico=None):
        self.mode = 'laliga'
        self.name = 'La Liga'
        if ico==None:
            self.icon = icon_path('logo.png')
        else:
            self.icon = icon_path(ico + '.png')
        self.categorized = False
        self.paginated = False
        self.multilink = True

class mylang():
    def __init__(self):
        zh = addon.get_string(30000)[0:8]
        self.spa = (zh == "Zona hor")

class main():
    def __init__(self):
        self.base = 'http://arenavision.in'
        self.headers = { "Cookie" : "beget=begetok; has_js=1;" }

    def links(self,url,tit):
        links = re.findall('(\d+.+?)\[(.+?)\]',url)
        links=self.__prepare_links(links,tit)
        return links

    def channels(self):
        result = client.request('http://arenavision.in/agenda', headers=self.headers)
        result = result.replace('<tr></tr>','')
        table = client.parseDOM(result,'table',attrs={'style':'width: 100%; float: left'})[0]
        rows = client.parseDOM(table,'tr')
        events = self.__prepare_events(rows)
        return events

    @staticmethod
    def convert_time(time,date):
        li = time.split(':')
        li2 = date.split('/')
        hour,minute = li[0],li[1]
        day,month,year = li2[0],li2[1],li2[2]
        import datetime
        # --- Para intentar arreglar los errores de fecha de arenavisión
        hoy = datetime.date.today()
        if hoy.month != month:
            fech = datetime.date(int(year), int(month), int(day))
            diff = fech - hoy
            if abs(diff.days) > 10:
                month = hoy.month
        # --- 
        from resources.lib.modules import pytzimp
        d = pytzimp.timezone(str(pytzimp.timezone('Europe/Ljubljana'))).localize(datetime.datetime(int(year), int(month), int(day), hour=int(hour), minute=int(minute)))
        timezona = control.setting('timezone_new')
        my_location = pytzimp.timezone(pytzimp.all_timezones[int(timezona)])
        convertido = d.astimezone(my_location)
        fm2 = "%H:%M"
        if mylang().spa:
            fmt = "%A, %d de %B de %Y"
            fch = convertido.strftime(fmt)
            hor = convertido.strftime(fm2)
            dict_py = os.path.join(addon.get_path().decode('utf-8'), 'dict_py')
            datos = open(dict_py).read()
            src = re.findall("eng:'(.*?)',spa:'(.*?)'",datos)
            for eng,spa in src:
                fch = fch.replace(eng,spa)
        else:
            fmt = "%A, %B %d, %Y"
            fch = convertido.strftime(fmt)
            hor = convertido.strftime(fm2)
        return hor,fch

    def __prepare_events(self,events):
        new = []
        events.pop(0)
        date_old = ''
        time = ''
        sport = ''
        competition = ''
        for event in events:
            items = client.parseDOM(event,'td')
            i = 0
            for item in items:
                if i==0:
                    date = item
                elif i==1:
                    time = item.replace('CET','').strip()
                elif i==2:
                    sport = item
                elif i==3:
                    competition = item
                elif i==4:
                    event = webutils.remove_tags(item)
                elif i==5:
                    url = item
                i += 1

            try:
            #if time != '' and date !='' and 'Last update' not in date:
                time, date = self.convert_time(time,date)
            except:
                pass

            sport = '(%s - %s)'%(sport,competition)
            event = re.sub('\s+',' ',event)
            title = '[COLOR orange]%s[/COLOR]  [B]%s[/B]'%(time,convert.unescape(event))
            atm1 = addon.get_setting('atm1')
            atm2 = addon.get_setting('atm2')
            if atm1 in title:
                title = title.replace(atm1,atm2)
            data_py = os.path.join(addon.get_path().decode('utf-8'), 'data_py')
            f = open(data_py,'r')
            datos = f.read()
            f.close()
            src = re.findall("bus:'(.*?)',ico:'(.*?)',set:'(.*?)'",datos)
            hay = False
            first = ''
            for bus,ico,stn in src:
                if first == '':
                    first = stn
                if addon.get_setting(stn)=='true':
                    hay = True
                    break
            if not hay:
                addon.set_setting(first,'true')
            for bus,ico,stn in src:
                if bus in sport and addon.get_setting(stn)=='true':
                    if date != date_old:
                        date_old = date
                        new.append(('x','[COLOR yellow]%s[/COLOR]'%date, info().icon))
                    if mylang().spa:
                        if atm2 in title:
                            title = title.replace('[B]','[B][COLOR tomato]')
                            title = title.replace('[/B]','[/COLOR][/B]')
                            ico='atm'
                        if title.find('SPAIN')!=-1:
                            title = title.replace('SPAIN','[COLOR red]ES[COLOR yellow]PA[/COLOR]ÑA[/COLOR]'.decode('utf-8'))
                    title = title.encode('utf-8')
                    new.append((url,title,info(ico).icon))
                    break
        return new

    def __prepare_links(self,links,tit):
        new=[]
        spc=[]
        ace=[]
        tit = re.sub('\[.+?\]','',tit)
        tit = '[COLOR gold]' + tit[7:].replace('-',' [COLOR orange]vs[/COLOR] ') + '[/COLOR]'
        ace.append(('x',tit,''))
        for link in links:
            lang = link[1]
            urls = link[0].split('-')
            for u in urls:
                title = '[B]• AV%s[/B] [%s]'%(u.replace(' ',''),lang)
                url = 'http://arenavision.in/av' + u
                if title.find('AVS')==-1:
                    new.append((url,title,tit))
                else:
                    spc.append((url,title,tit))
        if new!=[]:
            ace.append(('x','[COLOR darkkhaki]AceStream[/COLOR]',''))
        new = ace + new
        if spc!=[]:
            new.append(('x','[COLOR darkkhaki]Sopcast[/COLOR]',''))
            new = new + spc
        return new

    def resolve(self,url):
        import liveresolver
        return liveresolver.resolve(url,cache_timeout=0)

    def doit(self):
        for event in self.channels():
            addon.add_item({'mode': 'get_p2p_event', 'url': event[0],'site':info().mode , 'title':event[1], 'img': event[2]}, {'title': event[1]}, img=event[2], fanart=fanart,is_folder=True)

args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)

if mode is None:
    principal = main()
    principal.doit()
    addon.end_of_directory()

elif mode[0]=='get_p2p_event':
    url = args['url'][0]
    if url != 'x':
        title = args['title'][0]
        site = args['site'][0]
        img = args['img'][0]
        info = info()
        source = main()
        events = source.links(url,title)
        for event in events:
            addon.add_video_item({'mode':'play_p2p', 'url':event[0],'title':title,'title2':event[2],'img':img,'site':site}, {'title': event[1]}, img=img, fanart=fanart)
        addon.end_of_directory()

elif mode[0] == 'play_p2p':
    url = args['url'][0]
    title = args['title'][0]
    tit = args['title2'][0]
    img = args['img'][0]
    site = args['site'][0]
    source = main()
    resolved = source.resolve(url)
    li = xbmcgui.ListItem(title, path=resolved)
    li.setThumbnailImage(img)
    li.setLabel(title)
    li.setInfo('video', {'title': tit})
    handle = int(sys.argv[1])
    if handle > -1:
        xbmcplugin.endOfDirectory(handle, True, False, False)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
    li.setInfo('video', {'title': title})

