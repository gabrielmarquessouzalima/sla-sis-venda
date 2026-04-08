import sqlite3
import os

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DB_NAME = 'sistema_vendas.db'

def inicializar_db():
    """Cria o banco de dados e as tabelas caso não existam."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de Produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL
        )
    ''')
    
    # Tabela de Vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            quantidade INTEGER,
            total REAL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# --- FUNÇÕES DE MANIPULAÇÃO ---

def cadastrar_produto(nome, preco, estoque):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', 
                       (nome, preco, estoque))
        conn.commit()
        conn.close()
        print(f"\n✅ Produto '{nome}' cadastrado com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro ao cadastrar: {e}")

def listar_produtos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()
    
    if not produtos:
        print("\n⚠️ O estoque está vazio.")
        return

    print("\n" + "="*45)
    print(f"{'ID':<4} | {'Nome':<20} | {'Preço':<10} | {'Qtd'}")
    print("-" * 45)
    for p in produtos:
        print(f"{p[0]:<4} | {p[1]:<20} | R$ {p[2]:<7.2f} | {p[3]}")
    print("="*45)

def realizar_venda(produto_id, quantidade):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verifica se o produto existe e tem estoque
    cursor.execute('SELECT nome, preco, estoque FROM produtos WHERE id = ?', (produto_id,))
    produto = cursor.fetchone()
    
    if produto:
        nome_prod, preco_prod, estoque_atual = produto
        if estoque_atual >= quantidade:
            total_venda = preco_prod * quantidade
            novo_estoque = estoque_atual - quantidade
            
            # Atualiza estoque e registra a venda
            cursor.execute('UPDATE produtos SET estoque = ? WHERE id = ?', (novo_estoque, produto_id))
            cursor.execute('INSERT INTO vendas (produto_id, quantidade, total) VALUES (?, ?, ?)', 
                           (produto_id, quantidade, total_venda))
            
            conn.commit()
            print(f"\n💰 VENDA CONCLUÍDA!")
            print(f"Item: {nome_prod} | Total: R$ {total_venda:.2f}")
        else:
            print(f"\n❌ Estoque insuficiente! (Disponível: {estoque_atual})")
    else:
        print("\n❌ ID do produto não encontrado.")
    
    conn.close()

# --- INTERFACE DO USUÁRIO (MENU) ---

def menu():
    inicializar_db()
    
    while True:
        print("\n--- SISTEMA DE VENDAS (SISVENDA) ---")
        print("1. Novo Produto")
        print("2. Ver Estoque")
        print("3. Registrar Venda")
        print("4. Sair")
        
        opcao = input("\nSelecione uma opção: ")
        
        if opcao == '1':
            try:
                nome = input("Nome do produto: ")
                preco = float(input("Preço unitário: "))
                estoque = int(input("Quantidade inicial em estoque: "))
                cadastrar_produto(nome, preco, estoque)
            except ValueError:
                print("\n❌ Erro: Insira valores numéricos válidos para preço e estoque.")
                
        elif opcao == '2':
            listar_produtos()
            
        elif opcao == '3':
            listar_produtos()
            try:
                id_p = int(input("Informe o ID do produto para venda: "))
                qtd = int(input("Quantidade: "))
                if qtd > 0:
                    realizar_venda(id_p, qtd)
                else:
                    print("\n❌ A quantidade deve ser maior que zero.")
            except ValueError:
                print("\n❌ Erro: Digite apenas números inteiros para ID e Quantidade.")
                
        elif opcao == '4':
            print("Encerrando sistema... Até logo!")
            break
        else:
            print("\n⚠️ Opção inválida, tente novamente.")

if __name__ == "__main__":
    menu()