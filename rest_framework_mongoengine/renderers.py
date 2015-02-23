from rest_framework.renderers import YAMLRenderer as drf_YAMLRenderer
from rest_framework.utils.encoders import SafeDumper
from mongoengine.base.datastructures import BaseDict, BaseList


class YAMLRenderer(drf_YAMLRenderer):
    pass


SafeDumper.add_representer(BaseDict, SafeDumper.represent_dict)
SafeDumper.add_representer(BaseList, SafeDumper.represent_list)
