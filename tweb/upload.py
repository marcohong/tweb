import os
from urllib.parse import urlparse
from typing import Optional, Union
from tornado import httputil

from . import files
from tweb.utils.attr_util import AttrDict
from tweb.utils import strings
from tweb.utils.log import logger

# default upload image max pixel 1920x1080
MAX_IMG_PIXEL = (6000, 4000)
# default upload video max pixel 1920x1080
MAX_VIDEO_PIXEL = (3840, 2160)


class Upload:
    '''
    Tronado upload classes.

    Redis reserve key name see default_config keys.


    use redis config, rewrite classmethod::

    class MyUpload(Upload):
        @classmethod
        async def get_image_conf(cls) -> tuple:
            pass
        @classmethod
        async def get_video_conf(cls) -> tuple:
            pass
        @classmethod
        async def incr_number(cls) -> str:
            pass
        @classmethod
        async def get_value(cls, key_: str) -> Optional[str]:
            pass

    '''
    default_config = {
        'statics':
        '/static',
        'access:url':
        'http://localhost:8888',
        'upload:file:number':
        1,
        'image:upload:path':
        os.path.join(strings.get_root_path(), 'upload', 'images'),
        'image:upload:max:size':
        '26485760',  # 25MB
        'image:upload:fmt':
        'jpg,jpeg,png,gif',
        'video:upload:path':
        os.path.join(strings.get_root_path(), 'upload', 'video'),
        'video:upload:max:size':
        '104857600',  # 100MB
        'video:upload:fmt':
        'avi,wmv,mpeg,mp4,mov,mkv,flv,f4v,m4v,rmvb,rm,ts,mts'
    }

    @classmethod
    async def get_image_conf(cls) -> tuple:
        '''Rewrite'''
        return cls.default_config['image:upload:path'], cls.default_config[
            'image:upload:max:size'], cls.default_config['image:upload:fmt']

    @classmethod
    async def get_video_conf(cls) -> tuple:
        '''Rewrite'''
        return cls.default_config['video:upload:path'], cls.default_config[
            'video:upload:max:size'], cls.default_config['video:upload:fmt']

    @classmethod
    async def incr_number(cls) -> str:
        '''Rewrite'''
        cls.default_config['upload:file:number'] += 1
        return f"{cls.default_config['upload:file:number']}"

    @classmethod
    async def get_value(cls, key_: str) -> Optional[str]:
        '''Rewrite'''
        return cls.default_config.get(key_)

    @classmethod
    async def get_access_url(cls) -> str:
        return await cls.get_value('access:url')

    @classmethod
    async def get_img_upload_path(cls, classify: str) -> Optional[str]:
        _path = await cls.get_value('image:upload:path')
        return os.path.join(_path, classify)

    @classmethod
    async def get_video_upload_path(cls, classify: str) -> Optional[str]:
        _path = await cls.get_value('video:upload:path')
        return os.path.join(_path, classify)

    @classmethod
    async def get_image_classify(cls,
                                 access_path: str,
                                 append: Union[str, list] = None) -> str:
        '''Return format image path classify.

        If path access is not W_OK or not path, return ''.

        :param access_path: `<str>` e.g:
                images/users/logo
            or  /data/upload/images/users/logo
        :param append: `<str/list>` suffix, if append used def fmt_classify()
        '''
        url = urlparse(access_path)
        if not url.path or url.path == '/':
            return cls.fmt_classify(append) if append else ''
        # statics eg: /static,/images --> ['/static','/images'],
        # if not statics, used default ['/static']
        statics = await cls.get_value('statics')
        statics = statics.split(',')
        result = cls._get_path_suffix(url.path, statics)
        if append:
            append = append if isinstance(append, list) else [append]
            append.insert(0, result)
            return cls.fmt_classify(append)
        else:
            return result[1:] if result.startswith('/') else result

    @staticmethod
    def _get_path_suffix(path: str, statics: list) -> str:
        if not path:
            return ''
        for static in statics:
            if path.startswith(static):
                return path[len(static):]
        return path[1:]

    @staticmethod
    def fmt_classify(dirs: list) -> str:
        '''
        :param dirs: `<list>` eg. ['article','2018/10/10']
        '''
        if isinstance(dirs, list):
            url = '/'.join(dirs)
        else:
            url = dirs
        if url.startswith('/'):
            url = url[1:]
        return url if os.access(url, os.W_OK) else ''

    @classmethod
    async def upload_image(
            cls,
            request: httputil.HTTPServerRequest,
            name: str,
            max_pixel: tuple = MAX_IMG_PIXEL,
            classify: str = 'tmp',
            fetchone: bool = True,
            access_url: str = None) -> Optional[Union[dict, list]]:
        '''
        Upload image. If it returns an error message, it is
        internationalized content (message.po)

        :param request: `<httputil.HTTPServerRequest>`
        :param name: `<str>` form params name
        :param max_pixel: `<tuple>` image max pixel
        :param classify: `<str>` classify
        :param fetchone: `<bool>` default get first file,
            if fetchone false return all
        :param access_url: `<str>` base access url
        :return: `<AttrDict>`
            status(if status is False, only return message and status)
            origin_name
            file_path
            access_path
            message(error message)
        '''
        datas = []
        # upload_path: base_upload_url + classify,
        # eg. base url: /data/images
        # /data/images/users
        _path, max_size, fmt = await cls.get_image_conf()
        upload_path = os.path.join(_path, classify)
        file_names = files.get_up_file_name(request, name, fetchone=fetchone)
        max_size = int(max_size)
        if not access_url:
            access_url = await cls.get_access_url()
        if fetchone:
            file_names = [file_names]
        for idx, fname in enumerate(file_names):
            suffix = files.get_file_suffix(fname)
            if suffix[1:].lower() not in fmt.split(','):
                logger.warning('[%s]image format is not supported' % suffix)
                return AttrDict(
                    dict(status=False,
                         message='Image format is not supported'))
            number = await cls.incr_number()
            new_name = '%s%s' % (strings.get_now_date(fmt='%Y%m%d%H%M%S'),
                                 number.zfill(6))
            file_path = files.upload(request,
                                     name,
                                     upload_path,
                                     index=idx,
                                     new_name=new_name)
            image_pixel = files.get_image_pixel(file_path)
            if max_pixel[0] < image_pixel[0] or max_pixel[1] < image_pixel[1]:
                files.rm_file(file_path)
                return AttrDict(
                    dict(status=False, message='Image pixel is too large'))
            if files.get_file_size(file_path) > max_size:
                files.rm_file(file_path)
                return AttrDict(
                    dict(status=False, message='Image size is too large'))
            access_path = os.path.join(access_url, 'images', classify,
                                       os.path.basename(file_path))
            datas.append(
                AttrDict(
                    dict(status=True,
                         file_path=file_path,
                         origin_name=fname,
                         access_path=access_path)))
        return datas[0] if fetchone else datas

    @classmethod
    async def upload_video(
            cls,
            request: httputil.HTTPServerRequest,
            name: str,
            classify: str = 'tmp',
            fetchone: bool = True,
            access_url: str = None) -> Optional[Union[dict, list]]:
        '''
        Upload video. If it returns an error message, it is
        internationalized content (message.po)

        :param request: `<httputil.HTTPServerRequest>`
        :param name: `<str>` form params name
        :param classify: `<str>` classify
        :param fetchone: `<bool>` default get first file,
            if fetchone false return all
        :param access_url: `<str>` base access url
        :return: `<AttrDict>`
            status(if status is False, only return message and status)
            origin_name
            file_path
            access_path
            message(error message)
        '''
        datas = []
        _path, max_size, fmt = await cls.get_image_conf()
        upload_path = os.path.join(_path, classify)
        file_names = files.get_up_file_name(request, name, fetchone=fetchone)
        max_size = int(max_size)
        if not access_url:
            access_url = await cls.get_access_url()
        if fetchone:
            file_names = [file_names]
        if int(request.headers.get('Content-Length')) > max_size:
            size = int(max_size / 1024 / 1024)
            _msg = 'Temporarily not uploading files over %sM' % size
            logger.warning(_msg)
            return AttrDict(dict(status=False, message=_msg))
        for idx, fname in enumerate(file_names):
            suffix = files.get_file_suffix(fname)
            if suffix[1:].lower() not in fmt.split(','):
                logger.warning('[%s]video format is not supported' % suffix)
                return AttrDict(
                    dict(status=False,
                         message='Video format is not supported'))
            number = await cls.incr_number()
            new_name = '%s%s' % (strings.get_now_date(fmt='%Y%m%d%H%M%S'),
                                 number.zfill(6))
            file_path = files.upload(request,
                                     name,
                                     upload_path,
                                     index=idx,
                                     new_name=new_name)
            access_path = os.path.join(access_url, 'video', classify,
                                       os.path.basename(file_path))
            datas.append(
                AttrDict(
                    dict(status=True,
                         file_path=file_path,
                         origin_name=fname,
                         access_path=access_path)))
        return datas[0] if fetchone else datas
