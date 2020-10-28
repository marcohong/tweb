import os
import hashlib
from typing import Optional, Tuple, Any, Union
from PIL import Image, ImageDraw
from tornado import httputil

from tweb.utils import strings
from tweb.utils.font import DefaultFont
from tweb.utils.log import logger


def up_has_file(request: httputil.HTTPServerRequest, name: str) -> bool:
    '''
    判断是否有文件上传

    :param request: `<RequestHandler>` tornado request
    :param name: `<str>` 获取的文件名
    '''
    if request.files and request.files.get(name):
        return True
    return False


def up_file_count(request: httputil.HTTPServerRequest, name: str) -> int:
    '''
    获取上传文件数量

    :param request: `<RequestHandler>` tornado request
    :param name: `<str>` 获取的文件名
    '''
    files = request.files
    if files and files.get(name):
        return len(files.get(name))
    return 0


def up_file_in_types(request: httputil.HTTPServerRequest,
                     name: str,
                     types: list,
                     index: int = 0) -> bool:
    '''
    检测文件后缀是否在指定的列表范围内

    :param request: `<RequestHandler>` tornado request
    :param name: `<str>` 获取的文件名
    :param types: `<list>` 允许的文件类型列表
    :param index: `<int>` 默认获取第一个文件
    :returns: `<bool>` 如果存在返回True 否则返回False
    '''
    files = request.files
    if files and files.get(name):
        suffix = os.path.splitext(files.get(name)[index]['filename'])[1]
        if suffix[1:].lower() in types:
            return True
    return False


def get_up_file_name(request: httputil.HTTPServerRequest,
                     name: str,
                     fetchone: bool = True) -> Optional[Union[list, str]]:
    '''
    获取上传文件的文件名

    :param request: `<RequestHandler>` tornado request
    :param name: `<str>` 获取的文件名
    :param fetchone: `<bool>` 是否返回第一个文件名 默认是
    :return: `<str/list>`
    '''
    files = request.files
    if files and files.get(name):
        if fetchone:
            return files.get(name)[0]['filename']
        return [obj['filename'] for obj in files.get(name)]
    return None


def upload(request: httputil.HTTPServerRequest,
           name: str,
           path: str,
           index: int = 0,
           new_name: str = None,
           random_name: bool = True) -> Optional[str]:
    '''
    单文件上传

    :param request: `<RequestHandler>` tornado request
    :param name: `<str>` 获取的文件名
    :param path: `<str>` 保存路径
    :param index: `<int>` 默认获取第一个文件
    :param new_name: `<str>` 新命名(优先随机名random_name)
    :param random_name: `<bool>` 使用随机名
    '''
    files = request.files
    if not files or not files.get(name):
        return None
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            logger.error('Can not create upload path.')
            return None

    _file = files.get(name)[index]
    if new_name:
        suffix = os.path.splitext(_file['filename'])[1]
        filename = new_name + suffix
    elif not new_name and random_name:
        new_name = strings.get_file_name()
        suffix = os.path.splitext(_file['filename'])[1]
        filename = new_name + suffix
    else:
        filename = _file['filename']
    file_path = os.path.join(path, filename)
    with open(file_path, 'wb') as _fp:
        _fp.write(_file['body'])
    return file_path


def rm_file(path: str) -> None:
    '''
    删除文件
    '''
    if not os.path.exists(path):
        return
    if os.path.isfile(path) and os.access(path, os.W_OK):
        os.unlink(path)


def mv_file(old: str, new: str) -> None:
    '''
    重命名文件
    :param old: `<str>` 旧文件路径
    :param new: `<str>` 新文件路径
    '''
    if not os.path.exists(old) or not os.access(old, os.W_OK):
        return
    if not os.path.isdir(os.path.dirname(new)) or not os.access(new, os.W_OK):
        return
    os.rename(old, new)


def get_file_name(path: str, suffix: bool = False) -> str:
    '''
    获取文件名，默认不包括后缀
    :returns: str
    '''
    base_name = os.path.basename(path)
    if not suffix:
        return os.path.splitext(base_name)[0]
    else:
        return base_name


def get_file_suffix(path: str) -> str:
    '''
    获取文件后缀(包含.)
    '''
    base_name = os.path.basename(path)
    return os.path.splitext(base_name)[1]


def get_file_size(path: str) -> Optional[int]:
    '''
    获取文件的大小(bytes)
    :returns: None or <int> size
    '''
    if not os.path.exists(path):
        return None
    return os.path.getsize(path)


def get_file_md5(path: str) -> str:
    '''
    获取文件的md5值

    :param path: `<str>`
    :return:
    '''
    st_size = get_file_size(path)
    m = hashlib.md5()
    with open(path, 'rb') as _f:
        if int(st_size) / (1024 * 1024) >= 100:
            while 1:
                data = _f.read(8096)
                if not data:
                    break
                m.update(data)
        else:
            m.update(data)
    return m.hexdigest()


def get_file_create_time(path: str) -> str:
    '''
    获取文件的创建时间
    :returns: `<str>`
    '''
    atime = os.path.getctime(path)
    return strings.timestamp_to_time(atime)


def get_file_access_time(path: str) -> str:
    '''
    获取文件的访问时间
    :returns: `<str>`
    '''
    atime = os.path.getatime(path)
    return strings.timestamp_to_time(atime)


def get_file_modify_time(path: str) -> str:
    '''
    获取文件的修改时间
    :returns: `<str>`
    '''
    atime = os.path.getmtime(path)
    return strings.timestamp_to_time(atime)


def get_image_pixel(path: str) -> Tuple[int, int]:
    '''
    获取图片像素
    :returns: `<tuple>` (width,height)
    '''
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    return img.size


def thumbnail_image(path: str,
                    output: str,
                    width: int = 128,
                    height: int = 128) -> str:
    '''
    缩略图
    :param path: `<str>` 源图片路径
    :param output: `<str>` 输出路径
    :param width: `<int>`
    :param height: `<int>`
    '''
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    img.thumbnail((width, height))
    img.save(output)
    return output


def compress_image(path: str,
                   output: str,
                   width: int = None,
                   height: int = None,
                   quality: int = 80,
                   **kwargs: Any) -> str:
    '''
    按比例压缩图片，添加字体水印或图片水印(建议png)
    :param path: `<str>` 源图片路径
    :param output: `<str>` 输出路径
    :param width: `<int>`
    :param height: `<int>`
    :param quality: `<int>` 压缩质量，最大100
    :param water_mark: `<str>` 水印内容，文字或图片，默认没有水印
    :param water_opt: `<str>` 水印位置 leftup/rightup/leftlow/rightlow
    :param ratio: `<bool>` 等比压缩，默认True
    :param ratio_scale: `<int>` 等比压缩比例，默认不压缩，1/2 2, 1/3 3, 1/4 4...
    :param font_size: `<int>` 如果设置文字水印，则需要设置文字的字体大小，默认20
    :param opacity: `<int>` 水印的透明度，默认1
    '''
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    ori_w, ori_h = img.size
    # 等比压缩处理
    if width and height and not kwargs.get('ratio', True):
        # 非等比压缩 图片过小不能拉伸
        if width > ori_w and height > ori_h:
            width = width
            height = height
        else:
            width = ori_w
            height = ori_h
    elif (width and ori_w > width) or (height and ori_h > height):
        ratio_val = 1
        ratio_h = ratio_w = None
        if width and ori_w > width:
            ratio_w = float(width) / ori_w
        if height and ori_h > height:
            ratio_h = float(height) / ori_h

        if ratio_w and ratio_h:
            ratio_val = min([ratio_h, ratio_w])
        else:
            ratio_val = ratio_w or ratio_h or 1
        width = int(ori_w * ratio_val)
        height = int(ori_h * ratio_val)
    else:
        # 获取等比压缩比例，默认不压缩
        ratio_scale = kwargs.get('ratio_scale', 1)
        # 判断是否使用等比压缩，默认是True
        if not kwargs.get('ratio', True):
            ratio_scale = 1
        width = int(ori_w / ratio_scale)
        height = int(ori_h / ratio_scale)
    img = img.resize((width, height), Image.ANTIALIAS)
    # 水印处理，如果water_mark参数不为空，增加水印(水印可以是文字或图片)，
    # 获取水印位置，默认位置在右下方
    water_mark = kwargs.get('water_mark')
    if water_mark:
        new_img = process_water_mark(img.size, kwargs)
        # 保存图片
        Image.composite(new_img, img, new_img).save(output, quality=quality)
    else:
        img.save(output, quality=quality)
    return output


def process_water_mark(ori_size: Tuple[int, int], kwargs: dict) -> "Image":
    '''
    处理水印
    '''
    water_mark = kwargs.get('water_mark')
    if not os.path.exists(water_mark):
        # 文字水印处理
        font = DefaultFont().truetype(size=kwargs.get('font_size', 20))
        # font = ImageFont.truetype('Arial.ttf', kwargs.get('font_size', 20))
        new_img = Image.new('RGBA', ori_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(new_img)
        mark_opt = get_mark_opt(new_img.size, font.getsize(water_mark),
                                kwargs.get('water_opt', 'rightlow'))
        draw.text(mark_opt, water_mark, font=font, fill=(255, 255, 255, 255))
        # 处理透明度，暂时不生效
        # new_img = new_img.rotate(23, Image.BICUBIC)
        # alpha = new_img.split()[3]
        # alpha .Brightness(alpha).enhance(0.6)
        # new_img.putalpha(alpha)
    else:
        logo = Image.open(water_mark)
        new_img = Image.new('RGBA', ori_size, (0, 0, 0, 0))
        mark_opt = get_mark_opt(ori_size, logo.size,
                                kwargs.get('water_opt', 'rightlow'))
        new_img.paste(logo, mark_opt)
    return new_img


def get_mark_opt(ori_size: Tuple[int, int], size: Tuple[int, int],
                 water_opt: dict) -> dict:
    ori_w, ori_h = ori_size
    # 距离边框10个像素
    mark_w, mark_h = map(lambda x: x + 10, size)
    option = {
        'leftup': (10, 10),
        'rightup': (ori_w - mark_w, 10),
        'leftlow': (10, ori_h - mark_h),
        'rightlow': (ori_w - mark_w, ori_h - mark_h)
    }
    return option.get(water_opt, (ori_w - mark_w, ori_h - mark_h))
