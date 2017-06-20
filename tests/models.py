""" all models shared in tests
class names should be unique across whole project
"""
from mongoengine import Document, DynamicDocument, EmbeddedDocument, fields, DynamicEmbeddedDocument


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

    def __str__(self):
        return "<DumbEmbedded %s %s>" % (self.name, self.foo)


class OtherEmbedded(EmbeddedDocument):
    name = fields.StringField(required=True)
    bar = fields.IntField(required=True)


class DumbDynamicEmbedded(DynamicEmbeddedDocument):
    name = fields.StringField()
    foo = fields.IntField()

    def __str__(self):
        return "<DumbDynamicEmbedded %s %s>" % (self.name, self.foo)


class DumbDynamic(DynamicDocument):
    name = fields.StringField()
    foo = fields.IntField()


class EmbeddingDynamic(DynamicDocument):
    name = fields.StringField()
    foo = fields.IntField()
    embedded = fields.EmbeddedDocumentField(DumbEmbedded)


class DocumentEmbeddingDynamic(Document):
    name = fields.StringField()
    foo = fields.IntField()
    embedded = fields.EmbeddedDocumentField(DumbDynamicEmbedded)
