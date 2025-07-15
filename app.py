from flask import Flask, render_template, request, send_file
import os
from utils.curriculo_parser import analisar_curriculo
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULT_XLSX'] = 'matchscan_resultado.xlsx'
app.config['RESULT_PDF'] = 'matchscan_resultado.pdf'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    arquivos = request.files.getlist('curriculos')
    vaga = request.form.get('vaga')

    if not arquivos or not vaga:
        return "Envie currículos e a descrição da vaga."

    textos, nomes, dados = [], [], []

    for arquivo in arquivos:
        if arquivo.filename.endswith('.pdf'):
            path = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
            arquivo.save(path)
            info = analisar_curriculo(path)
            nomes.append(arquivo.filename)
            textos.append(info['texto'])
            dados.append(info)

    vetor = TfidfVectorizer(stop_words='english')
    matriz = vetor.fit_transform([vaga] + textos)
    scores = cosine_similarity(matriz[0:1], matriz[1:]).flatten()

    resultados = []
    for i, score in enumerate(scores):
        match = round(score * 100, 2)
        match = max(match, 1.0)
        resultados.append({
            'arquivo': nomes[i],
            'match': match,
            'email': dados[i]['email'],
            'linkedin': dados[i]['linkedin']
        })

    resultados.sort(key=lambda x: x['match'], reverse=True)

    # Exporta Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Ranking"
    ws.append(['Arquivo', 'Match (%)', 'Email', 'LinkedIn'])
    for r in resultados:
        ws.append([r['arquivo'], r['match'], r['email'], r['linkedin']])
    wb.save(app.config['RESULT_XLSX'])

    # Exporta PDF
    c = canvas.Canvas(app.config['RESULT_PDF'], pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 760, "Resultado - MatchScan")
    c.setFont("Helvetica", 12)
    y = 720
    for r in resultados:
        c.drawString(40, y, r['arquivo'][:25])
        c.drawString(200, y, f"{r['match']}%")
        c.drawString(300, y, (r['email'] or '-')[:20])
        c.drawString(460, y, (r['linkedin'] or '-')[:25])
        y -= 20
        if y < 40:
            c.showPage()
            y = 750
    c.save()

    # HTML resultado
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br" data-theme="light">
    <head>
        <meta charset="UTF-8">
        <title>Resultado</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background: #f5f5fa; font-family: 'Segoe UI', sans-serif; }}
            .header {{
                background: linear-gradient(to right, #7b2cbf, #9d4edd);
                color: white;
                padding: 40px 20px;
                border-bottom-left-radius: 30px;
                border-bottom-right-radius: 30px;
                text-align: center;
                position: relative;
                z-index: 2;
            }}
            #particles-js {{ position: fixed; width: 100%; height: 100%; z-index: 1; top: 0; left: 0; }}
            .container {{
                max-width: 1000px;
                margin: 40px auto;
                background: white;
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                position: relative;
                z-index: 2;
            }}
            .match-high {{ color: green; font-weight: bold; }}
            .match-low {{ color: red; font-weight: bold; }}
            footer {{
                position: fixed;
                bottom: 10px;
                width: 100%;
                text-align: center;
                font-size: 0.9rem;
                color: #888;
                z-index: 3;
            }}
            [data-theme="dark"] body {{ background: #1b1b2f; color: #f0f0f0; }}
            [data-theme="dark"] .container {{ background: #2c2c3e; color: white; }}
            [data-theme="dark"] .header {{
                background: linear-gradient(to right, #3a0ca3, #7209b7);
                color: #fff;
            }}
            [data-theme="dark"] footer {{ color: #aaa; }}
        </style>
    </head>
    <body>
        <div id="particles-js"></div>
        <div class="header">
            <h1>Ranking de Aderência</h1>
            <p>Veja quais candidatos se destacam 📊</p>
            <button id="toggle-theme" class="btn btn-light border-0 position-absolute top-0 end-0 m-3" title="Alternar tema">🌓</button>
        </div>
        <div class="container">
            <table class="table table-bordered table-hover">
                <thead class="table-light">
                    <tr><th>#</th><th>Arquivo</th><th>Match (%)</th><th>Email</th><th>LinkedIn</th></tr>
                </thead>
                <tbody>
    """

    for i, r in enumerate(resultados, 1):
        cls = "match-high" if r['match'] >= 70 else "match-low" if r['match'] <= 30 else ""
        html += f"<tr><td>{i}</td><td>{r['arquivo']}</td><td class='{cls}'>{r['match']}%</td><td>{r['email']}</td><td>{r['linkedin']}</td></tr>"

    html += """
                </tbody>
            </table>
            <div class="text-center mt-4">
                <a href="/" class="btn btn-outline-secondary me-2">🔁 Nova Análise</a>
                <a href="/download/excel" class="btn btn-primary me-2">📥 Excel</a>
                <a href="/download/pdf" class="btn btn-danger">📄 PDF</a>
            </div>
        </div>
        <footer>© Dev Larissa Campos</footer>
        <script src="/static/js/particles.min.js"></script>
        <script>
            particlesJS.load('particles-js', '/static/js/particles.json');
            const html = document.documentElement;
            const saved = localStorage.getItem("theme");
            if (saved) html.setAttribute("data-theme", saved);
            document.getElementById("toggle-theme").addEventListener("click", () => {
                const novo = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
                html.setAttribute("data-theme", novo);
                localStorage.setItem("theme", novo);
            });
        </script>
    </body>
    </html>
    """

    return html

@app.route('/download/excel')
def download_excel():
    return send_file(app.config['RESULT_XLSX'], as_attachment=True)

@app.route('/download/pdf')
def download_pdf():
    return send_file(app.config['RESULT_PDF'], as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
