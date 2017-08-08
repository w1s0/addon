# -*- coding: utf-8 -*-

import re

from core import config
from core import httptools
from core import logger
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item

__modo_grafico__ = config.get_setting('modo_grafico', "ver-pelis")
host = "http://ver-pelis.me"

def mainlist(item):
    logger.info()
    itemlist = []
    i = 0
    global i
    itemlist.append(
        item.clone(title = "[COLOR oldlace]Películas[/COLOR]", action = "scraper", url = host + "/ver/",
                   thumbnail = "http://imgur.com/36xALWc.png", fanart = "http://imgur.com/53dhEU4.jpg",
                   contentType = "movie"))
    itemlist.append(item.clone(title = "[COLOR oldlace]Películas por año[/COLOR]", action = "categoria_anno",
                               url = host, thumbnail = "http://imgur.com/36xALWc.png", extra = "Por año",
                               fanart = "http://imgur.com/53dhEU4.jpg", contentType = "movie"))
    itemlist.append(item.clone(title = "[COLOR oldlace]Películas en Latino[/COLOR]", action = "scraper",
                               url = host + "/ver/latino/", thumbnail = "http://imgur.com/36xALWc.png",
                               fanart = "http://imgur.com/53dhEU4.jpg", contentType = "movie"))
    itemlist.append(item.clone(title = "[COLOR oldlace]Películas en Español[/COLOR]", action = "scraper",
                               url = host + "/ver/subtituladas/", thumbnail = "http://imgur.com/36xALWc.png",
                               fanart = "http://imgur.com/53dhEU4.jpg", contentType = "movie"))
    itemlist.append(item.clone(title = "[COLOR oldlace]Películas Subtituladas[/COLOR]", action = "scraper",
                               url = host + "/ver/espanol/", thumbnail = "http://imgur.com/36xALWc.png",
                               fanart = "http://imgur.com/53dhEU4.jpg", contentType = "movie"))
    itemlist.append(item.clone(title = "[COLOR oldlace]Por Género[/COLOR]", action = "categoria_anno",
                               url = host, thumbnail = "http://imgur.com/36xALWc.png", extra = "Categorias",
                               fanart = "http://imgur.com/53dhEU4.jpg", contentType = "movie"))

    itemlist.append(itemlist[-1].clone(title = "[COLOR orangered]Buscar[/COLOR]", action = "search",
                                       thumbnail = "http://imgur.com/ebWyuGe.png", fanart = "http://imgur.com/53dhEU4.jpg",
                                       contentType = "tvshow"))

    return itemlist

def categoria_anno(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'mobile_menu.*?(%s.*?)</ul>' %item.extra)
    logger.info("Intel44 %s" %bloque)
    patron  = '(?is)<li.*?a href="([^"]+)'
    patron += '.*?title="[^"]+">([^<]+)'
    match = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in match:
        itemlist.append(Item(
                        channel = item.channel,
                        action = "scraper",
                        title = titulo,
                        url = url
                        ))
        
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/ver/buscar?s=" + texto
    item.extra = "search"
    if texto != '':
        return scraper(item)


def scraper(item):
    logger.info()
    itemlist = []
    url_next_page = ""
    global i
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = scrapertools.find_multiple_matches(data,
                                                '<a class="thumb cluetip".*?href="([^"]+)".*?src="([^"]+)" alt="([^"]+)".*?"res">([^"]+)</span>')
    if len(patron) > 20:
        if item.next_page != 20:
            url_next_page = item.url
            patron = patron[:20]
            next_page = 20
            item.i = 0
        else:
            patron = patron[item.i:][:20]
            next_page = 20

            url_next_page = item.url

    for url, thumb, title, cuality in patron:
        title = re.sub(r"Imagen", "", title)
        titulo = "[COLOR floralwhite]" + title + "[/COLOR]" + " " + "[COLOR crimson][B]" + cuality + "[/B][/COLOR]"
        title = re.sub(r"!|\/.*", "", title).strip()

        if item.extra != "search":
            item.i += 1
        new_item = item.clone(action="findvideos", title=titulo, url=url, thumbnail=thumb, fulltitle=title,
                              contentTitle=title, contentType="movie", library=True)
        new_item.infoLabels['year'] = get_year(url)
        itemlist.append(new_item)

    ## Paginación
    if url_next_page:
        itemlist.append(item.clone(title="[COLOR crimson]Siguiente >>[/COLOR]", url=url_next_page, next_page=next_page,
                                   thumbnail="http://imgur.com/w3OMy2f.png", i=item.i))
    try:
        from core import tmdb
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        for item in itemlist:
            if not "Siguiente >>" in item.title:
                if "0." in str(item.infoLabels['rating']):
                    item.infoLabels['rating'] = "[COLOR indianred]Sin puntuacíon[/COLOR]"
                else:
                    item.infoLabels['rating'] = "[COLOR orange]" + str(item.infoLabels['rating']) + "[/COLOR]"
                item.title = item.title + "  " + str(item.infoLabels['rating'])
    except:
        pass

    for item_tmdb in itemlist:
        logger.info(str(item_tmdb.infoLabels['tmdb_id']))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data_post = scrapertools.find_single_match(data, "type: 'POST'.*?id: (.*?),slug: '(.*?)'")
    if data_post:
        post = 'id=' + data_post[0] + '&slug=' + data_post[1]
        data_info = httptools.downloadpage(host + '/ajax/cargar_video.php', post=post).data
        enlaces = scrapertools.find_multiple_matches(data_info,
                                                     "</i> (\w+ \w+).*?<a onclick=\"load_player\('([^']+)','([^']+)', ([^']+),.*?REPRODUCIR\">([^']+)</a>")
        for server, id_enlace, name, number, idioma_calidad in enlaces:

            if "SUBTITULOS" in idioma_calidad and not "P" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("SUBTITULOS", "VO")
                idioma_calidad = idioma_calidad.replace("VO", "[COLOR orangered] VO[/COLOR]")
            elif "SUBTITULOS" in idioma_calidad and "P" in idioma_calidad:
                idioma_calidad = "[COLOR indianred] " + idioma_calidad + "[/COLOR]"

            elif "LATINO" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("LATINO", "[COLOR red]LATINO[/COLOR]")
            elif "Español" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("Español", "[COLOR crimson]ESPAÑOL[/COLOR]")
            if "HD" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("HD", "[COLOR crimson] HD[/COLOR]")
            elif "720" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("720", "[COLOR firebrick] 720[/COLOR]")
            elif "TS" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("TS", "[COLOR brown] TS[/COLOR]")

            elif "CAM" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("CAM", "[COLOR darkkakhi] CAM[/COLOR]")

            url = host + "/ajax/video.php?id=" + id_enlace + "&slug=" + name + "&quality=" + number

            if not "Ultra" in server:
                server = "[COLOR cyan][B]" + server + "[/B][/COLOR]"
                extra = ""
            else:
                server = "[COLOR yellow][B]" + server + "[/B][/COLOR]"
                extra = "yes"
            title = server.strip() + "  " + idioma_calidad
            itemlist.append(Item(channel=item.channel, action="play", title=title, url=url, fanart=item.fanart,
                                 thumbnail=item.thumbnail, fulltitle=item.title, extra=extra, folder=True))
        if item.library and config.get_videolibrary_support() and len(itemlist) > 0:
            infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'],
                          'title': item.infoLabels['title']}
            itemlist.append(Item(channel=item.channel, title="Añadir esta película a la videoteca",
                                 action="add_pelicula_to_library", url=item.url, infoLabels=infoLabels,
                                 text_color="0xFFf7f7f7",
                                 thumbnail='http://imgur.com/gPyN1Tf.png'))
    else:
        itemlist.append(
            Item(channel=item.channel, action="", title="[COLOR red][B]Upps!..Archivo no encontrado...[/B][/COLOR]",
                 thumbnail=item.thumbnail))
    return itemlist


def play(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\\', '', data)
    item.url = scrapertools.find_single_match(data, 'src="([^"]+)"')
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, 'window.location="([^"]+)"')
    if item.extra == "yes":
        data = httptools.downloadpage(url).data
        url = scrapertools.find_single_match(data, '(?is)iframe src="([^"]+)"')
    videolist = servertools.find_video_items(data=url)
    for video in videolist:
        itemlist.append(Item(channel=item.channel, url=video.url, server=video.server,
                             title="[COLOR floralwhite][B]" + video.server + "[/B][/COLOR]", action="play",
                             folder=False))

    return itemlist


def get_year(url):
    data = httptools.downloadpage(url).data
    year = scrapertools.find_single_match(data, '<p><strong>Año:</strong>(.*?)</p>')
    if year == "":
        year = " "
    return year
