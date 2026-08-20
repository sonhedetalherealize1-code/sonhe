from flask import Flask, render_template, request, redirect, url_for, session
import os
import mysql.connector
from functools import wraps
from datetime import date, datetime
import traceback


app = Flask(__name__)


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

app.secret_key = os.getenv(
    "SECRET_KEY",
    "chave-temporaria-apenas-local"
)


# ==========================================================
# CONEXÃO COM O MYSQL
# ==========================================================

def conectar_banco():

    conexao = mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE")
    )

    print("Conectado ao MySQL com sucesso!")

    return conexao


# ==========================================================
# PROTEÇÃO DO ADMINISTRADOR
# ==========================================================

def admin_required(func):

    @wraps(func)
    def verificar_login(*args, **kwargs):

        if not session.get("admin_logado"):
            return redirect(url_for("admin_login"))

        return func(*args, **kwargs)

    return verificar_login


# ==========================================================
# CLASSIFICAÇÃO DO EVENTO
# ==========================================================

def classificar_evento(data_evento):

    if not data_evento:
        return {
            "status": "Sem data",
            "classe": "sem-data",
            "dias": None
        }

    try:

        # Caso venha como datetime
        if isinstance(data_evento, datetime):
            data_evento = data_evento.date()

        # Caso venha como string
        elif isinstance(data_evento, str):

            data_evento = datetime.strptime(
                data_evento,
                "%Y-%m-%d"
            ).date()

        hoje = date.today()

        diferenca = (data_evento - hoje).days


        # ==============================================
        # EVENTO JÁ PASSOU
        # ==============================================

        if diferenca < 0:

            return {
                "status": "Concluído",
                "classe": "concluido",
                "dias": abs(diferenca)
            }


        # ==============================================
        # EVENTO HOJE
        # ==============================================

        if diferenca == 0:

            return {
                "status": "É hoje!",
                "classe": "hoje",
                "dias": 0
            }


        # ==============================================
        # ATÉ 7 DIAS
        # ==============================================

        if diferenca <= 7:

            return {
                "status": "Urgente",
                "classe": "urgente",
                "dias": diferenca
            }


        # ==============================================
        # ATÉ 30 DIAS
        # ==============================================

        if diferenca <= 30:

            return {
                "status": "Próximo",
                "classe": "proximo",
                "dias": diferenca
            }


        # ==============================================
        # MAIS DE 30 DIAS
        # ==============================================

        return {
            "status": "Agendado",
            "classe": "agendado",
            "dias": diferenca
        }


    except Exception as erro:

        print("Erro ao classificar data do evento:")
        print(erro)

        return {
            "status": "Data inválida",
            "classe": "sem-data",
            "dias": None
        }


# ==========================================================
# PÁGINA INICIAL - CONVITE
# ==========================================================

@app.route("/")
def convite():

    return render_template("convite.html")


# ==========================================================
# APRESENTAÇÃO / VÍDEO
# ==========================================================

@app.route("/apresentacao")
def apresentacao():

    return render_template("apresentacao.html")


# ==========================================================
# SOBRE A YASMINI
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

        # ==================================================
        # PEGAR DADOS DO FORMULÁRIO
        # ==================================================

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


        # ==================================================
        # LOG DOS DADOS RECEBIDOS
        # ==================================================

        print("")
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

            # ==================================================
            # CONECTAR AO MYSQL
            # ==================================================

            conexao = conectar_banco()

            cursor = conexao.cursor()


            # ==================================================
            # INSERIR ORÇAMENTO
            # ==================================================

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


            print("=================================")
            print("ORÇAMENTO SALVO COM SUCESSO!")
            print("=================================")


            # ==================================================
            # PÁGINA DE AGRADECIMENTO
            # ==================================================

            return render_template(
                "obrigado.html"
            )


        except Exception as erro:

            print("")
            print("=================================")
            print("ERRO AO SALVAR ORÇAMENTO")
            print("=================================")

            print("TIPO DO ERRO:")
            print(type(erro).__name__)

            print("ERRO:")
            print(erro)

            print("=================================")

            traceback.print_exc()

            print("=================================")


            return (
                "Erro ao salvar o orçamento. "
                "Verifique os logs do Railway.",
                500
            )


        finally:

            if cursor:

                try:
                    cursor.close()
                except:
                    pass


            if conexao:

                try:
                    conexao.close()
                except:
                    pass


    # ==================================================
    # GET
    # ==================================================

    return render_template(
        "orcamento.html"
    )


# ==========================================================
# ADMINISTRADOR - LOGIN
# ==========================================================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        usuario = request.form.get("usuario")
        senha = request.form.get("senha")


        # ==================================================
        # LOGIN VINDO DAS VARIABLES DO RAILWAY
        # ==================================================

        usuario_correto = os.getenv(
            "ADMIN_USER"
        )

        senha_correta = os.getenv(
            "ADMIN_PASSWORD"
        )


        # ==================================================
        # VERIFICAR LOGIN
        # ==================================================

        if (
            usuario == usuario_correto
            and senha == senha_correta
        ):

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


# ==========================================================
# ADMINISTRADOR - PAINEL
# ==========================================================

@app.route("/admin/painel")
@admin_required
def admin_painel():

    conexao = None
    cursor = None


    try:

        # ==================================================
        # PARÂMETROS DA PESQUISA
        # ==================================================

        busca = request.args.get(
            "busca",
            ""
        ).strip()


        ordem = request.args.get(
            "ordem",
            "recentes"
        )


        # ==================================================
        # CONECTAR
        # ==================================================

        conexao = conectar_banco()

        cursor = conexao.cursor(
            dictionary=True
        )


        # ==================================================
        # CONSULTA BASE
        # ==================================================

        comando = """
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
        """


        parametros = []


        # ==================================================
        # PESQUISA POR NOME
        # ==================================================

        if busca:

            comando += """
                WHERE nome LIKE %s
            """

            parametros.append(
                "%" + busca + "%"
            )


        # ==================================================
        # ORDENAÇÃO
        # ==================================================

        if ordem == "antigos":

            comando += """
                ORDER BY data_envio ASC
            """

        elif ordem == "evento_proximo":

            comando += """
                ORDER BY data_evento ASC
            """

        elif ordem == "evento_longe":

            comando += """
                ORDER BY data_evento DESC
            """

        else:

            comando += """
                ORDER BY data_envio DESC
            """


        # ==================================================
        # EXECUTAR
        # ==================================================

        cursor.execute(
            comando,
            parametros
        )


        clientes = cursor.fetchall()


        # ==================================================
        # CLASSIFICAR CADA CLIENTE
        # ==================================================

        for cliente in clientes:

            informacao_evento = classificar_evento(
                cliente.get("data_evento")
            )


            cliente["status_evento"] = (
                informacao_evento["status"]
            )


            cliente["classe_evento"] = (
                informacao_evento["classe"]
            )


            cliente["dias_evento"] = (
                informacao_evento["dias"]
            )


        # ==================================================
        # LOG
        # ==================================================

        print("")
        print("=================================")
        print("PAINEL ADMINISTRATIVO")
        print("=================================")
        print("Clientes encontrados:", len(clientes))
        print("Busca:", busca)
        print("Ordem:", ordem)
        print("=================================")


        return render_template(
            "admin_painel.html",
            clientes=clientes,
            busca=busca,
            ordem=ordem
        )


    except Exception as erro:

        print("")
        print("=================================")
        print("ERRO AO BUSCAR CLIENTES")
        print("=================================")

        print("TIPO DO ERRO:")
        print(type(erro).__name__)

        print("ERRO:")
        print(erro)

        print("=================================")

        traceback.print_exc()

        print("=================================")


        return (
            "Erro ao carregar os clientes. "
            "Verifique os logs do Railway.",
            500
        )


    finally:

        if cursor:

            try:
                cursor.close()
            except:
                pass


        if conexao:

            try:
                conexao.close()
            except:
                pass


# ==========================================================
# ADMINISTRADOR - VER CLIENTE
# ==========================================================

@app.route("/admin/cliente/<int:id>")
@admin_required
def admin_cliente(id):

    conexao = None
    cursor = None


    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(
            dictionary=True
        )


        # ==================================================
        # BUSCAR CLIENTE
        # ==================================================

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
            """,
            (id,)
        )


        cliente = cursor.fetchone()


        # ==================================================
        # VERIFICAR SE EXISTE
        # ==================================================

        if not cliente:

            return (
                "Cliente não encontrado.",
                404
            )


        # ==================================================
        # CLASSIFICAR EVENTO
        # ==================================================

        informacao_evento = classificar_evento(
            cliente.get("data_evento")
        )


        cliente["status_evento"] = (
            informacao_evento["status"]
        )


        cliente["classe_evento"] = (
            informacao_evento["classe"]
        )


        cliente["dias_evento"] = (
            informacao_evento["dias"]
        )


        return render_template(
            "admin_cliente.html",
            cliente=cliente
        )


    except Exception as erro:

        print("")
        print("=================================")
        print("ERRO AO BUSCAR CLIENTE")
        print("=================================")

        print("ID:", id)

        print("TIPO DO ERRO:")
        print(type(erro).__name__)

        print("ERRO:")
        print(erro)

        print("=================================")

        traceback.print_exc()

        print("=================================")


        return (
            "Erro ao carregar cliente. "
            "Verifique os logs do Railway.",
            500
        )


    finally:

        if cursor:

            try:
                cursor.close()
            except:
                pass


        if conexao:

            try:
                conexao.close()
            except:
                pass


# ==========================================================
# ADMINISTRADOR - EXCLUIR CLIENTE
# ==========================================================

@app.route(
    "/admin/cliente/<int:id>/excluir",
    methods=["GET", "POST"]
)
@admin_required
def admin_excluir_cliente(id):

    conexao = None
    cursor = None


    try:

        conexao = conectar_banco()

        cursor = conexao.cursor()


        # ==================================================
        # VERIFICAR SE EXISTE
        # ==================================================

        cursor.execute(
            """
            SELECT id
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


        # ==================================================
        # EXCLUIR
        # ==================================================

        cursor.execute(
            """
            DELETE FROM orcamentos
            WHERE id = %s
            """,
            (id,)
        )


        conexao.commit()


        print("")
        print("=================================")
        print("ORÇAMENTO EXCLUÍDO")
        print("ID:", id)
        print("=================================")


        return redirect(
            url_for("admin_painel")
        )


    except Exception as erro:

        print("")
        print("=================================")
        print("ERRO AO EXCLUIR CLIENTE")
        print("=================================")

        print("ID:", id)

        print("TIPO:", type(erro).__name__)

        print("ERRO:", erro)

        print("=================================")

        traceback.print_exc()


        return (
            "Erro ao excluir cliente.",
            500
        )


    finally:

        if cursor:

            try:
                cursor.close()
            except:
                pass


        if conexao:

            try:
                conexao.close()
            except:
                pass


# ==========================================================
# ADMINISTRADOR - LOGOUT
# ==========================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# ==========================================================
# EXECUÇÃO LOCAL
# ==========================================================

if __name__ == "__main__":

    porta = int(
        os.getenv(
            "PORT",
            5000
        )
    )


    app.run(
        host="0.0.0.0",
        port=porta,
        debug=True
    )