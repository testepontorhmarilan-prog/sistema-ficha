from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pandas as pd
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "super_seguro_rh"

def conectar():
    return sqlite3.connect("banco.db")

def criar_tabela():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS candidatos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        nascimento TEXT,
        cpf TEXT UNIQUE,
        rg TEXT,
        telefone TEXT,
        mae TEXT,
        pai TEXT,
        cidade TEXT,
        cargo TEXT,
        turno TEXT,
        escolaridade TEXT,
        score INTEGER
    )
    """)

    conn.commit()
    conn.close()

criar_tabela()

def calcular_score(escolaridade, cidade):

    score = 0

    escolaridade = escolaridade or ""
    cidade = cidade or ""

    if "completo" in escolaridade.lower():
        score += 10

    if cidade.lower() == "itapevi":
        score += 5

    return score

@app.route("/")
def index():
    return render_template("formulario.html")

@app.route("/salvar", methods=["POST"])
def salvar():

    try:

        nome = request.form.get("nome")
        nascimento = request.form.get("nascimento")
        cpf = request.form.get("cpf")
        rg = request.form.get("rg")
        telefone = request.form.get("telefone")
        mae = request.form.get("mae")
        pai = request.form.get("pai")
        cidade = request.form.get("cidade")
        cargo = request.form.get("cargo")
        turno = request.form.get("turno")
        escolaridade = request.form.get("escolaridade")

        score = calcular_score(escolaridade, cidade)

        conn = conectar()
        c = conn.cursor()

        c.execute("""
        INSERT INTO candidatos
        (nome,nascimento,cpf,rg,telefone,mae,pai,cidade,cargo,turno,escolaridade,score)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            nome,
            nascimento,
            cpf,
            rg,
            telefone,
            mae,
            pai,
            cidade,
            cargo,
            turno,
            escolaridade,
            score
        ))

        conn.commit()
        conn.close()

        ```python id="n7l3cx"
return """
<html>

<head>

<style>

body{
    font-family:Segoe UI;
    background:#eef2f7;
    display:flex;
    justify-content:center;
    align-items:center;
    height:100vh;
}

.box{
    background:white;
    padding:40px;
    border-radius:12px;
    box-shadow:0 5px 20px rgba(0,0,0,0.1);
    text-align:center;
}

.ok{
    color:#16a34a;
    font-size:22px;
    font-weight:bold;
}

p{
    color:#64748b;
}

</style>

<meta http-equiv="refresh" content="2;url=/">

</head>

<body>

<div class="box">

<div class="ok">
✅ Cadastro realizado com sucesso!
</div>

<p>
Redirecionando...
</p>

</div>

</body>

</html>
"""

    except sqlite3.IntegrityError:
        return "CPF já cadastrado!"

    except Exception as erro:
        return f"Erro no sistema: {erro}"

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        if request.form["usuario"] == "rh" and request.form["senha"] == "1234":

            session["logado"] = True

            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if not session.get("logado"):
        return redirect("/login")

    conn = conectar()

    df = pd.read_sql_query("SELECT * FROM candidatos", conn)

    total = len(df)

    conn.close()

    return render_template(
        "dashboard.html",
        dados=df.to_dict(orient="records"),
        total=total
    )

@app.route("/buscar", methods=["POST"])
def buscar():

    if not session.get("logado"):
        return redirect("/login")

    termo = request.form["termo"]

    conn = conectar()

    df = pd.read_sql_query(f"""
    SELECT * FROM candidatos
    WHERE cpf LIKE '%{termo}%'
    OR nome LIKE '%{termo}%'
    """, conn)

    conn.close()

    return df.to_html()

@app.route("/exportar")
def exportar():

    if not session.get("logado"):
        return redirect("/login")

    conn = conectar()

    df = pd.read_sql_query("SELECT * FROM candidatos", conn)

    if not os.path.exists("exports"):
        os.makedirs("exports")

    caminho = "exports/dados.xlsx"

    df.to_excel(caminho, index=False)

    conn.close()

    return send_file(caminho, as_attachment=True)

@app.route("/pdf/<cpf>")
def gerar_pdf(cpf):

    if not session.get("logado"):
        return redirect("/login")

    conn = conectar()

    df = pd.read_sql_query(
        f"SELECT * FROM candidatos WHERE cpf='{cpf}'",
        conn
    )

    conn.close()

    if df.empty:
        return "Candidato não encontrado"

    dados = df.iloc[0]

    if not os.path.exists("pdfs"):
        os.makedirs("pdfs")

    caminho = f"pdfs/{cpf}.pdf"

    doc = SimpleDocTemplate(caminho)

    styles = getSampleStyleSheet()

    conteudo = []

    conteudo.append(
        Paragraph("Ficha de Candidato", styles["Title"])
    )

    conteudo.append(Spacer(1, 10))

    for campo in dados.index:

        conteudo.append(
            Paragraph(f"{campo}: {dados[campo]}", styles["Normal"])
        )

        conteudo.append(Spacer(1, 5))

    doc.build(conteudo)

    return send_file(caminho, as_attachment=True)
