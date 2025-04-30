import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Define database model base class
class Base(DeclarativeBase):
    pass

# Initialize database
db = SQLAlchemy(model_class=Base)