from flask import Flask, render_template, request, redirect, url_for, session
import os
import mysql.connector
from functools import wraps


app = Flask(__name__)

# ==================================================
# CONFIGURAÇÕES
# ==================================================

app.secret_key = os.getenv(
    "SECRET_KEY",
    "chave-temporaria-apenas-local"
)


# ==================================================
# CONEXÃO COM O BANCO DE DADOS
# ==================================================

def conectar_banco():

    conexao = mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE")
    )

    return conexao


# ==================================================
# CRIAR TABELA AUTOMATICAMENTE
# ==================================================

def criar_tabela():

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()
        cursor = conexao.cursor()

        comando = """
        CREATE TABLE IF NOT EXISTS orcamentos (

            id INT AUTO_INCREMENT PRIMARY KEY,

            nome VARCHAR(150) NOT NULL,

            whatsapp VARCHAR(30) NOT NULL,

            evento VARCHAR(100) NOT NULL,

            data_evento DATE NOT NULL,

            cidade VARCHAR(150) NOT NULL,

            local_evento VARCHAR(200),

            convidados VARCHAR(50),

            servico VARCHAR(100),

            conheceu VARCHAR(150),

            sonho TEXT,

            data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """

        cursor.execute(comando)

        conexao.commit()

        print("=================================")
        print("TABELA ORCAMENTOS VERIFICADA")
        print("=================================")

    except Exception as erro:

        print("=================================")
        print("ERRO AO CRIAR TABELA")
        print("=================================")
        print(erro)

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ==================================================
# PROTEÇÃO DO ADMIN
# ==================================================

def admin_required(func):

    @wraps(func)
    def verificar_login(*args, **kwargs):

        if not session.get("admin_logado"):
            return redirect(url_for("admin_login"))

        return func(*args, **kwargs)

    return verificar_login


# ==================================================
# CONVITE
# ==================================================

@app.route("/")
def convite():

    return render_template("convite.html")


# ==================================================
# APRESENTAÇÃO / VÍDEO
# ==================================================

@app.route("/apresentacao")
def apresentacao():

    return render_template("apresentacao.html")


# ==================================================
# SOBRE A YASMINI
# ==================================================

@app.route("/sobre")
def sobre():

    return render_template("sobre.html")


# ==================================================
# ORÇAMENTO
# ==================================================

@app.route("/orcamento", methods=["GET", "POST"])
def orcamento():

    if request.method == "POST":

        # ==========================================
        # PEGAR DADOS DO FORMULÁRIO
        # ==========================================

        nome = request.form.get("nome")
        whatsapp = request.form.get("whatsapp")
        evento = request.form.get("evento")
        data = request.form.get("data")
        cidade = request.form.get("cidade")
        local = request.form.get("local")
        convidados = request.form.get("convidados")
        servico = request.form.get("servico")
        conheceu = request.form.get("conheceu")
        sonho = request.form.get("sonho")

        # ==========================================
        # VERIFICAR CAMPOS OBRIGATÓRIOS
        # ==========================================

        if not nome or not whatsapp or not evento or not data or not cidade:

            return render_template(
                "orcamento.html",
                erro="Por favor, preencha todos os campos obrigatórios."
            )

        # ==========================================
        # MOSTRAR DADOS NO LOG
        # ==========================================

        print("=================================")
        print("NOVO ORÇAMENTO")
        print("=================================")
        print("Nome:", nome)
        print("WhatsApp:", whatsapp)
        print("Evento:", evento)
        print("Data:", data)
        print("Cidade:", cidade)
        print("Local:", local)
        print("Convidados:", convidados)
        print("Serviço:", servico)
        print("Como conheceu:", conheceu)
        print("Sonho:", sonho)
        print("=================================")

        conexao = None
        cursor = None

        try:

            # ======================================
            # CONECTAR AO MYSQL
            # ======================================

            conexao = conectar_banco()

            print("Conectado ao MySQL com sucesso!")

            cursor = conexao.cursor()

            # ======================================
            # INSERIR ORÇAMENTO
            # ======================================

            comando = """
                INSERT INTO orcamentos (
                    nome,
                    whatsapp,
                    evento,
                    data_evento,
                    cidade,
                    local_evento,
                    convidados,
                    servico,
                    conheceu,
                    sonho
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            valores = (
                nome,
                whatsapp,
                evento,
                data,
                cidade,
                local,
                convidados,
                servico,
                conheceu,
                sonho
            )

            cursor.execute(comando, valores)

            conexao.commit()

            print("=================================")
            print("ORÇAMENTO SALVO COM SUCESSO!")
            print("=================================")

            # ======================================
            # MOSTRAR PÁGINA DE AGRADECIMENTO
            # ======================================

            return render_template("obrigado.html")

        except Exception as erro:

            print("=================================")
            print("ERRO AO SALVAR ORÇAMENTO")
            print("=================================")
            print("TIPO DO ERRO:", type(erro).__name__)
            print("ERRO:", erro)
            print("=================================")

            return render_template(
                "orcamento.html",
                erro="Não foi possível enviar suas informações. Tente novamente."
            ), 500

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    # ==========================================
    # GET
    # ==========================================

    return render_template("orcamento.html")


# ==================================================
# ADMINISTRADOR - LOGIN
# ==================================================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        usuario = request.form.get("usuario")
        senha = request.form.get("senha")

        # ==========================================
        # PEGAR LOGIN DO RAILWAY
        # ==========================================

        usuario_correto = os.getenv("ADMIN_USER")
        senha_correta = os.getenv("ADMIN_PASSWORD")

        # ==========================================
        # VERIFICAR LOGIN
        # ==========================================

        if (
            usuario == usuario_correto
            and senha == senha_correta
        ):

            session["admin_logado"] = True

            return redirect(url_for("admin_painel"))

        return render_template(
            "admin_login.html",
            erro="Usuário ou senha incorretos."
        )

    return render_template("admin_login.html")


# ==================================================
# ADMINISTRADOR - PAINEL
# ==================================================

@app.route("/admin/painel")
@admin_required
def admin_painel():

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM orcamentos
            ORDER BY data_envio DESC
        """)

        clientes = cursor.fetchall()

        return render_template(
            "admin_painel.html",
            clientes=clientes
        )

    except Exception as erro:

        print("=================================")
        print("ERRO AO BUSCAR CLIENTES")
        print("=================================")
        print(erro)

        return "Erro ao carregar os clientes.", 500

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ==================================================
# ADMINISTRADOR - VER CLIENTE
# ==================================================

@app.route("/admin/cliente/<int:id>")
@admin_required
def admin_cliente(id):

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM orcamentos
            WHERE id = %s
        """, (id,))

        cliente = cursor.fetchone()

        if not cliente:

            return "Cliente não encontrado.", 404

        return render_template(
            "admin_cliente.html",
            cliente=cliente
        )

    except Exception as erro:

        print("=================================")
        print("ERRO AO BUSCAR CLIENTE")
        print("=================================")
        print(erro)

        return "Erro ao carregar cliente.", 500

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ==================================================
# ADMINISTRADOR - LOGOUT
# ==================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("admin_login"))


# ==================================================
# INICIALIZAÇÃO
# ==================================================

if __name__ == "__main__":

    criar_tabela()

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=True
    )