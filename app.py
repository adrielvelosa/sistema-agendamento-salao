from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from extensions import db
from models import Cliente, Agendamento, Servico, agendamento_servicos, Usuario



app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///salao_da_leila.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = 'Leila_ta_rica'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('painel_leila'))
        flash('Usuário ou senha inválidos', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/agendamento/<int:agendamento_id>/atualizar_status', methods=['POST'])
@login_required
def atualizar_status(agendamento_id):
    agendamento_para_atualizar = Agendamento.query.get_or_404(agendamento_id)
    novo_status = request.form['novo_status']
    agendamento_para_atualizar.status = novo_status
    db.session.commit()
    return redirect(url_for('painel_leila'))

@app.route('/')
def home():
    return redirect(url_for('agendar'))

@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    
    todos_os_servicos = Servico.query.all()
    
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        data_str = request.form['data_hora']
        data_obj = datetime.strptime(data_str, '%Y-%m-%dT%H:%M')

        cliente = Cliente.query.filter_by(telefone=telefone).first()

        if cliente:
            dia_solicitado = data_obj.date()
            inicio_da_semana = dia_solicitado - timedelta(days=dia_solicitado.weekday())
            fim_da_semana = inicio_da_semana + timedelta(days=6)

            agendamento_existente = Agendamento.query.filter(
                Agendamento.cliente_id == cliente.id,
                Agendamento.data_hora >= inicio_da_semana,
                Agendamento.data_hora <= fim_da_semana,
                Agendamento.id != None
            ).order_by(Agendamento.data_hora).first()


            if agendamento_existente and agendamento_existente.data_hora.date() != data_obj.date():
                data_sugerida = agendamento_existente.data_hora
                sugestao = (f"Notamos que você já tem um horário marcado para "
                            f"{data_sugerida.strftime('%d/%m/%Y às %H:%M')}. "
                            f"Gostaria de marcar este novo serviço para o mesmo dia?")
                
                return render_template('agendamento.html', servicos=todos_os_servicos, sugestao=sugestao, nome_preenchido=nome, telefone_preenchido=telefone)

        if not cliente:
            cliente = Cliente(nome=nome, telefone=telefone)
            db.session.add(cliente)
            db.session.flush()
            
        novo_agendamento = Agendamento(data_hora=data_obj, cliente=cliente)
        
        ids_dos_servicos = request.form.getlist('servicos_selecionados')

        
        if ids_dos_servicos:
            servicos_obj = Servico.query.filter(Servico.id.in_(ids_dos_servicos)).all()
            novo_agendamento.servicos.extend(servicos_obj)
        
        
        db.session.add(novo_agendamento)
        db.session.commit()

        flash('Agendamento criado com sucesso!')
        return redirect(url_for('mostrar_historico', telefone=telefone))
    
    return render_template('agendamento.html', servicos=todos_os_servicos)

@app.route('/painel')
@login_required
def painel_leila():
    listagem_de_agendamentos = Agendamento.query.order_by(Agendamento.data_hora).all()
    return render_template('painel.html', agendamentos=listagem_de_agendamentos)

@app.route('/historico')
def buscar_historico():
    return render_template('buscar_historico.html')

@app.route('/meu_historico')
def mostrar_historico():
    telefone_buscado = request.args.get('telefone')

    cliente_encontrado = None

    if telefone_buscado:
        cliente_encontrado = Cliente.query.filter_by(telefone=telefone_buscado).first()
    
    agora = datetime.now()

    limite_cancelamento = agora + timedelta(days=2)

    return render_template('historico.html', cliente=cliente_encontrado, agora=agora, limite_cancelamento=limite_cancelamento)

@app.route('/agendamento/<int:agendamento_id>/cancelar', methods=['POST'])
def cancelar_agendamento(agendamento_id):
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    agora = datetime.now()

    telefone_do_cliente = agendamento.cliente.telefone

    if agendamento.data_hora > agora and (agendamento.data_hora - agora) > timedelta(days=2):
        agendamento.status = 'Cancelado'
        db.session.commit()
    else:
        pass

    return redirect(url_for('mostrar_historico', telefone=telefone_do_cliente)) 

@app.route('/agendamento/<int:agendamento_id>/alterar', methods=['GET', 'POST'])
def alterar_agendamento(agendamento_id):
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    agora = datetime.now()
    
    if request.method == 'POST':
        origem = request.form.get('origem_form')
    else: 
        origem = request.args.get('origem')

    if origem != 'painel':
        limite = agora + timedelta(days=2)
        if not (agendamento.data_hora > limite):
            flash('Alterações online não são permitidas com menos de 2 dias de antecedência.', 'danger')
            return redirect(url_for('buscar_historico'))

    if request.method == 'POST':
        nova_data_str = request.form['data_hora']
        novos_ids_servicos = request.form.getlist('servicos_selecionados')

        agendamento.data_hora = datetime.strptime(nova_data_str, '%Y-%m-%dT%H:%M')
        
        if novos_ids_servicos:
            novos_servicos_obj = Servico.query.filter(Servico.id.in_(novos_ids_servicos)).all()
            agendamento.servicos = novos_servicos_obj
        else:
            agendamento.servicos = []

        db.session.commit()
        flash('Agendamento alterado com sucesso!', 'success')
        
        if origem == 'painel':
             return redirect(url_for('painel_leila'))
        else:
             return redirect(url_for('mostrar_historico', telefone=agendamento.cliente.telefone))
        
    todos_os_servicos = Servico.query.all()
    return render_template('alterar_agendamento.html', 
                           agendamento=agendamento, 
                           todos_os_servicos=todos_os_servicos,
                           origem=origem)

@app.route('/dashboard')
@login_required
def dashboard():

    hoje = datetime.now().date()
    semana_atras = hoje - timedelta(days=6)

    agendamentos_concluidos_semana = Agendamento.query.filter(
        Agendamento.status == 'Concluído',
        func.date(Agendamento.data_hora).between(semana_atras, hoje)
    ).count()

    faturamento_semanal = db.session.query(func.sum(Servico.preco)).join(
        agendamento_servicos).join(Agendamento).filter(
            Agendamento.status == 'Concluído',
            func.date(Agendamento.data_hora).between(semana_atras, hoje
        )
    ).scalar() or 0.0 

    servico_mais_popular_query = db.session.query(
        Servico.nome, func.count(agendamento_servicos.c.servico_id).label('contagem')
    ).join(agendamento_servicos).join(Agendamento).filter(
        func.date(Agendamento.data_hora).between(semana_atras, hoje),
    ). group_by(Servico.nome).order_by(func.count(agendamento_servicos.c.servico_id).desc()).first() 

    servico_mais_popular = servico_mais_popular_query[0] if servico_mais_popular_query else "Nenhum"

    return render_template(
        'dashboard.html',
        agendamentos_semana=agendamentos_concluidos_semana,
        faturamento_semana=faturamento_semanal,
        servico_popular=servico_mais_popular,
        hoje=hoje,
        semana_atras=semana_atras
    )

if __name__ == '__main__':
    with app.app_context():
        #db.create_all()
        pass
    app.run(debug=True)
