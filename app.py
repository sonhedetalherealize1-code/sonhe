from flask import Flask, render_template, request, redirect, url_for, session
import os
import mysql.connector
from functools import wraps
from datetime import date


app = Flask(__name__)


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

app.secret_key = os.getenv(
    "SECRET_KEY",
    "chave-temporaria-apenas-local"
)


# ==========================================================
# CONEXÃO COM O BANCO DE DADOS
# ==========================================================

def conectar_banco():

    conexao = mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE")
    )

    return conexao


# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def calcular_status(data_evento):

    if not data_evento:
        return "Sem data"

    hoje = date.today()

    if data_evento < hoje:
        return "Concluído"

    elif data_evento == hoje:
        return "Hoje"

    else:
        return "Pendente"


def calcular_dias(data_evento):

    if not data_evento:
        return None

    hoje = date.today()

    return (data_evento - hoje).days


# ==========================================================
# PROTEÇÃO DO ADMIN
# ==========================================================

def admin_required(func):

    @wraps(func)
    def verificar_login(*args, **kwargs):

        if not session.get("admin_logado"):
            return redirect(url_for("admin_login"))

        return func(*args, **kwargs)

    return verificar_login


# ==========================================================
# PROTEÇÃO DO CLIENTE
# ==========================================================

def cliente_required(func):

    @wraps(func)
    def verificar_login(*args, **kwargs):

        if not session.get("cliente_id"):
            return redirect(url_for("cliente_login"))

        return func(*args, **kwargs)

    return verificar_login


# ==========================================================
# CONVITE
# ==========================================================

@app.route("/")
def convite():

    return render_template("convite.html")


# ==========================================================
# APRESENTAÇÃO
# ==========================================================

@app.route("/apresentacao")
def apresentacao():

    return render_template("apresentacao.html")


# ==========================================================
# SOBRE
# ==========================================================

@app.route("/sobre")
def sobre():

    return render_template("sobre.html")


# ==========================================================
# ORÇAMENTO
# ==========================================================

@app.route("/orcamento", methods=["GET", "POST"])
def orcamento():

    if request.method == "POST":

        nome = request.form.get("nome")
        whatsapp = request.form.get("whatsapp")
        evento = request.form.get("evento")
        data_evento = request.form.get("data")
        cidade = request.form.get("cidade")
        local = request.form.get("local")
        convidados = request.form.get("convidados")
        servico = request.form.get("servico")
        conheceu = request.form.get("conheceu")
        sonho = request.form.get("sonho")

        print("=================================")
        print("NOVO ORÇAMENTO")
        print("=================================")
        print("Nome:", nome)
        print("WhatsApp:", whatsapp)
        print("Evento:", evento)
        print("Data:", data_evento)
        print("Cidade:", cidade)
        print("Local:", local)
        print("Convidados:", convidados)
        print("Serviço:", servico)
        print("Como conheceu:", conheceu)
        print("Sonho:", sonho)
        print("=================================")

        if not nome or not whatsapp or not evento or not data_evento:

            return render_template(
                "orcamento.html",
                erro="Preencha os campos obrigatórios."
            )

        conexao = None
        cursor = None

        try:

            conexao = conectar_banco()

            print("Conectado ao MySQL com sucesso!")

            cursor = conexao.cursor()

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
                data_evento,
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
            print("ID:", cursor.lastrowid)
            print("=================================")

            return render_template("obrigado.html")

        except Exception as erro:

            if conexao:
                conexao.rollback()

            print("=================================")
            print("ERRO AO SALVAR ORÇAMENTO")
            print("=================================")
            print("TIPO:", type(erro).__name__)
            print("ERRO:", erro)
            print("=================================")

            return render_template(
                "orcamento.html",
                erro="Erro ao salvar o orçamento."
            ), 500

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template("orcamento.html")


# ==========================================================
# ADMIN - LOGIN
# ==========================================================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        usuario = request.form.get("usuario")
        senha = request.form.get("senha")

        usuario_correto = os.getenv("ADMIN_USER")
        senha_correta = os.getenv("ADMIN_PASSWORD")

        if (
            usuario == usuario_correto
            and senha == senha_correta
        ):

            session.clear()

            session["admin_logado"] = True

            return redirect(
                url_for("admin_painel")
            )

        return render_template(
            "admin_login.html",
            erro="Usuário ou senha incorretos."
        )

    return render_template("admin_login.html")


# ==========================================================
# ADMIN - PAINEL
# ==========================================================

@app.route("/admin/painel")
@admin_required
def admin_painel():

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(dictionary=True)

        pesquisa = request.args.get(
            "pesquisa",
            ""
        ).strip()

        ordem = request.args.get(
            "ordem",
            "proxima"
        )

        # --------------------------------------------------
        # ORDEM DOS CLIENTES
        # --------------------------------------------------

        if ordem == "antiga":

            ordenacao = "data_evento ASC"

        elif ordem == "recente":

            ordenacao = "data_evento DESC"

        elif ordem == "envio":

            ordenacao = "data_envio DESC"

        else:

            ordenacao = """
                CASE
                    WHEN data_evento >= CURDATE()
                    THEN 0
                    ELSE 1
                END,
                data_evento ASC
            """

        # --------------------------------------------------
        # PESQUISA
        # --------------------------------------------------

        if pesquisa:

            comando = f"""
                SELECT *
                FROM orcamentos
                WHERE nome LIKE %s
                ORDER BY {ordenacao}
            """

            cursor.execute(
                comando,
                (f"%{pesquisa}%",)
            )

        else:

            comando = f"""
                SELECT *
                FROM orcamentos
                ORDER BY {ordenacao}
            """

            cursor.execute(comando)

        clientes = cursor.fetchall()

        # --------------------------------------------------
        # STATUS E DIAS
        # --------------------------------------------------

        for cliente in clientes:

            cliente["status"] = calcular_status(
                cliente.get("data_evento")
            )

            cliente["dias_restantes"] = calcular_dias(
                cliente.get("data_evento")
            )

        return render_template(
            "admin_painel.html",
            clientes=clientes,
            pesquisa=pesquisa,
            ordem=ordem
        )

    except Exception as erro:

        print("=================================")
        print("ERRO AO BUSCAR CLIENTES")
        print("=================================")
        print("TIPO:", type(erro).__name__)
        print("ERRO:", erro)
        print("=================================")

        return (
            "Erro ao carregar os clientes. "
            "Verifique os logs do Railway.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ==========================================================
# ADMIN - VER DETALHES DO CLIENTE
# ==========================================================

@app.route("/admin/cliente/<int:id>")
@admin_required
def admin_cliente(id):

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM orcamentos
            WHERE id = %s
            """,
            (id,)
        )

        cliente = cursor.fetchone()

        if not cliente:

            return "Cliente não encontrado.", 404

        # --------------------------------------------------
        # CALCULAR STATUS
        # --------------------------------------------------

        cliente["status"] = calcular_status(
            cliente.get("data_evento")
        )

        # --------------------------------------------------
        # CALCULAR DIAS RESTANTES
        # --------------------------------------------------

        cliente["dias_restantes"] = calcular_dias(
            cliente.get("data_evento")
        )

        # --------------------------------------------------
        # ABRIR PÁGINA DO CLIENTE
        # --------------------------------------------------

        return render_template(
            "admin_cliente.html",
            cliente=cliente
        )

    except Exception as erro:

        print("=================================")
        print("ERRO AO BUSCAR CLIENTE")
        print("=================================")
        print("ID:", id)
        print("TIPO:", type(erro).__name__)
        print("ERRO:", erro)
        print("=================================")

        return (
            "Erro ao carregar cliente. "
            "Verifique os logs do Railway.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ==========================================================
# ADMIN - EXCLUIR CLIENTE
# ==========================================================

@app.route("/admin/excluir/<int:id>")
@admin_required
def excluir_cliente(id):

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor()

        cursor.execute(
            """
            DELETE FROM orcamentos
            WHERE id = %s
            """,
            (id,)
        )

        conexao.commit()

        print("=================================")
        print("ORÇAMENTO EXCLUÍDO")
        print("ID:", id)
        print("=================================")

        return redirect(
            url_for("admin_painel")
        )

    except Exception as erro:

        if conexao:
            conexao.rollback()

        print("=================================")
        print("ERRO AO EXCLUIR CLIENTE")
        print("=================================")
        print("ID:", id)
        print("TIPO:", type(erro).__name__)
        print("ERRO:", erro)
        print("=================================")

        return "Erro ao excluir cliente.", 500

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ==========================================================
# ADMIN - LOGOUT
# ==========================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# ==========================================================
# CLIENTE - LOGIN
# ==========================================================

@app.route("/cliente", methods=["GET", "POST"])
def cliente_login():

    if request.method == "POST":

        whatsapp = request.form.get("whatsapp")

        if whatsapp:
            whatsapp = whatsapp.strip()

        if not whatsapp:

            return render_template(
                "cliente_login.html",
                erro="Digite seu número de WhatsApp."
            )

        conexao = None
        cursor = None

        try:

            conexao = conectar_banco()

            cursor = conexao.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT *
                FROM orcamentos
                WHERE whatsapp = %s
                ORDER BY data_evento ASC
                """,
                (whatsapp,)
            )

            clientes = cursor.fetchall()

            if not clientes:

                return render_template(
                    "cliente_login.html",
                    erro="Não encontramos nenhum orçamento com esse número."
                )

            cliente = clientes[0]

            session.clear()

            session["cliente_id"] = cliente["id"]
            session["cliente_whatsapp"] = whatsapp

            return redirect(
                url_for("cliente_painel")
            )

        except Exception as erro:

            print("=================================")
            print("ERRO NO LOGIN DO CLIENTE")
            print("=================================")
            print("TIPO:", type(erro).__name__)
            print("ERRO:", erro)
            print("=================================")

            return render_template(
                "cliente_login.html",
                erro="Erro ao acessar sua área."
            ), 500

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template(
        "cliente_login.html"
    )


# ==========================================================
# CLIENTE - PAINEL
# ==========================================================

@app.route("/cliente/painel")
@cliente_required
def cliente_painel():

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(dictionary=True)

        whatsapp = session.get(
            "cliente_whatsapp"
        )

        cursor.execute(
            """
            SELECT *
            FROM orcamentos
            WHERE whatsapp = %s
            ORDER BY data_evento ASC
            """,
            (whatsapp,)
        )

        clientes = cursor.fetchall()

        if not clientes:

            session.clear()

            return redirect(
                url_for("cliente_login")
            )

        for cliente in clientes:

            cliente["status"] = calcular_status(
                cliente.get("data_evento")
            )

            cliente["dias_restantes"] = calcular_dias(
                cliente.get("data_evento")
            )

        return render_template(
            "cliente_painel.html",
            clientes=clientes
        )

    except Exception as erro:

        print("=================================")
        print("ERRO AO CARREGAR PAINEL DO CLIENTE")
        print("=================================")
        print("TIPO:", type(erro).__name__)
        print("ERRO:", erro)
        print("=================================")

        return (
            "Erro ao carregar seu painel.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ==========================================================
# CLIENTE - VER DETALHES
# ==========================================================

@app.route("/cliente/detalhes/<int:id>")
@cliente_required
def cliente_detalhes(id):

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(dictionary=True)

        whatsapp = session.get(
            "cliente_whatsapp"
        )

        cursor.execute(
            """
            SELECT *
            FROM orcamentos
            WHERE id = %s
            AND whatsapp = %s
            """,
            (id, whatsapp)
        )

        cliente = cursor.fetchone()

        if not cliente:

            return "Orçamento não encontrado.", 404

        cliente["status"] = calcular_status(
            cliente.get("data_evento")
        )

        cliente["dias_restantes"] = calcular_dias(
            cliente.get("data_evento")
        )

        return render_template(
            "cliente_painel.html",
            clientes=[cliente]
        )

    except Exception as erro:

        print("=================================")
        print("ERRO AO BUSCAR DETALHES DO CLIENTE")
        print("=================================")
        print("ID:", id)
        print("TIPO:", type(erro).__name__)
        print("ERRO:", erro)
        print("=================================")

        return (
            "Erro ao carregar as informações.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ==========================================================
# CLIENTE - LOGOUT
# ==========================================================

@app.route("/cliente/logout")
def cliente_logout():

    session.clear()

    return redirect(
        url_for("cliente_login")
    )


# ==========================================================
# TESTE DO BANCO
# ==========================================================

@app.route("/teste-banco")
@admin_required
def teste_banco():

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor()

        cursor.execute("SELECT 1")

        resultado = cursor.fetchone()

        return f"""
        <h1>Banco funcionando!</h1>
        <p>Resultado: {resultado}</p>
        """

    except Exception as erro:

        return f"""
        <h1>Erro no banco</h1>
        <p>{erro}</p>
        """, 500

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ==========================================================
# EXECUÇÃO LOCAL
# ==========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv("PORT", 5000)
        ),
        debug=True
    )