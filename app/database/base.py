from sqlalchemy.orm import DeclarativeBase

#Base is the parent class for all our database models. SQLAlchemy uses it to collect information about tables, columns, relationships, and constraints.
#All models will inherit from Base.

class Base(DeclarativeBase):
    pass