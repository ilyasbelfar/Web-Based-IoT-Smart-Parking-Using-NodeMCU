from datetime import datetime
from email.policy import default

from mongoengine import (Document,
                         DateTimeField,
                         BooleanField,
                         ReferenceField,
                         FloatField)

from models.clients import Clients
from models.logs import Logs

class Payments(Document):
    client = ReferenceField(Clients)
    log = ReferenceField(Logs)
    payment_amount = FloatField(default=0.0)
    payment_date = DateTimeField(default=None)
    is_payment_successful = BooleanField(default=False)
