from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Set
from typing import Tuple
from typing import TypeVar
from typing import Union
from xml.dom.minidom import Document

import numpy as np

from .datatype import data_type
from .serializerutils import SerializerUtils

# Generic class type alias
CLASS = TypeVar('CLASS')

# Generic class inst type alias
INSTANCE = TypeVar('INSTANCE')


def get_blacklist_name(
        class_name: str,
) -> str:
    blacklist_name = f'_Serializer__blacklist'
    return blacklist_name


class Serialize(SerializerUtils):

    def _delete_class_vars(
            self
    ) -> None:
        if hasattr(self, 'doc'):
            del self.__class__.doc
            del self.__class__.rootName
            del self.__class__.root

    def _set_class_vars(
            self,
    ) -> None:
        self.__class__.doc = Document()
        self.__class__.rootName = self.__class__.__name__
        self.__class__.root = self.doc.createElement(self.rootName)
        self.doc.appendChild(self.root)

    @staticmethod
    def get_blacklisted_attrs(
            cls_dict: Dict,
            blacklist_name: str,
    ) -> Tuple:
        blacklisted_attrs = ()
        if blacklist_name in cls_dict:
            blacklisted_attrs = tuple(cls_dict[blacklist_name])
        return blacklisted_attrs

    def data_type(
            self,
            data: Any,
    ) -> str:
        return data.__class__.__name__

    def is_abstract_data_type(
            self,
            data: Any,
    ) -> Union[None, bool]:
        data_type = self.data_type(data)
        pdts = {'int', 'float', 'bool', 'str', 'float64', 'float128'
                                                          'NoneType',
                'float32', 'int64', 'int32', 'complex64', 'complex128'}
        if data_type in pdts:
            return
        return True

    def pdt_str_cast(
            self,
            data: Union[
                int, str, float,
                bool, np.float64, np.float32,
                np.int64, np.int32, None,
                np.complex64, np.complex128,
                np.float128,
            ]
    ) -> str:
        return str(data)

    def set_xml_attribs(
            self,
            parent: ET.Element,
            **kwargs,
    ) -> None:
        for attrib_name, attrib_value in kwargs.items():
            parent.setAttribute(attrib_name, attrib_value)

    def set_non_hash_container_tag(
            self,
            index: int,
            minidom_doc: Document,
            parent: ET.Element,
    ) -> ET.Element:
        return minidom_doc.createElement(
            (
                    parent.tagName
                    + '_e'
                    + str(index)
            )
        )

    def set_ndarray_tag(
            self,
            index: int,
            minidom_doc: Document,
            parent: ET.Element,
    ) -> ET.Element:
        return minidom_doc.createElement(
            (
                    parent.tagName
                    + '_e'
                    + str(index)
            )
        )

    def set_dict_tag(
            self,
            key,
            minidom_doc,
            parent
    ) -> ET.Element:
        tag = self.doc.createElement(key)
        return tag

    def serialize_pdt(
            self,
            data,
            minidom_doc,
            parent,
    ) -> None:
        xml_str = self.pdt_str_cast(data)
        tag = minidom_doc.createTextNode(xml_str)
        parent.setAttribute('type', self.data_type(data))
        parent.appendChild(tag)

    def serialize_struct(
            self,
            struct,
            minidom_doc,
            parent,
    ) -> None:
        type_ = data_type(struct)
        if type_ == 'instance':
            self.serialize_inst(struct, minidom_doc, parent)
        elif type_ == 'namedtuple':
            self.serialize_namedtuple(struct, minidom_doc, parent)
        elif type_ == 'list':
            self.serialize_list(struct, minidom_doc, parent)
        elif type_ == 'tuple':
            self.serialize_tuple(struct, minidom_doc, parent)
        elif type_ == 'ndarray':
            self.serialize_ndarray(struct, minidom_doc, parent)
        elif type_ == 'dict':
            self.serialize_dict(struct, minidom_doc, parent)
        elif type_ == 'set':
            self.serialize_set(struct, minidom_doc, parent)

    def serialize_set(
            self,
            set_: Set,
            minidom_doc: Document,
            parent: ET.Element,
    ) -> None:
        parent.setAttribute('type', 'set')
        for i, e in enumerate(set_):
            tag = self.set_non_hash_container_tag(
                i, minidom_doc, parent
            )
            parent.appendChild(tag)
            self.set_xml_attribs(parent, type='set')
            self._serialize(e, tag)

    def serialize_inst(
            self,
            cls,
            minidom_doc,
            parent,
    ) -> None:
        cls_dict = self.get_cls_dict(type(cls))
        inst_dict = self.get_inst_dict(cls)
        class_name = self.get_object_name(cls)
        blacklist_name = get_blacklist_name(class_name)
        blacklisted_attrs = self.get_blacklisted_attrs(
            cls_dict, blacklist_name
        )
        for attr_name, attr_value in inst_dict.items():
            if attr_name in blacklisted_attrs:
                continue
            attr_value = inst_dict[attr_name]
            tag = minidom_doc.createElement(attr_name)
            self.set_xml_attribs(
                parent,
                type='instance',
                class_name=class_name,
                module=self.get_module_name(cls)
            )
            parent.appendChild(tag)
            self._serialize(attr_value, tag)

    def serialize_namedtuple(
            self,
            namedtuple_: NamedTuple,
            minidom_doc: Document,
            parent: ET.Element,
    ) -> None:
        for field_key, field_val in namedtuple_._asdict().items():
            if field_key.startswith('__'):
                continue
            tag = minidom_doc.createElement(field_key)
            self.set_xml_attribs(
                parent,
                type='namedtuple',
                namedtuple_name=self.get_object_name(namedtuple_)
            )
            parent.appendChild(tag)
            self._serialize(field_val, tag)

    def serialize_list(
            self,
            list_: List,
            minidom_doc: Document,
            parent: ET.Element,
    ) -> None:
        parent.setAttribute('type', 'list')
        for i, e in enumerate(list_):
            tag = self.set_non_hash_container_tag(
                i, minidom_doc, parent
            )
            parent.appendChild(tag)
            self.set_xml_attribs(parent, type='list')
            self._serialize(e, tag)

    def serialize_tuple(
            self,
            tuple_: Tuple,
            minidom_doc: Document,
            parent: ET.Element,
    ) -> None:
        parent.setAttribute('type', 'tuple')
        for i, e in enumerate(tuple_):
            tag = self.set_non_hash_container_tag(
                i, minidom_doc, parent
            )
            parent.appendChild(tag)
            self.set_xml_attribs(parent, type='tuple')
            self._serialize(e, tag)

    def serialize_ndarray(
            self,
            ndarray_: np.ndarray,
            minidom_doc: Document,
            parent: ET.Element,
    ) -> None:
        parent.setAttribute('type', 'ndarray')
        for i, e in enumerate(ndarray_):
            tag = self.set_non_hash_container_tag(
                i, minidom_doc, parent
            )
            parent.appendChild(tag)
            self.set_xml_attribs(parent, type='ndarray')
            self._serialize(e, tag)

    def make_dict_keys_serializeable(
            self,
            dict_: Dict,
    ) -> Dict:
        dtype_suffix_dict = {
            'int': '',
            'str': '',
            'float': '',
            'int32': '-INT32',
            'int64': '-INT64',
            'float32': '-FLOAT32',
            'float64': '-FLOAT64',
            'float128': '-FLOAT128',
            'complex64': '-COMPLEX64',
            'complex128': '-COMPLEX128',
        }
        serializeable_dict = {}
        for key, value in dict_.items():
            if isinstance(key, str):
                serializeable_dict[key] = value
            elif isinstance(key, tuple):
                prefix = 'key_'
                suffix = 'tuple'
                serializeable_key = prefix
                for i in key:
                    serializeable_key += str(i) + dtype_suffix_dict[
                        i.__class__.__name__] + '_'
                serializeable_key = serializeable_key + suffix
                serializeable_dict[serializeable_key] = value
            else:
                serializeable_key = (
                        f'key_{key}_'
                        + f'{dtype_suffix_dict[key.__class__.__name__]}'
                )
                serializeable_dict[serializeable_key] = value
        return serializeable_dict

    def serialize_dict(
            self,
            dict_: Dict,
            minidom_doc: Document,
            parent: ET.Element,
    ) -> None:
        dict_ = self.make_dict_keys_serializeable(dict_)
        parent.setAttribute('type', 'dict')
        for key in dict_:
            tag = self.set_dict_tag(key, minidom_doc, parent)
            parent.appendChild(tag)
            self.set_xml_attribs(parent, type='dict')
            self._serialize(dict_[key], tag)

    def add_child(
            self,
            data: Any,
            minidom_doc: Document,
            parent: ET.Element,
    ) -> None:
        if self.data_type(data) == 'NoneType':
            return
        elif self.is_abstract_data_type(data):
            self.serialize_struct(data, minidom_doc, parent)
        else:
            self.serialize_pdt(data, minidom_doc, parent)

    def _serialize(
            self,
            value: Any,
            parent: ET.Element,
    ) -> None:
        self.add_child(value, self.doc, parent)

    def serialize(
            self,
            xml_filename: Optional[str] = None,
            xml_header: Optional[str] = False,

    ) -> None:
        self._set_class_vars()
        parent = self.root
        self._serialize(self, parent)
        if xml_filename is not None:
            self._write_xml(xml_filename, xml_header)
        self._delete_class_vars()

    def _write_xml(
            self,
            xml_filename: str,
            xml_header: str,
    ) -> None:
        xmlstr = self.doc.toprettyxml(indent="	  ")
        if xml_header:
            xmlstr = xmlstr.replace(
                f'?>\n', f'?>\n<!--{xml_header}-->\n', 1
            )
        xml_file = open(xml_filename, 'w')
        xml_file.write(xmlstr)
        xml_file.close()
