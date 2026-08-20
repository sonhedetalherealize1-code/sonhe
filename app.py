from flask import Flask, render_template, request

app = Flask(__name__)


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

        return render_template("obrigado.html")

    return render_template("orcamento.html")


if __name__ == "__main__":
    app.run(debug=True)