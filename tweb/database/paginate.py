'''
Page units.
'''
from math import ceil
from typing import Union, Any
import peewee


class BasePages:
    def __init__(self, query: str, page: int, limit: int):
        self.page = page
        self.query = query
        self.limit = limit
        self.count = self._load_count()

    def _load_count(self):
        raise NotImplementedError

    @property
    def pages(self):
        return ceil(self.count / self.limit)

    @property
    def prev(self):
        return self.page > 1

    @property
    def next(self):
        return self.page < self.pages

    def list(self):
        raise NotImplementedError

    def pager(self):
        raise NotImplementedError


class PgSqlPages(BasePages):
    def __init__(self,
                 query: str,
                 db: peewee.Database,
                 page: int = 1,
                 limit: int = 20,
                 sum_cols: Union[None, list] = None,
                 **query_args: Any):
        self.db = db
        self.query = query
        self.sum_cols = sum_cols or []
        self.query_args = query_args
        self._rows = None
        self._row_count = None
        self._sum_rows = dict([(item, 0) for item in self.sum_cols])
        super().__init__(self._fix_sql(query), page, limit)

    def _fix_sql(self, sql: str):
        '''
        - 去掉尾部的分号符
        - 统计rows_count数据
        - 组合汇总数据
        '''
        _sql = sql.strip().lower()
        _sql = _sql[:-1] if _sql.endswith(';') else _sql
        cols, opts = _sql.split('from', 1)
        _group_list = ['COUNT(1) OVER() _row_count']
        for col in self.sum_cols:
            if '(' in col:
                _key = col.split('(')[0]
                _val = col.split('(')[-1].split(')')[0]
                key = col.split(-1)
                _group_list.append(f'{_key}({_key}({_val})) OVER() _sum_{key}')
                continue
            elif 'AS' in col:
                _key, _val = col.split('AS')
                _key = _key.strip()
                _val = _val.strip()
            else:
                _key = _val = col
            _group_list.append(f'SUM(SUM({_key})) OVER() _sum_{_val}')
        return ' '.join([cols, ','+','.join(_group_list), 'from', opts])

    def _load_list(self):
        if self._rows is not None:
            return self._rows
        offset = (self.page - 1) * self.limit
        sql = f'{self.query} OFFSET {offset} LIMIT {self.limit}'
        record = self.db.execute_sql(sql, self.query_args)
        data = []
        rows = record.fetchall()
        if not rows:
            self._row_count = 0
            self._rows = data
            return data

        self._set_rows(rows[0])
        for row in rows:
            row_dict = dict(zip(row.keys(), row))
            data.append(row_dict)
        self._rows = data
        return data

    def _set_rows(self, row):
        row_dict = dict(zip(row.keys(), row))
        self._row_count = row_dict.get('_row_count', 0)
        for k, v in row_dict.items():
            if k.startswith('_sum__'):
                k = k.replace('__sum__', '')
                self._sum_rows[k] = v

    def list(self):
        return self._load_list()

    def _load_count(self):
        self._load_list()
        return self._row_count

    def _load_sum_rows(self):
        self._load_list()
        return self._sum_rows

    def pager(self):
        '''
        Return dict object.
        '''
        self._load_count()
        return {
            'total': self._row_count,
            'pages': self.pages,
            'page': self.page,
            'limit': self.limit,
            'data': self._rows
        }


class MySqlPages(BasePages):
    def __init__(self,
                 query: str,
                 db: peewee.Database,
                 page: int = 1,
                 limit: int = 20,
                 sum_cols: Union[None, list] = None,
                 **query_args: Any):
        self.db = db
        self.query = query
        self.sum_cols = sum_cols or []
        self.query_args = query_args
        self._rows = None
        self._row_count = None
        self._sum_rows = dict([(item, 0) for item in self.sum_cols])
        super().__init__(self._fix_sql(query), page, limit)

    def _get_columns(self, sql):
        '''
        获取查询语句的字段
        '''
        _sql = sql.lower().strip()
        if not _sql.startswith('select'):
            return []
        cols = _sql[6:].split('from', 1)[0]
        flag = (True, 0, 0)
        columns = []
        for col in cols.split(','):
            col = col.strip()
            lc = col.count('(')
            rc = col.count(')')
            if flag[0] is False:
                if (flag[1] + lc) == (flag[2] + rc):
                    flag = (True, 0, 0)
                    columns.append(col.split()[-1])
                else:
                    flag = (False, flag[1] + lc, flag[2] + rc)
            elif lc == rc:
                columns.append(col.split()[-1])
            else:
                flag = (False, lc, rc)
        return columns

    def _fix_sql(self, sql: str):
        '''
        - 去掉尾部的分号符
        - 统计rows_count数据
        - 组合汇总数据
        '''
        _sql = sql.strip().lower()
        _sql = _sql[:-1] if _sql.endswith(';') else _sql
        cols, opts = _sql.split('from', 1)
        # sql_calc_found_rows 统计总行数，最后执行 SELECT FOUND_ROWS()获取总行数
        # SELECT SQL_CALE_FOUND_ROWS id,xxx from xxx
        # SELECT FOUND_ROWS()
        _group_list = []
        for col in self.sum_cols:
            if '(' in col:
                _key = col.split('(')[0]
                _val = col.split('(')[-1].split(')')[0]
                key = col.split(-1)
                _group_list.append(f'{_key}({_key}({_val})) OVER() _sum_{key}')
                continue
            elif 'AS' in col:
                _key, _val = col.split('AS')
                _key = _key.strip()
                _val = _val.strip()
            else:
                _key = _val = col
            _group_list.append(f'SUM(SUM({_key})) OVER() _sum_{_val}')
        if _group_list:
            res = ['SELECT SQL_CALC_FOUND_ROWS'+cols[6:],
                   ','+','.join(_group_list), 'FROM', opts]
        else:
            res = ['SELECT SQL_CALC_FOUND_ROWS'+cols[6:], 'FROM', opts]
        return ' '.join(res)

    def _load_list(self):
        if self._rows is not None:
            return self._rows
        offset = (self.page - 1) * self.limit
        sql = f'{self.query} LIMIT {offset}, {self.limit}'
        record = self.db.execute_sql(sql, self.query_args)
        data = []
        columns = self._get_columns(self.query)
        rows = record.fetchall()
        if not rows:
            self._row_count = 0
            self._rows = data
            return data
        self._set_sum_rows(rows[0], columns)
        for row in rows:
            row_dict = dict(zip(columns, row))
            data.append(row_dict)
        self._rows = data
        self._set_row_count()
        return data

    def _set_row_count(self):
        sql = 'SELECT FOUND_ROWS()'
        record = self.db.execute_sql(sql)
        rows = record.fetchone()
        self._row_count = rows[0]

    def _set_sum_rows(self, row, columns):
        row_dict = dict(zip(columns, row))
        for k, v in row_dict.items():
            if k.startswith('_sum__'):
                k = k.replace('__sum__', '')
                self._sum_rows[k] = v

    def list(self):
        return self._load_list()

    def _load_count(self):
        self._load_list()
        return self._row_count

    def _load_sum_rows(self):
        self._load_list()
        return self._sum_rows

    def pager(self):
        '''
        Return dict object.
        '''
        self._load_count()
        return {
            'total': self._row_count,
            'pages': self.pages,
            'page': self.page,
            'limit': self.limit,
            'data': self._rows
        }


def pager(obj: peewee.Model,
          page: int = 1,
          limit: int = 20,
          order: Union[str, tuple] = None,
          ignores: Union[str, list] = None,
          fks: Union[str, list] = None,
          columns: Union[None, str, list] = None,
          ** kwargs: Any) -> dict:
    '''
    :param obj: `<peewee.model>` object
    :param page: `<int>` default page=1
    :param limit: `<int>` default limit=20
    :param order: `<tuple>` order columns
        eg: (-User.id,) or (User.id, -User.age)
    :param ignores: `<list>` ignore columns return
    :param fks: `<dict>` fk name，
        eg:{'dept_id':['id','name'],'role_id':'name'},value maybe str or list,
        return {'dept_id':{'name':'test','id':1},'role_id':'test'}
    :param columns: `<list>` others columns
    :param kwargs: others parameters
    :return: `<dict>`
    '''
    total = obj.count()
    page = page if page > 0 else 1
    limit = limit if limit > 0 else 20
    if not order or not isinstance(order, tuple):
        datas = obj.paginate(page, limit)
    else:
        if len(order) == 1:
            order = (order[0],)
        datas = obj.paginate(page, limit).order_by(*order)

    pages = ceil(total / limit)
    data = fmt_idx_data(datas, ignores, fks, columns)
    result = {
        'total': total,
        'pages': pages,
        'page': page,
        'limit': limit,
        'rows': data
    }
    if kwargs.get('summary'):
        result.update({'summary': kwargs['summary']})

    # if kwargs and '_order' in kwargs:
    #     kwargs['order'] = kwargs.pop('_order', None)
    #     return {**result, **kwargs}
    return result


def fmt_idx_data(datas: peewee.Model,
                 ignores: Union[str, list] = None,
                 fks: Union[str, list] = None,
                 columns: Union[None, str, list] = None) -> list:
    data = list()
    for d in datas:
        data.append(d.get_dict(ignores, fks=fks, columns=columns))
    return data
