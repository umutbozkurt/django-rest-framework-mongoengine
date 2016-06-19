""" all models shared in tests
class names should be unique across whole project
"""
from mongoengine import Document, DynamicDocument, EmbeddedDocument, fields


class DumbDocument(Document):
    name = fields.StringField()
    foo = fields.IntField()


class IntIdDocument(Document):
    id = fields.IntField(primary_key=True)
    name = fields.StringField()
    foo = fields.IntField()


class DumbEmbedded(EmbeddedDocument):
    name = fields.StringField()
    foo = fields.IntField()


class OtherEmbedded(EmbeddedDocument):
    name = fields.StringField()
    bar = fields.IntField()


class DumbDynamic(DynamicDocument):
    name = fields.StringField()
    foo = fields.IntField()
