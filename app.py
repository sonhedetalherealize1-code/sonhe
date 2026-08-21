from flask import Flask, render_template, request, redirect, url_for, session
import os
import mysql.connector
from functools import wraps
from datetime import date, datetime


app = Flask(__name__)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

app.secret_key = os.getenv(
    "SECRET_KEY",
    "chave-temporaria-apenas-local"
)


# ============================================================
# CONEXÃO COM O MYSQL
# ============================================================

def conectar_banco():

    conexao = mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE")
    )

    return conexao


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def calcular_status(data_evento):

    if not data_evento:
        return "Pendente", "pendente", None

    # Caso venha como datetime
    if isinstance(data_evento, datetime):
        data_evento = data_evento.date()

    # Caso venha como texto
    if isinstance(data_evento, str):

        try:
            data_evento = datetime.strptime(
                data_evento,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return "Pendente", "pendente", None

    hoje = date.today()

    diferenca = (data_evento - hoje).days

    # Evento já passou
    if diferenca < 0:

        return (
            "Concluído",
            "concluido",
            diferenca
        )

    # Até 7 dias
    elif diferenca <= 7:

        return (
            "Urgente",
            "urgente",
            diferenca
        )

    # Até 30 dias
    elif diferenca <= 30:

        return (
            "Atenção",
            "atencao",
            diferenca
        )

    # Mais de 30 dias
    else:

        return (
            "Pendente",
            "pendente",
            diferenca
        )


def preparar_cliente(cliente):

    status, status_classe, dias = calcular_status(
        cliente.get("data_evento")
    )

    cliente["status"] = status
    cliente["status_classe"] = status_classe
    cliente["dias_restantes"] = dias

    return cliente


# ============================================================
# PROTEÇÃO DO ADMIN
# ============================================================

def admin_required(func):

    @wraps(func)
    def verificar_login(*args, **kwargs):

        if not session.get("admin_logado"):

            return redirect(
                url_for("admin_login")
            )

        return func(*args, **kwargs)

    return verificar_login


# ============================================================
# PROTEÇÃO DO CLIENTE
# ============================================================

def cliente_required(func):

    @wraps(func)
    def verificar_cliente(*args, **kwargs):

        if not session.get("cliente_id"):

            return redirect(
                url_for("cliente_login")
            )

        return func(*args, **kwargs)

    return verificar_cliente


# ============================================================
# CONVITE
# ============================================================

@app.route("/")
def convite():

    return render_template(
        "convite.html"
    )


# ============================================================
# APRESENTAÇÃO
# ============================================================

@app.route("/apresentacao")
def apresentacao():

    return render_template(
        "apresentacao.html"
    )


# ============================================================
# SOBRE A YASMINI
# ============================================================

@app.route("/sobre")
def sobre():

    return render_template(
        "sobre.html"
    )


# ============================================================
# ORÇAMENTO
# ============================================================

@app.route(
    "/orcamento",
    methods=["GET", "POST"]
)
def orcamento():

    if request.method == "POST":

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

            conexao = conectar_banco()

            print(
                "Conectado ao MySQL com sucesso!"
            )

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
                data,
                cidade,
                local,
                convidados,
                servico,
                conheceu,
                sonho
            )

            cursor.execute(
                comando,
                valores
            )

            conexao.commit()

            print(
                "ORÇAMENTO SALVO COM SUCESSO!"
            )

            return render_template(
                "obrigado.html"
            )

        except Exception as erro:

            print("=================================")
            print("ERRO AO SALVAR ORÇAMENTO")
            print("=================================")
            print(
                "TIPO:",
                type(erro).__name__
            )
            print(
                "ERRO:",
                erro
            )
            print("=================================")

            if conexao:
                conexao.rollback()

            return (
                "Erro ao salvar o orçamento.",
                500
            )

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template(
        "orcamento.html"
    )


# ============================================================
# ADMIN - LOGIN
# ============================================================

@app.route(
    "/admin",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        usuario = request.form.get(
            "usuario"
        )

        senha = request.form.get(
            "senha"
        )

        usuario_correto = os.getenv(
            "ADMIN_USER"
        )

        senha_correta = os.getenv(
            "ADMIN_PASSWORD"
        )

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

    return render_template(
        "admin_login.html"
    )


# ============================================================
# ADMIN - PAINEL
# ============================================================

@app.route("/admin/painel")
@admin_required
def admin_painel():

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(
            dictionary=True
        )

        # ----------------------------------------------------
        # PESQUISA
        # ----------------------------------------------------

        pesquisa = request.args.get(
            "pesquisa",
            ""
        ).strip()

        # ----------------------------------------------------
        # ORDENAÇÃO
        # ----------------------------------------------------

        ordem = request.args.get(
            "ordem",
            "recente"
        )

        if ordem == "data_asc":

            ordenacao = "data_evento ASC"

        elif ordem == "data_desc":

            ordenacao = "data_evento DESC"

        elif ordem == "nome":

            ordenacao = "nome ASC"

        else:

            ordenacao = "data_envio DESC"

        # ----------------------------------------------------
        # BUSCAR CLIENTES
        # ----------------------------------------------------

        if pesquisa:

            cursor.execute(
                f"""
                SELECT *
                FROM orcamentos
                WHERE nome LIKE %s
                ORDER BY {ordenacao}
                """,
                (
                    f"%{pesquisa}%",
                )
            )

        else:

            cursor.execute(
                f"""
                SELECT *
                FROM orcamentos
                ORDER BY {ordenacao}
                """
            )

        clientes = cursor.fetchall()

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        for cliente in clientes:

            preparar_cliente(
                cliente
            )

        # ----------------------------------------------------
        # ESTATÍSTICAS
        # ----------------------------------------------------

        total = len(clientes)

        urgentes = 0
        atencao = 0
        concluidos = 0
        pendentes = 0

        for cliente in clientes:

            if cliente["status"] == "Urgente":

                urgentes += 1

            elif cliente["status"] == "Atenção":

                atencao += 1

            elif cliente["status"] == "Concluído":

                concluidos += 1

            else:

                pendentes += 1

        return render_template(
            "admin_painel.html",
            clientes=clientes,
            total=total,
            urgentes=urgentes,
            atencao=atencao,
            concluidos=concluidos,
            pendentes=pendentes,
            pesquisa=pesquisa,
            ordem=ordem
        )

    except Exception as erro:

        print("=================================")
        print("ERRO AO CARREGAR PAINEL")
        print("=================================")
        print(
            "TIPO:",
            type(erro).__name__
        )
        print(
            "ERRO:",
            erro
        )
        print("=================================")

        return (
            "Erro ao carregar os clientes.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ============================================================
# ADMIN - VER CLIENTE
# ============================================================

@app.route(
    "/admin/cliente/<int:id>"
)
@admin_required
def admin_cliente(id):

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(
            dictionary=True
        )

        # ----------------------------------------------------
        # BUSCAR PELO ID
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                nome,
                whatsapp,
                evento,
                data_evento,
                cidade,
                local_evento,
                convidados,
                servico,
                conheceu,
                sonho,
                data_envio
            FROM orcamentos
            WHERE id = %s
            LIMIT 1
            """,
            (id,)
        )

        cliente = cursor.fetchone()

        # ----------------------------------------------------
        # CLIENTE NÃO EXISTE
        # ----------------------------------------------------

        if not cliente:

            return render_template(
                "admin_cliente.html",
                cliente=None,
                erro="Cliente não encontrado."
            ), 404

        # ----------------------------------------------------
        # PREPARAR STATUS
        # ----------------------------------------------------

        preparar_cliente(
            cliente
        )

        # ----------------------------------------------------
        # RETORNAR PÁGINA
        # ----------------------------------------------------

        return render_template(
            "admin_cliente.html",
            cliente=cliente
        )

    except Exception as erro:

        print("=================================")
        print("ERRO AO BUSCAR CLIENTE")
        print("=================================")
        print(
            "ID:",
            id
        )
        print(
            "TIPO:",
            type(erro).__name__
        )
        print(
            "ERRO:",
            erro
        )
        print("=================================")

        return (
            "Erro ao carregar cliente.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ============================================================
# ADMIN - EXCLUIR
# ============================================================

@app.route(
    "/admin/excluir/<int:id>",
    methods=["POST"]
)
@admin_required
def admin_excluir(id):

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

        return redirect(
            url_for("admin_painel")
        )

    except Exception as erro:

        print(
            "ERRO AO EXCLUIR:",
            erro
        )

        if conexao:
            conexao.rollback()

        return (
            "Erro ao excluir orçamento.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ============================================================
# ADMIN - LOGOUT
# ============================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_logado",
        None
    )

    return redirect(
        url_for("admin_login")
    )


# ============================================================
# CLIENTE - LOGIN
# ============================================================

@app.route(
    "/cliente",
    methods=["GET", "POST"]
)
def cliente_login():

    if request.method == "POST":

        whatsapp = request.form.get(
            "whatsapp",
            ""
        ).strip()

        if not whatsapp:

            return render_template(
                "cliente_login.html",
                erro="Digite seu WhatsApp."
            )

        # ----------------------------------------------------
        # LIMPAR FORMATAÇÃO
        # ----------------------------------------------------

        whatsapp_limpo = (
            whatsapp
            .replace("(", "")
            .replace(")", "")
            .replace("-", "")
            .replace(" ", "")
            .replace("+", "")
        )

        conexao = None
        cursor = None

        try:

            conexao = conectar_banco()

            cursor = conexao.cursor(
                dictionary=True
            )

            # ------------------------------------------------
            # BUSCAR PELO WHATSAPP
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT *
                FROM orcamentos

                WHERE REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    whatsapp,
                                    '(',
                                    ''
                                ),
                                ')',
                                ''
                            ),
                            '-',
                            ''
                        ),
                        ' ',
                        ''
                    ),
                    '+',
                    ''
                ) = %s

                ORDER BY data_envio DESC

                LIMIT 1
                """,
                (
                    whatsapp_limpo,
                )
            )

            cliente = cursor.fetchone()

            # ------------------------------------------------
            # NÃO ENCONTROU
            # ------------------------------------------------

            if not cliente:

                return render_template(
                    "cliente_login.html",
                    erro=(
                        "Não encontramos um orçamento "
                        "com esse WhatsApp."
                    )
                )

            # ------------------------------------------------
            # LOGIN
            # ------------------------------------------------

            session.clear()

            session["cliente_id"] = cliente["id"]

            return redirect(
                url_for("cliente_painel")
            )

        except Exception as erro:

            print("=================================")
            print("ERRO NO LOGIN DO CLIENTE")
            print("=================================")
            print(
                "TIPO:",
                type(erro).__name__
            )
            print(
                "ERRO:",
                erro
            )
            print("=================================")

            return (
                "Erro ao acessar a área do cliente.",
                500
            )

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template(
        "cliente_login.html"
    )


# ============================================================
# CLIENTE - PAINEL
# ============================================================

@app.route(
    "/cliente/painel"
)
@cliente_required
def cliente_painel():

    cliente_id = session.get(
        "cliente_id"
    )

    conexao = None
    cursor = None

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM orcamentos
            WHERE id = %s
            LIMIT 1
            """,
            (cliente_id,)
        )

        cliente = cursor.fetchone()

        if not cliente:

            session.clear()

            return redirect(
                url_for("cliente_login")
            )

        preparar_cliente(
            cliente
        )

        return render_template(
            "cliente_painel.html",
            cliente=cliente
        )

    except Exception as erro:

        print("=================================")
        print("ERRO AO CARREGAR ÁREA DO CLIENTE")
        print("=================================")
        print(
            "TIPO:",
            type(erro).__name__
        )
        print(
            "ERRO:",
            erro
        )
        print("=================================")

        return (
            "Erro ao carregar sua área.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# ============================================================
# CLIENTE - LOGOUT
# ============================================================

@app.route(
    "/cliente/logout"
)
def cliente_logout():

    session.pop(
        "cliente_id",
        None
    )

    return redirect(
        url_for("cliente_login")
    )


# ============================================================
# EXECUÇÃO LOCAL
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )