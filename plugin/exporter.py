import os
from collections import namedtuple

from PyQt5.QtWidgets import QMessageBox

from org.umlfri.api.model import ElementVisual

from dialog import ShowSourceDialog


def check_last(iterable):
    iterator = iter(iterable)
    try:
        previous = next(iterator)
    except StopIteration:
        return
    for val in iterator:
        yield False, previous
        previous = val
    yield True, previous


def values_to_dict(values):
    ret = {}
    for path, value in values:
        path = path.split('/')
        curr = ret
        mk_new = None
        for is_last, part in check_last(path):
            if mk_new is not None:
                if isinstance(curr, dict):
                    if part.isdigit():
                        curr[mk_new] = []
                    else:
                         curr[mk_new] = {}
                else:
                    if part.isdigit():
                        while len(curr) <= mk_new:
                            curr.append([])
                    else:
                        while len(curr) <= mk_new:
                            curr.append({})
                curr = curr[mk_new]
                mk_new = None
            if isinstance(curr, dict):
                if is_last:
                    curr[part] = value
                elif part in curr:
                    curr = curr[part]
                else:
                    mk_new = part
            elif isinstance(curr, list):
                idx = int(part)
                if is_last:
                    while len(curr) <= idx:
                        curr.append(None)
                    curr[idx] = value
                elif idx < len(curr):
                    curr = curr[idx]
                else:
                    mk_new = idx
    return ret


class JavaClass:
    Attribute = namedtuple('Attribute', ['name', 'type', 'visibility', 'is_static', 'is_final', 'default'])
    Constructor = namedtuple('Constructor', ['visibility', 'parameters'])
    Method = namedtuple('Method', ['name', 'return_type', 'visibility', 'is_static', 'parameters'])
    Parameter = namedtuple('Parameter', ['name', 'type'])
    
    def __init__(self, name):
        self.__type = 'class'
        self.__name = name
        self.__super_class = None
        self.__interfaces = []
        self.__enum_items = []
        self.__attributes = []
        self.__methods = []
        self.__constructors = []
    
    def get_name(self):
        return self.__name
    
    def make_interface(self):
        self.__type = 'interface'
    
    def make_abstract(self):
        self.__type = 'abstract class'
    
    def make_enum(self):
        self.__type = 'enum'
    
    def build(self):
        ret = []
        ret.append("public {} {}".format(self.__type, self.__name))
        if self.__super_class is not None:
            ret.append(" extends {}".format(self.__super_class))
        
        if self.__interfaces:
            ret.append(" implements {}".format(", ".join(self.__interfaces)))
        
        ret.append(" {\n")
        
        for is_last, item in check_last(self.__enum_items):
            if not is_last:
                ret.append("    {},\n".format(item))
            elif self.__attributes or self.__methods or self.__constructors:
                ret.append("    {};\n".format(item))
            else:
                ret.append("    {}\n".format(item))
        
        for attr in self.__attributes:
            ret.append("    ")
            if attr.visibility:
                ret.append("{} ".format(attr.visibility))
            if attr.is_static:
                ret.append("static ")
            if attr.is_final:
                ret.append("final ")
            ret.append("{} {}".format(attr.type or '???', attr.name))
            if attr.default is not None:
                ret.append(" = {}".format(attr.default))
            ret.append(";\n")
        
        for constructor in self.__constructors:
            ret.append("    \n")
            ret.append("    ")
            if self.__type != 'enum' and constructor.visibility:
                ret.append("{} ".format(constructor.visibility))
            ret.append("{}(".format(self.__name))
            for is_last, param in check_last(constructor.parameters):
                if not is_last:
                    ret.append("{} {}, ".format(param.type or '???', param.name))
                else:
                    ret.append("{} {}".format(param.type or '???', param.name))
            ret.append(") {\n")
            ret.append("        \n")
            ret.append("    }\n")
        
        for method in self.__methods:
            ret.append("    \n")
            ret.append("    ")
            if self.__type != 'interface' and method.visibility:
                ret.append("{} ".format(method.visibility))
            if method.is_static:
                ret.append("static ")
            ret.append("{} {}(".format(method.return_type or 'void', method.name))
            for is_last, param in check_last(method.parameters):
                if not is_last:
                    ret.append("{} {}, ".format(param.type or '???', param.name))
                else:
                    ret.append("{} {}".format(param.type or '???', param.name))
            ret.append(") {\n")
            ret.append("        \n")
            ret.append("    }\n")
        
        ret.append("}")
        return "".join(ret)
    
    def set_super_class(self, super_class):
        self.__super_class = super_class
    
    def add_implementation(self, iface_name):
        self.__interfaces.append(iface_name)

    def add_enum_item(self, item):
        self.__enum_items.append(item)

    def add_attribute(self, name, type, visibility, is_static, is_final, default):
        self.__attributes.append(JavaClass.Attribute(name, type, visibility, is_static, is_final, default))

    def add_constructor(self, visibility, parameters):
        self.__constructors.append(JavaClass.Constructor(visibility, tuple(JavaClass.Parameter(*param) for param in parameters)))

    def add_method(self, name, return_type, visibility, is_static, parameters):
        self.__methods.append(JavaClass.Method(name, return_type, visibility, is_static, tuple(JavaClass.Parameter(*param) for param in parameters)))


class AttributeInfo:
    def __init__(self, props):
        self.__props = props
    
    def can_be_enum_item(self):
        return self.__props.get('visibility') == '+' and self.__props.get('static')
    
    def get_visibility(self):
        vis = self.__props.get('visibility')
        if vis == '+':
            return 'public'
        elif vis == '#':
            return 'protected'
        elif vis == '~':
            return None
        else:
            return 'private'
    
    def get_enum_item(self):
        return self.__props['name']
    
    def get_name(self):
        return self.__props['name']
    
    def get_type(self):
        return self.__props.get('type', None)
    
    def is_static(self):
        return self.__props.get('static', True)

    def is_final(self):
        return self.__props.get('stereotype') == 'final'

    def get_default_value(self):
        return self.__props.get('default') or None


class OperationInfo:
    def __init__(self, class_name, props):
        self.__props = props
        self.__class_name = class_name
    
    def can_be_constructor(self):
        if self.__props.get('name') == self.__class_name and not self.__props.get('rtype'):
            return True
        if self.__props.get('name') == 'new' and self.__props.get('static') and self.__props.get('rtype') == self.__class_name:
            return True
        return False
    
    def get_visibility(self):
        vis = self.__props.get('visibility')
        if vis == '+':
            return 'public'
        elif vis == '#':
            return 'protected'
        elif vis == '~':
            return None
        else:
            return 'private'

    def get_parameters(self):
        return tuple((param['name'], param.get('type') or None) for param in self.__props.get('parameters', ()))

    def get_name(self):
        return self.__props['name']

    def get_return_type(self):
        return self.__props.get('rtype') or None

    def is_static(self):
        return self.__props.get('static', False)


class ClassExporter:
    def __init__(self, element_object):
        self.__element = element_object
        self.__props = values_to_dict(self.__element.values)
    
    def export(self):
        cls = JavaClass(self.__get_name())
        
        if self.__stereotype_is('interface'):
            cls.make_interface()
        
        if self.__is_abstract():
            cls.make_abstract()
        
        if self.__stereotype_is('enum'):
            cls.make_enum()
            is_enum = True
        else:
            is_enum = False
        
        for super_class in self.__get_connected_classes('generalisation'):
            super_class_name = values_to_dict(super_class.values)['name']
            cls.set_super_class(super_class_name)
        
        for iface in self.__get_connected_classes('implementation'):
            iface_name = values_to_dict(iface.values)['name']
            cls.add_implementation(iface_name)
        
        enum_items = []
        attributes = []
        
        for attr in self.__get_attributes():
            attr = AttributeInfo(attr)
            if attr.can_be_enum_item() and is_enum:
                enum_items.append(attr)
            else:
                attributes.append(attr)
        
        for item in enum_items:
            cls.add_enum_item(item.get_enum_item())
        
        for attr in attributes:
            cls.add_attribute(attr.get_name(), attr.get_type(), attr.get_visibility(), attr.is_static(), attr.is_final(), attr.get_default_value())
        
        constructors = []
        methods = []
        
        for op in self.__get_operations():
            op = OperationInfo(self.__get_name(), op)
            if op.can_be_constructor():
                constructors.append(op)
            else:
                methods.append(op)
        
        for op in constructors:
            cls.add_constructor(op.get_visibility(), op.get_parameters())
        
        for op in methods:
            cls.add_method(op.get_name(), op.get_return_type(), op.get_visibility(), op.is_static(), op.get_parameters())
        
        return cls
    
    def __get_name(self):
        return self.__props['name']
    
    def __stereotype_is(self, value):
        return self.__props.get('stereotype') == value
    
    def __is_abstract(self):
        return self.__props.get('abstract', False)
    
    def __get_connected_classes(self, connection_type):
        for connection in self.__element.connections:
            if connection.type.name == connection_type and connection.source == self.__element:
                if connection.destination.type.name == 'class':
                    yield connection.destination

    def __get_attributes(self):
        return self.__props.get('attributes', ())

    def __get_operations(self):
        return self.__props.get('operations', ())


class Exporter:
    def __init__(self, app):
        self.__app = app
    
    def export(self):
        if self.__app.current_diagram is None:
            QMessageBox.critical(None, "Java export", "No diagram")
            return
        selected = [sel for sel in self.__app.current_diagram.selection if isinstance(sel, ElementVisual) and sel.object.type.name == 'class']
        if not selected:
            QMessageBox.critical(None, "Java export", "No class is selected")
            return
        if len(selected) > 1:
            QMessageBox.critical(None, "Java export", "Select just one class")
            return
        
        cls = ClassExporter(selected[0].object).export()
        
        dlg = ShowSourceDialog()
        dlg.set_class_name(cls.get_name())
        dlg.set_source(cls.build())
        if os.name == 'nt':
            dlg.showMinimized()
            dlg.showNormal()
        else:
            dlg.show()
