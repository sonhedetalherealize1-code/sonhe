from flask import Flask, render_template, request, redirect, url_for, session
import os
import mysql.connector
from functools import wraps
from datetime import date


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

    hoje = date.today()

    diferenca = (data_evento - hoje).days

    # Evento já passou
    if diferenca < 0:
        return "Concluído", "concluido", diferenca

    # Evento é hoje
    elif diferenca == 0:
        return "Hoje", "hoje", diferenca

    # Até 7 dias
    elif diferenca <= 7:
        return "Urgente", "urgente", diferenca

    # Até 30 dias
    elif diferenca <= 30:
        return "Atenção", "atencao", diferenca

    # Mais de 30 dias
    else:
        return "Pendente", "pendente", diferenca


def preparar_cliente(cliente):

    if not cliente:
        return cliente

    status, status_classe, dias = calcular_status(
        cliente.get("data_evento")
    )

    cliente["status"] = status
    cliente["status_classe"] = status_classe
    cliente["dias_restantes"] = dias

    return cliente


# ============================================================
# PROTEÇÃO DO ADMINISTRADOR
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
# SOBRE
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
                "TIPO DO ERRO:",
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
# ADMIN
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
            and
            senha == senha_correta
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
# PAINEL ADMIN
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

        pesquisa = request.args.get(
            "pesquisa",
            ""
        ).strip()

        ordem = request.args.get(
            "ordem",
            "recente"
        )

        # ----------------------------------------------------
        # ORDENAÇÃO
        # ----------------------------------------------------

        if ordem == "data_asc":

            ordenacao = "data_evento ASC"

        elif ordem == "data_desc":

            ordenacao = "data_evento DESC"

        elif ordem == "nome":

            ordenacao = "nome ASC"

        else:

            ordenacao = "data_envio DESC"


        # ----------------------------------------------------
        # PESQUISA
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
# VER DETALHES DO CLIENTE
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

            return (
                "Cliente não encontrado.",
                404
            )


        preparar_cliente(
            cliente
        )


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
# EXCLUIR CLIENTE
# ============================================================

@app.route(
    "/admin/excluir/<int:id>",
    methods=["GET", "POST"]
)
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

        print(
            "ORÇAMENTO EXCLUÍDO:",
            id
        )

        return redirect(
            url_for("admin_painel")
        )


    except Exception as erro:

        print("=================================")
        print("ERRO AO EXCLUIR CLIENTE")
        print("=================================")

        print(
            "ID:",
            id
        )

        print(
            "ERRO:",
            erro
        )

        print("=================================")

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
# COMPATIBILIDADE COM A ROTA ANTIGA
# ============================================================

@app.route(
    "/admin/excluir-cliente/<int:id>",
    methods=["GET", "POST"]
)
@admin_required
def admin_excluir(id):

    return excluir_cliente(id)


# ============================================================
# LOGOUT ADMIN
# ============================================================

@app.route(
    "/admin/logout"
)
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


        # ----------------------------------------------------
        # DEIXAR SOMENTE NÚMEROS
        # ----------------------------------------------------

        whatsapp_limpo = "".join(
            caractere
            for caractere in whatsapp
            if caractere.isdigit()
        )


        if not whatsapp_limpo:

            return render_template(
                "cliente_login.html",
                erro="Digite seu WhatsApp."
            )


        conexao = None
        cursor = None


        try:

            conexao = conectar_banco()

            cursor = conexao.cursor(
                dictionary=True
            )


            # ------------------------------------------------
            # BUSCAR CLIENTE
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT *
                FROM orcamentos

                WHERE REPLACE(
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
                ) = %s

                ORDER BY id DESC

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


            print("=================================")
            print("LOGIN DO CLIENTE")
            print("=================================")
            print(
                "ID:",
                cliente["id"]
            )
            print(
                "Nome:",
                cliente["nome"]
            )
            print(
                "WhatsApp:",
                cliente["whatsapp"]
            )
            print("=================================")


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

            return render_template(
                "cliente_login.html",

                erro=(
                    "Não foi possível acessar "
                    "sua área."
                )
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
# PAINEL DO CLIENTE
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


        # ----------------------------------------------------
        # BUSCAR NOVAMENTE O CLIENTE NO BANCO
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM orcamentos
            WHERE id = %s
            """,
            (
                cliente_id,
            )
        )


        cliente = cursor.fetchone()


        # ----------------------------------------------------
        # CLIENTE FOI EXCLUÍDO
        # ----------------------------------------------------

        if not cliente:

            session.pop(
                "cliente_id",
                None
            )

            return redirect(
                url_for("cliente_login")
            )


        # ----------------------------------------------------
        # CALCULAR STATUS E DIAS
        # ----------------------------------------------------

        preparar_cliente(
            cliente
        )


        # ----------------------------------------------------
        # GARANTIR QUE A VARIÁVEL CLIENTE
        # SEJA ENVIADA AO HTML
        # ----------------------------------------------------

        print("=================================")
        print("PAINEL DO CLIENTE")
        print("=================================")

        print(
            "ID:",
            cliente.get("id")
        )

        print(
            "Nome:",
            cliente.get("nome")
        )

        print(
            "Evento:",
            cliente.get("evento")
        )

        print(
            "Data:",
            cliente.get("data_evento")
        )

        print(
            "Status:",
            cliente.get("status")
        )

        print(
            "Dias restantes:",
            cliente.get("dias_restantes")
        )

        print("=================================")


        return render_template(
            "cliente_painel.html",

            cliente=cliente,

            dias_restantes=cliente.get(
                "dias_restantes"
            ),

            status=cliente.get(
                "status"
            ),

            status_classe=cliente.get(
                "status_classe"
            )
        )


    except Exception as erro:

        print("=================================")
        print("ERRO AO CARREGAR PAINEL DO CLIENTE")
        print("=================================")

        print(
            "ID:",
            cliente_id
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
            "Erro ao carregar sua área.",
            500
        )


    finally:

        if cursor:

            cursor.close()

        if conexao:

            conexao.close()


# ============================================================
# LOGOUT CLIENTE
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