import os
from PIL import ImageFont

from tweb.utils.single import SingleClass
__all__ = ['DefaultFont']

TWEB_ROOT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


class DefaultFont(SingleClass):

    font: str = None

    def config_font(self, font: str = None) -> None:
        '''
        Font

        :param font: `<str>` font full path
        :return:
        '''
        if not font:
            font = os.path.join(TWEB_ROOT_PATH, 'tweb', 'fonts',
                                'SourceHanSansSC-Normal.otf')
        self.font = font

    def get_font(self) -> str:
        if self.font is None:
            self.config_font()
        return self.font

    def truetype(self,
                 size: int = 32,
                 index: int = 0,
                 encoding: str = '',
                 layout_engine: int = None) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(self.get_font(),
                                  size=size,
                                  index=index,
                                  encoding=encoding,
                                  layout_engine=layout_engine)
