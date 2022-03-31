import sqlalchemy
from db.db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'user'
    
    id = sqlalchemy.Column(
        sqlalchemy.Integer, unique=True, nullable=False, primary_key=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    notifications = sqlalchemy.orm.relationship(
        'Notification', back_populates='user', lazy='joined')
   
    def __repr__(self):
        return f"<User> {self.id}"
