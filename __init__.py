from .nodes import HotelShowPrepare, HotelShowRender

NODE_CLASS_MAPPINGS = {'HotelShowPrepare': HotelShowPrepare, 'HotelShowRender': HotelShowRender}
NODE_DISPLAY_NAME_MAPPINGS = {
    'HotelShowPrepare': 'HotelShow · 多图整理 / ZIP',
    'HotelShowRender': 'HotelShow · 酒店图文精确排版',
}
WEB_DIRECTORY = './web'

# Upload support is optional on hosted platforms. Native LoadImage inputs still work.
try:
    from . import upload
except ImportError:
    pass
