from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import PyPDF2
from io import BytesIO

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Criar pasta de uploads se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# ... existing code ...
PROMPTS_RESUMO = {
    'geral': {
        'simples': 'Faça um resumo breve e objetivo do texto a seguir.',
        'analitico': 'Leia o texto abaixo e produza um resumo destacando os principais argumentos, causas e consequências.',
        'critico': 'Resuma o texto a seguir e inclua uma análise crítica dos pontos fortes e fracos apresentados.',
        'topicos': 'Gere um resumo do texto abaixo em formato de tópicos, listando as ideias principais.',
        'apresentacao': 'Crie um resumo do texto a seguir, adaptado para ser apresentado oralmente de forma clara e concisa.',
        'academico': 'Elabore um resumo acadêmico do texto, seguindo as normas da ABNT e destacando objetivo, metodologia, resultados e conclusão.'
    },
    'medicina': {
        'clinico': 'Faça um resumo clínico do caso apresentado, destacando sintomas, diagnóstico, tratamento e prognóstico.',
        'cientifico': 'Resuma o artigo científico abaixo, enfatizando objetivo, metodologia, resultados e conclusões relevantes para a prática médica.',
        'prontuario': 'Elabore um resumo de prontuário médico, destacando histórico, exames realizados e condutas adotadas.'
    },
    'direito': {
        'juridico': 'Elabore um resumo jurídico do texto, destacando os principais argumentos, fundamentos legais e decisões judiciais citadas.',
        'legislacao': 'Resuma a legislação apresentada, apontando os pontos-chave e possíveis impactos práticos.',
        'jurisprudencia': 'Faça um resumo da jurisprudência citada, destacando a tese jurídica e sua aplicabilidade.'
    },
    'licitacoes': {
        'edital': 'Faça um resumo do edital de licitação, destacando objeto, critérios de participação, prazos e principais exigências.',
        'processo': 'Resuma o processo licitatório descrito, indicando etapas, documentos necessários e critérios de julgamento.',
        'contrato': 'Elabore um resumo do contrato administrativo, destacando objeto, prazo, valor e principais cláusulas.'
    }
}

def extrair_texto_pdf(arquivo_pdf):
    """Extrai texto de um arquivo PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(arquivo_pdf)
        texto_completo = ""
        
        for pagina in pdf_reader.pages:
            texto_completo += pagina.extract_text() + "\n"
        
        return texto_completo.strip()
    except Exception as e:
        return f"Erro ao extrair texto do PDF: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo foi enviado'}), 400
    
    arquivo = request.files['arquivo']
    
    if arquivo.filename == '':
        return jsonify({'erro': 'Nenhum arquivo selecionado'}), 400
    
    if arquivo and arquivo.filename.lower().endswith('.pdf'):
        try:
            # Extrair texto diretamente do arquivo em memória
            texto_extraido = extrair_texto_pdf(BytesIO(arquivo.read()))
            
            if texto_extraido.startswith("Erro"):
                return jsonify({'erro': texto_extraido}), 500
            
            return jsonify({
                'sucesso': True,
                'texto': texto_extraido,
                'nome_arquivo': arquivo.filename
            })
        except Exception as e:
            return jsonify({'erro': f'Erro ao processar PDF: {str(e)}'}), 500
    else:
        return jsonify({'erro': 'Apenas arquivos PDF são aceitos'}), 400

@app.route('/gerar_prompt', methods=['POST'])
def gerar_prompt():
    dados = request.json
    categoria = dados.get('categoria', 'geral')
    tipo = dados.get('tipo', 'simples')
    texto_extraido = dados.get('texto', '')
    
    # Busca o prompt correspondente
    if categoria in PROMPTS_RESUMO and tipo in PROMPTS_RESUMO[categoria]:
        prompt_base = PROMPTS_RESUMO[categoria][tipo]
        
        if texto_extraido:
            prompt_gerado = f"{prompt_base}\n\n{texto_extraido}"
        else:
            prompt_gerado = f"{prompt_base}\n\n[Insira aqui o texto a ser resumido]"
    else:
        prompt_gerado = "Prompt não encontrado para a categoria e tipo selecionados."
    
    return jsonify({'prompt': prompt_gerado})

if __name__ == '__main__':
    app.run(debug=True)