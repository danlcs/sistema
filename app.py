import hashlib
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinica_veterinaria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)

class Tutor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf_criptografado = db.Column(db.String(64), nullable=False) 
    pets = db.relationship('Pet', backref='tutor', lazy=True)

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(50), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor.id'), nullable=False)
    agendamentos = db.relationship('Agendamento', backref='pet', lazy=True)

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)

def criptografar_cpf(cpf):
    return hashlib.sha256(cpf.encode('utf-8')).hexdigest()

with app.app_context():
    db.create_all()
    if not Usuario.query.first():
        u1 = Usuario(nome="Dr. Carlos", username="carlos", senha="123")
        u2 = Usuario(nome="Dra. Ana", username="ana", senha="123")
        u3 = Usuario(nome="Atendente Mariana", username="mariana", senha="123")
        db.session.add_all([u1, u2, u3])
        
        t1 = Tutor(nome="João Silva", cpf_criptografado=criptografar_cpf("11122233344"))
        t2 = Tutor(nome="Maria Souza", cpf_criptografado=criptografar_cpf("55566677788"))
        t3 = Tutor(nome="Pedro Santos", cpf_criptografado=criptografar_cpf("99900011122"))
        db.session.add_all([t1, t2, t3])
        db.session.commit()

        p1 = Pet(nome="Rex", especie="Cão", tutor_id=t1.id)
        p2 = Pet(nome="Mingau", especie="Gato", tutor_id=t2.id)
        p3 = Pet(nome="Thor", especie="Cão", tutor_id=t3.id)
        db.session.add_all([p1, p2, p3])
        db.session.commit()

        a1 = Agendamento(data_hora=datetime(2026, 11, 15, 14, 0), pet_id=p1.id)
        a2 = Agendamento(data_hora=datetime(2026, 11, 12, 9, 30), pet_id=p2.id)
        a3 = Agendamento(data_hora=datetime(2026, 11, 12, 16, 0), pet_id=p3.id)
        db.session.add_all([a1, a2, a3])
        db.session.commit()


@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(username=username, senha=senha).first()
        
        if usuario:
            session['user_id'] = usuario.id
            session['user_nome'] = usuario.nome
            return redirect(url_for('dashboard'))
        else:
            flash("Falha na autenticação. Usuário ou senha incorretos.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/tutores', methods=['GET', 'POST'])
def tutores():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    termo_busca = request.args.get('busca', '')
    if termo_busca:
        lista_tutores = Tutor.query.filter(Tutor.nome.contains(termo_busca)).all()
    else:
        lista_tutores = Tutor.query.all()
        
    return render_template('tutores.html', tutores=lista_tutores, busca=termo_busca)

@app.route('/tutores/editar/<int:id>', methods=['POST'])
def editar_tutor(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    tutor = Tutor.query.get_or_create(id=id)[0]
    novo_nome = request.form.get('nome')
    novo_cpf = request.form.get('cpf')
    
    if novo_nome:
        tutor.nome = novo_nome
    if novo_cpf:
        tutor.cpf_criptografado = criptografar_cpf(novo_cpf)
        
    db.session.commit()
    flash("Dados do tutor atualizados com sucesso!", "success")
    return redirect(url_for('tutores'))

@app.route('/agendamentos', methods=['GET', 'POST'])
def agendamentos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    lista_agendamentos = Agendamento.query.order_by(Agendamento.data_hora.asc()).all()
    return render_template('agendamentos.html', agendamentos=lista_agendamentos)

@app.route('/agendamentos/atualizar/<int:id>', methods=['POST'])
def atualizar_agendamento(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    agendamento = Agendamento.query.get(id)
    nova_data_str = request.form.get('nova_data')
    
    if nova_data_str:
        try:
            agendamento.data_hora = datetime.strptime(nova_data_str, '%Y-%m-%dT%H:%M')
            db.session.commit()
            flash("Data de agendamento atualizada com sucesso!", "success")
        except ValueError:
            flash("Formato de data inválido.", "danger")
            
    return redirect(url_for('agendamentos'))

if __name__ == '__main__':
    app.run(debug=True)
