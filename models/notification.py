import sqlalchemy
from db.db_session import SqlAlchemyBase


class Notification(SqlAlchemyBase):
    __tablename__ = 'notification'

    id = sqlalchemy.Column(
        sqlalchemy.Integer, unique=True, nullable=False, primary_key=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("user.id"))
    
    user = sqlalchemy.orm.relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification> {self.id}"
