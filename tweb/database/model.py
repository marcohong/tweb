import copy
import datetime
from typing import Any, Callable, Union
import peewee

from tweb.utils.strings import datetime_to_str

DFMT = '%Y-%m-%d %H:%M:%S'
DEF_DATE = datetime.datetime.now
CVS_DATE = (datetime.timedelta, datetime.date, datetime.time)


class BaseModel(peewee.Model):
    '''
    Base model class.

    usage:

        MyModel(BaseModel):
            id = peewee.AutoField()
            name = peewee.CharField()
            class Meta:
                database = db
    '''
    # status 1->normal 2->disable
    _st_normal = 1
    _st_disable = 2

    @classmethod
    def fetchone(cls, *query: Any,
                 **kwargs: Any) -> Callable[..., peewee.Model]:
        '''Repeace peewee get(*query, **kwargs) function.
        '''
        try:
            return cls.get(*query, **kwargs)
        except peewee.DoesNotExist:
            return None

    def get_dict(self,
                 ignore: Union[None, str, list] = None,
                 fks: Union[None, dict] = None,
                 fk_merge: bool = True,
                 columns: Union[None, str, list] = None,
                 **kwargs: Any) -> dict:
        '''
        :param ignore: `<list>` ignore Field, default None
        :param fks: `<dict>` ForeignKeyField value,not support datetime type

            usage::

            fks = {'dept_id':['id',name']}
            return {'id':1,'name':'test'}
        :param fk_merge: `<bool>` ForeignKeyField key-value marge. default True
        :param columns: `<str/list>`

            usage::

                fn.COUNT('id').over().alias('total')
                columns='total'
        :return: `<dict>` object
        '''
        data = copy.copy(self.__dict__.get('__data__'))
        # process ignore fields
        if ignore and isinstance(ignore, list):
            intersection = list(set(data.keys()).intersection(ignore))
            for key in intersection:
                del data[key]

        # get field value
        field_get = self._meta.__dict__.get('fields').get
        for key, value in data.items():
            if isinstance(value, datetime.datetime):
                if isinstance(field_get(key), peewee.TimestampField):
                    data[key] = int(value.timestamp())
                else:
                    data[key] = datetime_to_str(value)
            elif isinstance(value, CVS_DATE):
                data[key] = str(value)

        # get mapping values
        if fks and isinstance(fks, dict):
            for field, fk_name in fks.items():
                fk_obj = getattr(self, field)
                if isinstance(fk_name, str):
                    fk_name = [fk_name]
                _dict = {name: getattr(fk_obj, name) for name in fk_name}
                data.update(_dict if fk_merge else {field: _dict})

        # get columns value
        if columns:
            if isinstance(columns, str):
                columns = [columns]
            for field in columns:
                data[field] = getattr(self, field)
        return self.data_filter(data)

    def data_filter(self, data: dict) -> dict:
        ''' Data filters, users can achieve their own

        :param data: `<dict>`
        :return:
        '''
        return data

    def __str__(self):
        return str(self.__dict__.get('__data__'))

    class Meta:
        pass
        # database = db
