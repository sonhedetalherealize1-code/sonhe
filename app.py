from flask import Flask, render_template, request, redirect, url_for, session
import os
import mysql.connector
from functools import wraps


app = Flask(__name__)

# ==========================================
# CONFIGURAÇÕES
# ==========================================

# Chave usada para proteger as sessões do administrador.
# No Railway, crie uma variável chamada SECRET_KEY.
app.secret_key = os.getenv("SECRET_KEY", "chave-temporaria-apenas-local")


# ==========================================
# CONEXÃO COM O BANCO DE DADOS
# ==========================================

def conectar_banco():

    conexao = mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE")
    )

    return conexao


# ==========================================
# PROTEÇÃO DO ADMIN
# ==========================================

def admin_required(func):

    @wraps(func)
    def verificar_login(*args, **kwargs):

        if not session.get("admin_logado"):
            return redirect(url_for("admin_login"))

        return func(*args, **kwargs)

    return verificar_login


# ==========================================
# CONVITE
# ==========================================

@app.route("/")
def convite():

    return render_template("convite.html")


# ==========================================
# APRESENTAÇÃO / VÍDEO
# ==========================================

@app.route("/apresentacao")
def apresentacao():

    return render_template("apresentacao.html")


# ==========================================
# SOBRE A YASMINI
# ==========================================

@app.route("/sobre")
def sobre():

    return render_template("sobre.html")


# ==========================================
# ORÇAMENTO
# ==========================================

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
        # MOSTRAR NO TERMINAL
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


        # ==========================================
        # SALVAR NO MYSQL
        # ==========================================

        try:

            conexao = conectar_banco()

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

            cursor.execute(comando, valores)

            conexao.commit()

            print("ORÇAMENTO SALVO COM SUCESSO!")

            cursor.close()
            conexao.close()


        except Exception as erro:

            print("=================================")
            print("ERRO AO SALVAR ORÇAMENTO")
            print("=================================")

            print(erro)

            return "Erro ao salvar o orçamento.", 500


        # ==========================================
        # PÁGINA DE AGRADECIMENTO
        # ==========================================

        return render_template("obrigado.html")


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
        # PEGAR LOGIN DAS VARIABLES DO RAILWAY
        # ==========================================

        usuario_correto = os.getenv("ADMIN_USER")
        senha_correta = os.getenv("ADMIN_PASSWORD")


        # ==========================================
        # VERIFICAR LOGIN
        # ==========================================

        if usuario == usuario_correto and senha == senha_correta:

            session["admin_logado"] = True

            return redirect(url_for("admin_painel"))


        # Login incorreto

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

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(dictionary=True)


        # ==========================================
        # BUSCAR TODOS OS ORÇAMENTOS
        # ==========================================

        cursor.execute("""
            SELECT *
            FROM orcamentos
            ORDER BY data_envio DESC
        """)

        clientes = cursor.fetchall()


        cursor.close()
        conexao.close()


        return render_template(
            "admin_painel.html",
            clientes=clientes
        )


    except Exception as erro:

        print("ERRO AO BUSCAR CLIENTES:")
        print(erro)

        return "Erro ao carregar os clientes.", 500


# ==================================================
# ADMINISTRADOR - VER CLIENTE
# ==================================================

@app.route("/admin/cliente/<int:id>")
@admin_required
def admin_cliente(id):

    try:

        conexao = conectar_banco()

        cursor = conexao.cursor(dictionary=True)


        # ==========================================
        # BUSCAR CLIENTE
        # ==========================================

        cursor.execute("""
            SELECT *
            FROM orcamentos
            WHERE id = %s
        """, (id,))


        cliente = cursor.fetchone()


        cursor.close()
        conexao.close()


        # ==========================================
        # CLIENTE NÃO ENCONTRADO
        # ==========================================

        if not cliente:

            return "Cliente não encontrado.", 404


        return render_template(
            "admin_cliente.html",
            cliente=cliente
        )


    except Exception as erro:

        print("ERRO AO BUSCAR CLIENTE:")
        print(erro)

        return "Erro ao carregar cliente.", 500


# ==================================================
# ADMINISTRADOR - LOGOUT
# ==================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("admin_login"))


# ==================================================
# EXECUÇÃO LOCAL
# ==================================================

if __name__ == "__main__":

    app.run(debug=True)