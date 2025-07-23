from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
# Removido: import fitz  # PyMuPDF
from io import BytesIO
import socket

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

# Removida função extrair_texto_pdf

@app.route('/')
def index():
    return render_template('index.html')

# Removida rota /upload_pdf

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
    
    prompt_gerado = f"{prompt_base}\n\n[Insira aqui o texto a ser resumido]"
    
    return jsonify({'prompt': prompt_gerado})

@app.route('/config')
def config():
    return render_template('config.html')

@app.route('/api/prompts/<categoria>')
def listar_prompts(categoria):
    """Lista todos os prompts disponíveis para uma categoria"""
    if categoria not in PROMPTS_TIPOS:
        return jsonify({'erro': 'Categoria não encontrada'}), 404
    
    prompts = []
    for tipo in PROMPTS_TIPOS[categoria]:
        caminho_arquivo = os.path.join(app.config['PROMPTS_FOLDER'], categoria, f"{tipo}.txt")
        existe = os.path.exists(caminho_arquivo)
        prompts.append({
            'tipo': tipo,
            'nome': tipo.replace('_', ' ').title(),
            'existe': existe
        })
    
    return jsonify({'prompts': prompts})

@app.route('/api/prompt/<categoria>/<tipo>')
def obter_prompt(categoria, tipo):
    """Obtém o conteúdo de um prompt específico"""
    if categoria not in PROMPTS_TIPOS or tipo not in PROMPTS_TIPOS[categoria]:
        return jsonify({'erro': 'Prompt não encontrado'}), 404
    
    conteudo = carregar_prompt(categoria, tipo)
    if conteudo is None:
        return jsonify({'erro': 'Arquivo de prompt não encontrado'}), 404
    
    return jsonify({'conteudo': conteudo})

@app.route('/api/prompt/<categoria>/<tipo>', methods=['POST'])
def salvar_prompt(categoria, tipo):
    """Salva o conteúdo de um prompt"""
    if categoria not in PROMPTS_TIPOS or tipo not in PROMPTS_TIPOS[categoria]:
        return jsonify({'erro': 'Prompt não encontrado'}), 404
    
    dados = request.json
    conteudo = dados.get('conteudo', '')
    
    caminho_arquivo = os.path.join(app.config['PROMPTS_FOLDER'], categoria, f"{tipo}.txt")
    
    try:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
            arquivo.write(conteudo)
        
        return jsonify({'sucesso': True, 'mensagem': 'Prompt salvo com sucesso'})
    except Exception as e:
        return jsonify({'erro': f'Erro ao salvar prompt: {str(e)}'}), 500

@app.route('/api/server-info')
def server_info():
    """Retorna informações do servidor"""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Tentar obter informações de rede mais detalhadas
        interfaces = []
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            interfaces.append({
                                'interface': interface,
                                'ip': ip
                            })
        except ImportError:
            # netifaces não está disponível
            pass
        
        return jsonify({
            'hostname': hostname,
            'local_ip': local_ip,
            'interfaces': interfaces
        })
    except Exception as e:
        return jsonify({
            'hostname': 'unknown',
            'local_ip': 'localhost',
            'interfaces': [],
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)