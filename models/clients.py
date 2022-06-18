from mongoengine import (Document,
                         StringField,
                         EmailField,
                         BooleanField,
                         IntField,
                         FloatField)

from flask_bcrypt import generate_password_hash, check_password_hash

class Clients(Document):
    first_name = StringField(unique=False)
    last_name = StringField(unique=False)
    email = EmailField(required=True, unique=True)
    tag=StringField(required=False, unique=False)
    password = StringField(required=True, regex=None)
    picture_url = StringField(default="/static/user_avatar.jpg")
    balance = FloatField(default=0.0)
    money_debt= FloatField(default=0.0)
    total_money= FloatField(default=0.0)
    is_admin = BooleanField(default=False)
    is_banned = BooleanField(default=False)


    def generate_pw_hash(self):
        self.password = generate_password_hash(password=self.password).decode('utf-8')
    generate_pw_hash.__doc__ = generate_password_hash.__doc__



    def check_pw_hash(self, password: str) -> bool:
        return check_password_hash(pw_hash=self.password, password=password)
    check_pw_hash.__doc__ = check_password_hash.__doc__



    def save(self, *args, **kwargs):
        if self._created:
          self.generate_pw_hash()
        super(Clients, self).save(*args, **kwargs)
