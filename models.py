from flask_login import UserMixin
from extensions import db

agendamento_servicos = db.Table('agendamento_servico',
    db.Column('agendamento_id', db.Integer, db.ForeignKey('agendamento.id'), primary_key=True),
    db.Column('servico_id', db.Integer, db.ForeignKey('servico.id'), primary_key=True)
)

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    duracao_minutos = db.Column(db.Integer, nullable=False)
    preco = db.Column(db.Float, nullable=False)


class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(15), nullable=True)
    agendamentos = db.relationship('Agendamento', backref='cliente', lazy=True)


class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default = 'Pendente')
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)

    servicos = db.relationship('Servico', secondary=agendamento_servicos, backref=db.backref('agendamentos', lazy=True))