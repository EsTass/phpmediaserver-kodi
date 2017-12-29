# -*- coding: utf-8 -*-
# Module: default
# Author: Tass
# Created on: 20-12-2017
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import json

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

#OWN PHPMEDIASERVER
'''
{
    'Category': [
        {
            'name' => 'title',
            'plot' => 'plot',
            'year' => 'year',
            'season' => 'season',
            'episode' => 'episode',
            'thumb' => 'url',
            'landscape' => 'url',
            'banner' =>  'banner',
            'video' => 'video',
            'genre' => 'genres',
        },
        ...
    ],
    ...
}
'''

def is_json(myjson):
  try:
    json_object = json.loads(myjson)
  except ValueError, e:
    return False
  return True

def extract_text(s, leader, trailer):
    end_of_leader = s.index(leader) + len(leader)
    start_of_trailer = s.index(trailer, end_of_leader)
    return s[end_of_leader:start_of_trailer]

def login():
    result = False
    PHPSESSION = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "phpsession" )
    USERNAME = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "username" )
    PASSWORD = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "password" )
    url = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "url" )

    if check_session() == False:
        payload = {'r' : 'r', 'action' : 'login', 'user': USERNAME, 'pass': PASSWORD}

        s = requests.session()

        # POST with form-encoded data
        r = s.post(url, data=payload, verify=False)

        # Response, status etc
        #print( r.text.encode('unicode-escape') )
        #print( r.status_code.encode('unicode-escape') )

        for cookie in r.cookies:
            #print (cookie.name, cookie.value)
            PHPSESSION = cookie.value
            xbmcaddon.Addon('plugin.video.phpmediaserver').setSetting( id="phpsession", value=str(PHPSESSION) )
            result = True
    else:
        result = True
    
    return result

def check_session():
    result = False
    
    PHPSESSION = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( id="phpsession" )
    url = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "url" )
    
    if len( PHPSESSION ) > 0:
        payload = { 'r' : 'r', 'action' : 'kodi', 'saction': 'check', 'PHPSESSION': PHPSESSION }
        s = requests.session()

        # GET with params in URL
        r = s.get(url, params=payload, verify=False)
        if is_json( r.text ):
            data = json.loads(r.text)
            if 'login' in data and data['login'] == True:
                result = True
        
    return result


def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            # Must be encoded in UTF-8
            v.decode('utf8')
        out_dict[k.encode('utf8')] = v
    return out_dict

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs, 'utf-8'))

def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    
    result = False
    PHPSESSION = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "phpsession" )
    url = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "url" )
    
    payload = { 'r' : 'r', 'action' : 'kodi', 'saction': 'categories', 'PHPSESSION': PHPSESSION }
    s = requests.session()

    # GET with params in URL
    r = s.get(url, params=payload, verify=False)
    if is_json( r.text ):
        data = json.loads(r.text)
        if len( data ) <= 0:
            result = False
            xbmcgui.Dialog().notification( 'Categories Error', 'Error in category list 1.', xbmcgui.NOTIFICATION_ERROR )
        else:
            create_folders( data )
    else:
        result = False
        xbmcgui.Dialog().notification( 'Categories Error', 'Error in category list 2.', xbmcgui.NOTIFICATION_ERROR )
        
    return result

def create_folders( data ):
    
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'phpmediaserver')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get video categories
    categories = data
    # Iterate through categories
    for category in categories:
        category = category.encode( 'utf8' )
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        #list_item.setArt({'thumb': VIDEOS[category][0]['thumb'],
        #                  'icon': VIDEOS[category][0]['thumb'],
        #                  'fanart': VIDEOS[category][0]['landscape']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': category, 'genre': category})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', category=category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_videos(category):
    """
    Create the list of playable videos in the Kodi interface.

    :param category: Category name
    :type category: str
    """
    
    result = False
    
    #UPDATE
    if category.startswith( '*' ):
        list_categories()
        pass
    
    #SERIES
    if category.startswith( '+' ):
        PHPSESSION = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "phpsession" )
        url = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "url" )
        payload = { 'r' : 'r', 'action' : 'kodi', 'saction': 'series', 'PHPSESSION': PHPSESSION }
        s = requests.session()
        # GET with params in URL
        r = s.get(url, params=payload, verify=False)
        data = json.loads(r.text)
        if len( data ) <= 0:
            result = False
            xbmcgui.Dialog().notification( 'Series Error', 'Error in data 1.', xbmcgui.NOTIFICATION_ERROR )
            return result
        else:
            create_folders( data )
        pass
    
    #SEARCH
    if category.startswith( '-' ):
        PHPSESSION = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "phpsession" )
        url = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "url" )
        search = xbmcgui.Dialog().input( category )
        payload = { 'r' : 'r', 'action' : 'kodi', 'saction': 'search', 'PHPSESSION': PHPSESSION, 'search': search }
        s = requests.session()
        # GET with params in URL
        r = s.get(url, params=payload, verify=False)
        data = json.loads(r.text)
        if len( data ) <= 0:
            result = False
            xbmcgui.Dialog().notification( 'Search Error', 'Error in search 1.', xbmcgui.NOTIFICATION_ERROR )
            return result
        else:
            videos = data
    else:
        PHPSESSION = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "phpsession" )
        url = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "url" )
        
        payload = { 'r' : 'r', 'action' : 'kodi', 'saction': 'category', 'cat': category, 'PHPSESSION': PHPSESSION }
        s = requests.session()

        # GET with params in URL
        r = s.get(url, params=payload, verify=False)
        data = json.loads(r.text)
        if len( data ) <= 0:
            result = False
            xbmcgui.Dialog().notification( 'Categories List Error', 'Error in category list 1.', xbmcgui.NOTIFICATION_ERROR )
            return result
        videos = data
        
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, category)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Iterate through videos.
    for video in videos:
        video = encoded_dict( video )
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['name'])
        # Set additional info for the list item.
        #list_item.setInfo('video', {'title': video['name'], 'genre': video['genre']})
        list_item.setInfo('video', {'title': video['name'], 'genre': video['genre'], 'plot': video['plot'], 'year': video['year'], 'season': video['season'], 'episode': video['episode']})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['landscape'], 'banner': video['banner']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        url = get_url(action='play', video=video['video'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        result = True
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)
    
    return result

def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
    
    xbmc.sleep(1000)
    
    time = 0
    while xbmc.Player().isPlaying():
        time = xbmc.Player().getTime()
        xbmc.sleep(1000)
    
    if time > 0:
        timetotal = 0
        PHPSESSION = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "phpsession" )
        url = xbmcaddon.Addon('plugin.video.phpmediaserver').getSetting( "url" )
        s = requests.session()
        urltime = url
        payload = { 'r' : 'r', 'action' : 'playstop', 'timeplayed' : int( time ), \
            'timetotal' : int( timetotal ), 'idmedia' : extract_text( path, 'idmedia=', '&' ),\
            'PHPSESSION' : PHPSESSION
                }
        r = s.get(url, params=payload, verify=False)
        

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    
    if login()  == False:
        xbmcgui.Dialog().notification( 'Login error', 'Error login to server, change config.', xbmcgui.NOTIFICATION_ERROR )
        return True
    
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_videos(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
