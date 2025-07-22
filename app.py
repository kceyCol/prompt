from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from io import BytesIO

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROMPTS_FOLDER'] = 'prompts'

# Criar pasta de uploads se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Criar pasta de prompts se não existir
if not os.path.exists(app.config['PROMPTS_FOLDER']):
    os.makedirs(app.config['PROMPTS_FOLDER'])
    # Criar subpastas para cada categoria
    for categoria in ['geral', 'medicina', 'direito', 'licitacoes']:
        os.makedirs(os.path.join(app.config['PROMPTS_FOLDER'], categoria), exist_ok=True)

# Estrutura para armazenar os tipos de prompts disponíveis por categoria
PROMPTS_TIPOS = {
    'geral': ['simples', 'analitico', 'critico', 'topicos', 'apresentacao', 'academico'],
    'medicina': ['artigo_cientifico', 'relato_caso', 'pico', 'tecnica_cirurgica', 
                'guideline', 'journal_club', 'estado_arte', 'impacto_clinico', 'translacional'],
    'direito': ['juridico', 'legislacao', 'jurisprudencia'],
    'licitacoes': ['edital', 'processo', 'contrato']
}

def carregar_prompt(categoria, tipo):
    """Carrega o prompt de um arquivo externo"""
    caminho_arquivo = os.path.join(app.config['PROMPTS_FOLDER'], categoria, f"{tipo}.txt")
    
    # Se o arquivo existir, carrega o conteúdo
    if os.path.exists(caminho_arquivo):
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                return arquivo.read().strip()
        except Exception as e:
            print(f"Erro ao ler arquivo de prompt {caminho_arquivo}: {str(e)}")
            return None
    
    # Se o arquivo não existir, retorna None
    return None

def extrair_texto_pdf(arquivo_pdf):
    """Extrai texto de um arquivo PDF usando PyMuPDF"""
    try:
        # Abrir o PDF com PyMuPDF
        documento = fitz.open(stream=arquivo_pdf.read(), filetype="pdf")
        texto_completo = ""
        
        # Extrair texto de cada página
        for pagina in documento:
            texto_completo += pagina.get_text() + "\n"
        
        documento.close()
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
            # Extrair texto diretamente do arquivo
            texto_extraido = extrair_texto_pdf(arquivo)
            
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
    categoria = dados.get('categoria', 'medicina')  # Alterado para 'medicina' como padrão
    tipo = dados.get('tipo', 'artigo_cientifico')  # Alterado para 'artigo_cientifico' como padrão
    
    # Tenta carregar o prompt do arquivo externo
    prompt_base = carregar_prompt(categoria, tipo)
    
    # Se não encontrar o arquivo ou ocorrer erro na leitura, usa um prompt padrão
    if prompt_base is None:
        prompt_base = "Faça um resumo do texto a seguir."
        print(f"Aviso: Prompt não encontrado para {categoria}/{tipo}. Usando prompt padrão.")
    
    prompt_gerado = f"{prompt_base}\n\n[Insira aqui o texto a ser resumido ou anexe o arquivo PDF]"
    
    return jsonify({'prompt': prompt_gerado})

if __name__ == '__main__':
    app.run(debug=True)