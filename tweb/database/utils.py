import peewee
from typing import Any, List, Optional, Union

PARAM_TYPE = Union[dict, list, tuple]


class SQLQuery:
    @classmethod
    def fetchone(cls,
                 db: peewee.Database,
                 sql: str,
                 columns: list,
                 params: PARAM_TYPE = None) -> Optional[dict]:
        record = db.execute_sql(sql, params=params).fetchone()
        if not record:
            return None
        return dict(zip(columns, record))

    @classmethod
    def fetchall(cls,
                 db: peewee.Database,
                 sql: str,
                 columns: list,
                 params: PARAM_TYPE = None) -> Optional[List[dict]]:
        records = db.execute_sql(sql, params=params).fetchall()
        datas = []
        if not records:
            return None
        for record in records:
            datas.append(dict(zip(columns, record)))
        return datas

    @classmethod
    def exists(cls, db: peewee.Database, table: str,
               **query_args: Any) -> bool:
        if not query_args:
            where = '1=0'
        else:
            where = ' '.join([f"{k}='{v}' AND" for k, v in query_args.items()])
            where = where[:-4]
        sql = f'SELECT 1 FROM {table} WHERE {where} LIMIT 1'
        record = db.execute_sql(sql).fetchone()
        if not record:
            return False
        return True

    @classmethod
    def count(cls, db: peewee.Database, sql, params: PARAM_TYPE = None) -> int:
        record = db.execute_sql(sql, params=params).fetchone()
        return record[0]
