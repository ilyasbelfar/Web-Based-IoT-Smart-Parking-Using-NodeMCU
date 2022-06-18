from datetime import datetime

from mongoengine import (DateTimeField,
                         StringField,
                         BooleanField,
                         ReferenceField)

# I need this in get_or_404() function
from mongoengine import Document

from models.clients import Clients

class RFID(Document):
    client = ReferenceField(Clients)
    tag_identifier = StringField(required=True, unique=True)
    tag_suspended = BooleanField(default=False)
    created = DateTimeField(default=datetime.now)
    lastScanned = DateTimeField(default=None)
    is_used = BooleanField(default=False)
    is_reserved = BooleanField(default=False)