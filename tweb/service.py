'''
Base service class.
'''
import peewee
from typing import Any, Union
from tweb.database.paginate import pager
from tweb.exceptions import NotFoundError
from tweb.utils import strings

# Default page=1 and limit=20
DEF_PAGE, DEF_LIMIT = 1, 20
IGNORES = Union[None, str, list, tuple]
NULL_VALUES = (None, '')


def st_filter(obj: peewee.Model, value: int) -> Any:
    '''
    Filter status

    :param obj: `<peewee.model>` eg: Menu
    :param value: `<int>`
    '''
    if value is not None:
        return obj.status == value
    return obj.status != value


def in_or_eq(field: peewee.Field, value: Any, not_in: bool = False) -> bool:
    '''
    Processing in or equal

    :param field: `<peewee.field>` column
    :param value: `<list/tuple/str>`
    :param not_in: `<bool>` True/False default False
    '''
    if isinstance(value, (list, tuple)):
        return field.not_in(value) if not_in else field << value
    return field != value if not_in else field == value


def not_in(field: peewee.Field, value: Any) -> bool:
    '''
    Processing query not in

    :param field: `<peewee.field>` column
    :param value: `<list/tuple/str>`
    '''
    return in_or_eq(field, value, True)


def like(lst: list,
         field: peewee.Field,
         query: dict,
         name: str = None) -> None:
    '''
    Append fuzzy query condition.

    :param lst: `<list>` query list
    :param field: `<peewee.field>` query columns
    :param query: `<dict>` query params
    :param name: `<str>` parameter name，default column name
    '''
    result = query.get(name if name else field.name)
    if result not in NULL_VALUES and isinstance(lst, list):
        if result.startswith('%') or result.endswith('%'):
            lst.append(field**result)
        else:
            lst.append(field**f'{result}%')


def _fn_filter_over(obj: peewee.Query,
                    alias: str,
                    query: tuple = None,
                    over: Any = None):
    if query:
        if len(query) == 1:
            obj = obj.filter(query)
        else:
            obj = obj.filter(*tuple(query))
    if over:
        return obj.over(over).alias(alias)
    return obj.over().alias(alias)


def fn_sum(field: peewee.Field,
           alias: str,
           query: tuple = None,
           over: Any = None):
    '''
    sum by condition(pg)

    :param field: `<peewee.field>` query column
    :param alias: `<str>` alias name
    :param query: `<tuple>` query param, eg: (Admin.id==1,)
    :param over: `<Any>` over
    :return:
    '''
    data = peewee.fn.SUM(field)
    return _fn_filter_over(data, alias, query, over)


def fn_count(field: peewee.Field,
             alias: str,
             query: tuple = None,
             over: Any = None):
    '''
    count by condition(pg)

    :param field: `<peewee.field>` query column
    :param alias: `<str>` alias name
    :param query: `<tuple>` query param, eg: (Admin.id==1,)
    :param over: `<Any>` over
    :return:
    '''
    data = peewee.fn.COUNT(field)
    return _fn_filter_over(data, alias, query, over)


def case_when(query: str, field: str) -> peewee.SQL:
    '''MySQL case when.
    '''
    return peewee.SQL(f'CASE WHEN {query} THEN {field} END')


def ordering(order: Union[str, tuple], model: peewee.Model) -> tuple:
    '''
    Process sql order by.

    :param order: `<str/tuple>` order string

        e.g::
            order = 'id desc,mtime asc'
            # or
            order = (-User.id, User.mtime)
    :param model: `<peewee.model>`
    '''
    if isinstance(order, str):
        _order = []
        orders = order.split(',')
        for obj in orders:
            item = obj.split()
            key, val = (item[0], 'desc') if len(item) == 1 else item
            if not hasattr(model, key):
                continue
            if val.strip().lower() == 'desc':
                _order.append(getattr(model, key).desc())
            else:
                _order.append(getattr(model, key).asc())
        _order = tuple(_order)
    else:
        _order = order
    if not _order:
        return None
    _order = _order if len(_order) > 1 else (_order[0], )
    return _order


def filter_fields(model: peewee.Model, ignores: Union[str, list]) -> tuple:
    '''Filter ignores fields.

    :param model: `<peewee.model>`
    :param ignores: `<list>` ignore columns
    return: `<tuple>`
    '''
    if not ignores:
        ignores = []
    if isinstance(ignores, str):
        ignores = [ignores]
    keys = list(model._meta.fields.keys())
    fields = list(set(keys).difference(ignores))
    return tuple([getattr(model, field) for field in fields])


def fmt_data(datas: peewee.Model,
             ignores: list = None,
             fmt: bool = True) -> Union[peewee.Model, list]:
    '''
    Format data to dict.

    :param datas: `<peewee.model>`
    :param ignores: `<list>` ignore columns
    :param fmt: `<bool>` format default True
    '''
    if fmt is False:
        return datas
    # return [model_to_dict(data) for data in datas]
    return [data.get_dict(ignores) for data in datas]


class BaseService(object):
    def __init__(self, empty: peewee.Model) -> None:
        self.empty = empty

    def is_db_col(self, key):
        if hasattr(self.empty, key):
            field = getattr(self.empty, key)
            if isinstance(field, peewee.Field):
                return True
        return False

    def find_by_id(self, pk: Union[int, str]) -> peewee.Model:
        if not pk:
            return None
        return self.empty.fetchone(self.empty._meta.primary_key == pk)

    def get_or_404(self, pk: Union[int, str]) -> peewee.Model:
        data = self.find_by_id(pk)
        if not data:
            raise NotFoundError
        return data

    def find_by_condition(self, *query: Any, **kwargs: Any) -> peewee.Model:
        data = self.empty.fetchone(*query, **kwargs)
        return data

    def find(self, pk: int = None, **columns: Any) -> peewee.Model:
        '''
        Find obj by id or others columns
        usage::

        def get_user(pk:int,columns:dict):
            return self.find(pk=pk, name=columns['username'],
                    email=columns['email'])

        :param : `<str>`
        :return:
        '''
        if pk:
            return self.find_by_id(pk)
        return self.find_by_condition(**columns)

    def save(self, **cloumns: Any) -> int:
        '''
        Save data

        :param columns: `<dict>`
        :raise OperateError:
        :return: `<int>`
        '''
        return self.empty.create(**cloumns)

    def update(self, pk: Union[int, str], **columns: Any) -> int:
        return self.empty.update(**columns).where(
            self.empty.id == pk).execute()

    def updates(self, pks: list, **columns: Any) -> int:
        if not isinstance(pks, (list, tuple)):
            pks = [pks]
        return self.empty.update(
            **columns).where(self.empty.id << pks).execute()

    def save_or_update(self, columns: dict, pk: int = None) -> int:
        '''
        Save or update

        :param columns: `<dict>`
        :param pk: `<int>`
        :raise OperateError:
        :return:
        '''
        if pk is None or pk == 0:
            return self.save(**columns)
        else:
            # self.get_or_404(pk)
            return self.update(pk, **columns)

    def delete(self, ids: Union[int, str, list]) -> int:
        if not isinstance(ids, list):
            ids = [ids]
        return self.empty.delete().where(self.empty.id << ids).execute()

    def assert_exist(self, pks: Union[int, list, tuple]) -> None:
        '''
        Check data exists.

        :param pks: `<int/list>` primary_key
        :raise NotFoundError:
        :return:
        '''
        flag = self.exist(pks)
        if not flag:
            raise NotFoundError

    def exist(self, pk: Union[int, list, tuple]) -> bool:
        if isinstance(pk, (list, tuple)):
            length = len(pk)
            query = (self.empty._meta.primary_key << pk, )
        else:
            length = 1
            query = (self.empty._meta.primary_key == pk, )
        return True if self.count(query) == length else False

    def key_exist(self, column: str, value: Any) -> bool:
        _count = self.count((getattr(self.empty, column) == value, ))
        return True if _count else False

    def count(self, query: tuple = None) -> int:
        data = self.empty.select()
        if query and isinstance(query, tuple):
            if len(query) > 1:
                data = data.where(*query)
            else:
                data = data.where(query[0])
        return data.count()

    def count_field(self, field: str, value: Any) -> int:
        return self.count((getattr(self.empty, field) == value, ))

    def find_all(self,
                 query: tuple = None,
                 order: Union[str, tuple] = None,
                 ignores: Union[str, list] = None,
                 fmt: bool = True) -> Union[peewee.Model, list]:
        '''
        :param query: `<tuple>` query condition
        :param order: `<tuple>` order by
        :param ignores: `<list>` ignore columns
        :param fmt: `<bool>` format default True
        '''
        if not ignores:
            data = self.empty.select()
        else:
            fields = filter_fields(self.empty, ignores)
            data = self.empty.select(*fields)
        data = self._where(data, query)
        if order and isinstance(order, (str, tuple)):
            order = ordering(order, self.empty)
            if order:
                data = data.order_by(*order)
        return fmt_data(data, None if ignores else ignores, fmt)

    def find_by_page(self,
                     page: int = DEF_PAGE,
                     limit: int = DEF_LIMIT,
                     order: Union[None, tuple] = None,
                     ignores: Union[None, list] = None,
                     fks: Union[None, dict] = None,
                     **kwargs: Any) -> dict:
        '''
        分页查询
        :param page: `<int>` 页数 默认第1页
        :param limit: `<int>` 一页返回多少条记录 默认20
        :param order: `<tuple>` 排序
        :param ignores: `<list>` 忽略的字段
        :param fks: `<dict>` 外键自带值
        :param kwargs: 查询的字段(自定义) 查看self._query(query)方法定义
        :returns: `<dict>`
        '''
        query = self._query(kwargs, self.empty)
        if not query:
            query = []
        data = self.find_all(query=tuple(query),
                             order=order,
                             ignores=ignores,
                             fmt=False)
        return self.pager(data,
                          page=page,
                          limit=limit,
                          order=order,
                          fks=fks,
                          **kwargs)

    def _query(self, query: dict, obj: peewee.Model) -> list:
        '''Query filter

        User-defined query filter condition.

        :param query: `<dict>` query
        :param obj: `<peewee.model>` obj
        '''
        pass

    def _where(self, data: peewee.Model, query: Union[tuple,
                                                      list]) -> peewee.Model:
        '''Where filter

        :param data: `<peewee.model>` select model
        :param query: `<list/tuple>` query
        :return:
        '''
        if not query:
            return data
        if len(query) == 1:
            return data.where(query[0])
        else:
            return data.where(*tuple(query))

    def pager(self,
              data: peewee.Model,
              page: int = DEF_PAGE,
              limit: int = DEF_LIMIT,
              order: Union[str, tuple] = None,
              ignores: Union[str, list] = None,
              fks: Union[str, list] = None,
              **kwargs: Any) -> dict:
        '''Query by page
        '''
        if order and isinstance(order, (str, tuple)):
            kwargs['_order'] = order
            order = ordering(order, data.model)
        return pager(data,
                     page=page,
                     limit=limit,
                     order=order,
                     ignores=ignores,
                     fks=fks,
                     **kwargs)

    @staticmethod
    def get_now_time(fmt: bool = True):
        return strings.get_now_time(fmt=fmt)
