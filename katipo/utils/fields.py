import datetime

from django.db import models
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

class PythonField(models.TextField):
    @staticmethod
    def compile(code_string):
        ml = {}
        mc = compile(code_string.replace('\r\n', '\n'), '<PythonField>', 'exec')
        eval(mc, {}, ml)
        return ml
    
    def contribute_to_class(self, cls, name):
        super(PythonField, self).contribute_to_class(cls, name)
        
        def get_pymod(model_instance):
            mname = "_%s_module" % self.attname
            if not hasattr(model_instance, mname):
                setattr(model_instance, mname, PythonField.compile(getattr(model_instance, self.attname, '')))
            return getattr(model_instance, mname)
        
        setattr(cls, 'get_%s_module' % self.name, get_pymod)
    
    def formfield(self, *args, **kwargs):
        defaults={'form_class': PythonFormField}
        defaults.update(kwargs)
        return super(PythonField, self).formfield(*args, **defaults)

class PythonFormField(forms.CharField):
    default_error_messages = {
        'syntax':  _(u'Syntax error at line %(lineno)d.'),
        'compile': _(u'Error compiling: %(message)s')
    }

    def clean(self, value):
        super(PythonFormField, self).clean(value)
        try:
            cm = PythonField.compile(value)
        except SyntaxError, e:
            raise forms.ValidationError(self.error_messages['syntax'] % {'lineno':e.lineno})
        except Exception, e:
            raise forms.ValidationError(self.error_messages['compile'] % {'message':e})
        
        return value



# from http://www.djangosnippets.org/snippets/1060/
# modified to use floatfield, represent <1s intervals
# and have a get_FIELD_seconds() method

class TimedeltaField(models.Field):
    u'''
    Store pythons datetime.timedelta in an integer column.
    Most databasesystems only support 32 Bit integers by default.
    '''
    SECS_PER_DAY=3600*24
    
    __metaclass__=models.SubfieldBase
    
    def __init__(self, *args, **kwargs):
        super(TimedeltaField, self).__init__(*args, **kwargs)
    
    def to_python(self, value):
        if (value is None) or isinstance(value, datetime.timedelta):
            return value
        assert isinstance(value, (float,int)), (value, type(value))
        return datetime.timedelta(seconds=value)
    
    def get_internal_type(self):
        return 'FloatField'
    
    def get_db_prep_lookup(self, lookup_type, value):
        raise NotImplementedError()  # SQL WHERE
    
    def get_db_prep_save(self, value):
        if value is None:
            return None
        elif isinstance(value, (float, int)):
            return float(value)
        return self.SECS_PER_DAY*value.days + value.seconds + value.microseconds/1E6
    
    def contribute_to_class(self, cls, name):
        super(TimedeltaField, self).contribute_to_class(cls, name)
        
        def get_secs(model_instance):
            return self.get_db_prep_save(getattr(model_instance, self.attname, None))
        
        setattr(cls, 'get_%s_seconds' % self.name, get_secs)

