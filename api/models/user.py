from database import db
from passlib.hash import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.Index('idx_user_username', 'username', unique=True),
        db.Index('idx_user_email', 'email', unique=True),
        {'schema': 'mercor'}
    )
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(80), unique=True, nullable=False)
    email: str = db.Column(db.String(120), unique=True, nullable=True)
    password_hash: str = db.Column(db.String(128), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password_hash)
