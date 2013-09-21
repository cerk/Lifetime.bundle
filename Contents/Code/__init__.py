import re

NAME = 'Lifetime'
ICON = 'icon-default.png'
ART = 'art-default.jpg'

LT_BASE = '/video/lifetime'

LT_URL = 'http://www.mylifetime.com'
LT_VIDEO = LT_URL + '/video'
LT_SHOWS = LT_URL + '/shows'
LT_MOVIES = LT_URL + '/movies'
LT_SHOW_PREFIX = LT_SHOWS + '/'
LT_MOVIE_PREFIX = LT_MOVIES + '/'
LT_VIDEO_POSTFIX = '/video'

MILLISECONDS_IN_A_MINUTE = 60000

####################################################################################################
def Start():

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    NextPageObject.thumb = R(ICON)
    EpisodeObject.thumb = R(ICON)
    VideoClipObject.thumb = R(ICON)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0'

####################################################################################################
@handler(LT_BASE, NAME, art=ART, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()

    html = HTML.ElementFromURL(LT_VIDEO)
    
    for header in html.xpath('//h3[not(@id)]'):
        title = header.xpath('./a/text()')[0]
        oc.add(DirectoryObject(key=Callback(Video, title=title), title=title))

    return oc
    
####################################################################################################
@route(LT_BASE + '/videos')
def Video(title):
    
    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(LT_VIDEO)
    
    for show_element in html.xpath('//h3/a[text()="' + title + '"]/../following-sibling::div[1]//span[@class="views-field-title"]//a'):
        show = show_element.xpath('./text()')[0]
        original_url = show_element.xpath('./@href')[0]
        alternate_url = re.sub(r'&', 'and', show)
        alternate_url = re.sub(r' ', '-', alternate_url)
        alternate_url = re.sub(r'[^A-Za-z0-9-]', '', alternate_url)
        alternate_url = alternate_url.lower()

        url = original_url + LT_VIDEO_POSTFIX
        # By trial and error, any original URL containing 'test', 'page', or a number at the end needs to be corrected.
        incorrect_url_match = re.search(r'test|page|\d$', original_url)

        if re.search(r'^' + LT_SHOWS, original_url):
            if incorrect_url_match:
                url = LT_SHOW_PREFIX + alternate_url + LT_VIDEO_POSTFIX

            oc.add(DirectoryObject(
                key = Callback(Show, title=show, url=url),
                title = show,
                thumb = R(ICON)
            ))
            
        if re.search(r'^' + LT_MOVIES, original_url):
            if incorrect_url_match:
                url = LT_MOVIE_PREFIX + alternate_url + LT_VIDEO_POSTFIX
     
            oc.add(DirectoryObject(
                key = Callback(Season, title=show, url=url),
                title = show,
                thumb = R(ICON)
            ))

    return oc
    
####################################################################################################
def GetInfoFromVideoPage(html):

    media_type = html.xpath('//input[@name="media_type"]/@value')[0]
    media_season = html.xpath('//input[@name="media_season"]/@value')[0]
    primary_property_tid = html.xpath('//input[@name="primary_property_tid"]/@value')[0]
    primary_property_vid = html.xpath('//input[@name="primary_property_vid"]/@value')[0]
    
    thumb = R(ICON)
    logo = R(ICON)
    logo_image = html.xpath('//div[@class="video-relative-logo"]//a/img/@src')
    if logo_image:
        thumb = logo_image[0]
        logo = logo_image[0]
    promo_logo_image = html.xpath('//div[@class="video-promo-logo"]//a/img/@src')
    if promo_logo_image:
        thumb = promo_logo_image[0]
            
    return media_type, media_season, primary_property_tid, primary_property_vid, thumb, logo
    
####################################################################################################
@route(LT_BASE + '/shows')
def Show(title, url):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)

    media_type, media_season, primary_property_tid, primary_property_vid, thumb, logo = GetInfoFromVideoPage(html)
    
    url_postfix = '?page=0&field_length_value_many_to_one=All&primary_property_tid=' + primary_property_tid + '&primary_property_vid=' + primary_property_vid + '&media_type=' + media_type
    
    primary_property = html.xpath('//select[@name="primary_property"]')[0]
    
    for optgroup in primary_property.xpath('./optgroup'):
        label = optgroup.xpath('./@label')[0]
        if re.search(r'^Season', label):
            new_title = title + ' ' + label
            for option in optgroup.xpath('./option'):
                value = option.xpath('./@value')[0]
                text = option.xpath('./text()')[0]
                if re.search(r'^All Episodes', text):
                    new_url = url + url_postfix + '&media_season=' + value + '&primary_property=' + value
                    oc.add(SeasonObject(
                        url = new_url,
                        key = Callback(Season, title=new_title, url=new_url),
                        index = int(re.search(r'(\d+)', label).group(1)),
                        title = label,
                        thumb = thumb
                    ))
                    
    for option in primary_property.xpath('./option'):
        value = option.xpath('./@value')[0]
        text = option.xpath('./text()')[0]
        if (re.search(r'^Season', text)):
            new_title = title + ' ' + text
            new_url = url + url_postfix + '&media_season=' + value + '&primary_property=' + value
            oc.add(SeasonObject(
                url = new_url,
                key = Callback(Season, title=new_title, url=new_url),
                index = int(re.search(r'(\d+)', text).group(1)),
                title = text,
                thumb = thumb
            ))

    # Sort by season number.
    oc.objects.sort(key=lambda obj: obj.index, reverse=True)       
    return oc
   
####################################################################################################
@route(LT_BASE + '/seasons')
def Season(title, url):

    oc = ObjectContainer(title2=title)
    base_url = url.split('?')[0]    
    html = HTML.ElementFromURL(url)

    media_type, media_season, primary_property_tid, primary_property_vid, thumb, logo = GetInfoFromVideoPage(html)    
    
    url_postfix = 'primary_property_tid=' + primary_property_tid + '&primary_property_vid=' + primary_property_vid + '&media_type=' + media_type
    if len(media_season) > 0:
        url_postfix += '&media_season=' + media_season + '&primary_property=' + media_season
        
    for option in html.xpath('//select[@name="field_length_value_many_to_one"]/option'):
        text = option.xpath('./text()')[0]
        value = option.xpath('./@value')[0]
        if value != 'All':
            new_title = title + ' ' + text
            new_url = base_url + '?page=0&field_length_value_many_to_one=' + value + '&' + url_postfix
            if value == 'FullEp':
                oc.add(DirectoryObject(
                    key = Callback(Episode, title=new_title, url=new_url, video_type=value, page_num=0),
                    title = text,
                    thumb = thumb
                ))
            elif value == 'FullMov':
                oc.add(DirectoryObject(
                    key = Callback(Episode, title=new_title, url=new_url, video_type=value, page_num=0),
                    title = text,
                    thumb = thumb
                ))                
            elif value == 'Clip':
                oc.add(DirectoryObject(
                    key = Callback(ClipType, title=new_title, url=new_url, video_type=value, use_property_subchannel=1),
                    title = text,
                    thumb = thumb
                ))            
        
    return oc

####################################################################################################
@route(LT_BASE + '/episodes')
def Episode(title, url, video_type, page_num):

    oc = ObjectContainer(title2=title)
    base_url = url.split('?')[0]
    html = HTML.ElementFromURL(url)
    
    media_type, media_season, primary_property_tid, primary_property_vid, thumb, logo = GetInfoFromVideoPage(html)        
    url_postfix = 'field_length_value_many_to_one=' + video_type + '&primary_property_tid=' + primary_property_tid + '&primary_property_vid=' + primary_property_vid + '&media_type=' + media_type
    if len(media_season) > 0:
        url_postfix += '&media_season=' + media_season + '&primary_property=' + media_season        

    for episode in html.xpath('//div[@class="video-rollover-container-middle-content"]/div[contains(@class, "views-row")]'):
        show = episode.xpath('.//div[@class="video-rollover-container-middle-player-text"]/b/text()')[0].rstrip(":")
        new_url = episode.xpath('.//a/@href')[0]
        description = episode.xpath('.//a/@title')[0]
        summary = re.sub(r'<.*?>', '', description)
        new_thumb = episode.xpath('.//img/@src')[0]
        air_date = episode.xpath('.//div[@class="video-rollover-container-player-timer-text"]/text()')[0].strip()
        originally_available_at = Datetime.ParseDate(air_date).date()
        new_title = episode.xpath('.//img/@title')[0]
        premium = episode.xpath('.//div[@class="video-play-symbol is-premium"]')
        if len(premium) > 0:
            new_title = 'Premium - ' + new_title
        if video_type == 'FullEp':
            season_match = re.search(r'/season-(\d+)/', new_url)
            season = int(season_match.group(1))
            oc.add(EpisodeObject(
                show = show,
                season = season,
                url = new_url,
                title = new_title,
                summary = summary,
                thumb = new_thumb,
                originally_available_at = originally_available_at
            ))
        else:
            oc.add(MovieObject(
                url = new_url,
                title = new_title,
                summary = summary,
                thumb = new_thumb,
                originally_available_at = originally_available_at
            ))            
    
    page = int(page_num)
    max_page = 0
    max_page_element = html.xpath('//li[@class="video-rollover-container-navigation-current"]/text()')
    if max_page_element:
        max_page_match = re.search(r'(\d+)', max_page_element[0])
        if max_page_match:
            max_page = int(max_page_match.group(1))
    
    # Add a Next... entry if applicable.
    if page < max_page - 1:
        page += 1
        new_url = base_url + '?&page=' + str(page) + '&' + url_postfix
        oc.add(NextPageObject(key=Callback(Episode, title=title, url=new_url, video_type=video_type, page_num=str(page)), title='Next ...', thumb = thumb))
        
    return oc

####################################################################################################
@route(LT_BASE + '/cliptypes')
def ClipType(title, url, video_type, use_property_subchannel):

    oc = ObjectContainer(title2=title)
    base_url = url.split('?')[0]    
    html = HTML.ElementFromURL(url)

    media_type, media_season, primary_property_tid, primary_property_vid, thumb, logo = GetInfoFromVideoPage(html)    
    
    url_postfix = 'field_length_value_many_to_one=' + video_type + '&primary_property_tid=' + primary_property_tid + '&primary_property_vid=' + primary_property_vid + '&media_type=' + media_type
    if len(media_season) > 0:
        url_postfix += '&media_season=' + media_season + '&primary_property=' + media_season
    
    property_subchannel = html.xpath('//select[@name="property_subchannel"]')
    if int(use_property_subchannel) and property_subchannel:
        for option in property_subchannel[0].xpath('./option'):
            text = option.xpath('./text()')[0]
            value = option.xpath('./@value')[0]
            if value != 'All':            
                new_title = title + ' ' + text
                new_url = base_url + '?page=0&property_subchannel=' + value + '&' + url_postfix 
                oc.add(DirectoryObject(
                    key = Callback(Clip, title=new_title, url=new_url, video_type=video_type, clip_type=value, page_num=0),
                    title = text,
                    thumb = thumb
                ))
            else:
                new_url = base_url + '?page=0&property_subchannel=' + value + '&' + url_postfix            
                oc.add(DirectoryObject(
                    key = Callback(ClipType, title=title, url=new_url, video_type=video_type, use_property_subchannel=0),
                    title = text,
                    thumb = thumb
                ))              
    else: 
        max_page = 1
        max_page_element = html.xpath('//li[@class="video-rollover-container-navigation-current"]/text()')
        if max_page_element:
            max_page_match = re.search(r'(\d+)', max_page_element[0])
            if max_page_match:
                max_page = int(max_page_match.group(1))
                
        if max_page == 1:
            # If there is only one page of clips just go directly to it.
            # This url should already be cached from the lookup in Season().
            new_title = title + ' Page 1'
            new_url = base_url + '?&page=0&' + url_postfix
            return Clip(title=new_title, url=new_url, video_type=video_type, clip_type=None, page_num=0)
        else:            
            for page in range(max_page):
                page_title = 'Page ' + str(page + 1)
                new_title = title + ' ' + page_title
                new_url = base_url + '?&page=' + str(page) + '&' + url_postfix           
                oc.add(DirectoryObject(
                    key = Callback(Clip, title=new_title, url=new_url, video_type=video_type, clip_type=None, page_num=str(page)),
                    title = page_title,
                    thumb = thumb
                ))  
        
    return oc
 
####################################################################################################
@route(LT_BASE + '/clips')
def Clip(title, url, video_type, clip_type, page_num):

    oc = ObjectContainer(title2=title)
    base_url = url.split('?')[0]
    html = HTML.ElementFromURL(url)

    media_type, media_season, primary_property_tid, primary_property_vid, thumb, logo = GetInfoFromVideoPage(html)
        
    url_postfix = ''
    if clip_type:
        url_postfix = 'property_subchannel=' + clip_type + '&'
    url_postfix += 'field_length_value_many_to_one=' + video_type + '&primary_property_tid=' + primary_property_tid + '&primary_property_vid=' + primary_property_vid + '&media_type=' + media_type
    if len(media_season) > 0:
        url_postfix += '&media_season=' + media_season + '&primary_property=' + media_season        

    for clip in html.xpath('//div[@class="video-rollover-container-middle-content"]/div[contains(@class, "views-row")]'):           
        show = clip.xpath('.//div[@class="video-rollover-container-middle-player-text"]/b/text()')[0].rstrip(":")
        new_url = clip.xpath('.//a/@href')[0]
        description = clip.xpath('.//a/@title')[0]
        summary = re.sub(r'<.*?>', '', description)
        new_thumb = clip.xpath('.//img/@src')[0]
        air_date = clip.xpath('.//div[@class="video-rollover-container-player-timer-text"]/text()')[0].strip()
        originally_available_at = Datetime.ParseDate(air_date).date()
        new_title = clip.xpath('.//img/@title')[0]
        premium = clip.xpath('.//div[@class="video-play-symbol is-premium"]')
        if len(premium) > 0:
            new_title = 'Premium - ' + new_title        
        duration = None
        duration_element = clip.xpath('.//div[@class="video-rollover-container-player-date-text"]')
        if duration_element:
            duration_text = duration_element[0].xpath('./text()')[0].strip()
            duration_match = re.search(r'(\d+)', duration_text)
            if duration_match:
                duration = int(duration_match.group(1)) * MILLISECONDS_IN_A_MINUTE
                
        oc.add(VideoClipObject(
            url = new_url,
            title = new_title,
            summary = summary,
            thumb = new_thumb,
            originally_available_at = originally_available_at,
            duration = duration
        ))          

    if clip_type:
        page = int(page_num)        
        max_page = 0
        max_page_element = html.xpath('//li[@class="video-rollover-container-navigation-current"]/text()')
        if max_page_element:
            max_page_match = re.search(r'(\d+)', max_page_element[0])
            if max_page_match:
                max_page = int(max_page_match.group(1))
        
        # Add a Next... entry if applicable.
        if page < max_page - 1:
            page += 1
            new_url = base_url + '?&page=' + str(page) + '&' + url_postfix
            oc.add(NextPageObject(key=Callback(Clip, title=title, url=new_url, video_type=video_type, clip_type=clip_type, page_num=str(page)), title='Next ...', thumb = thumb))
        
    return oc
