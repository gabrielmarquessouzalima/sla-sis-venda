import sqlite3

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
# Mude de 'sistema_vendas.db' para 'sistema_vendas_v2.db'
DB_NAME = 'sistema_vendas_v2.db'

def inicializar_db():
    """Cria o banco de dados e as tabelas necessárias se não existirem."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Tabela de Usuários (com campo CARGO)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                cargo TEXT NOT NULL
            )
        ''')
        
        # Tabela de Produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco REAL NOT NULL,
                estoque INTEGER NOT NULL
            )
        ''')
        
        # Tabela de Vendas (Saídas)
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

        # Tabela de Compras (Entradas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER,
                quantidade INTEGER,
                custo_total REAL,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
        ''')
        conn.commit()

# --- FUNÇÕES DE AUTENTICAÇÃO ---

def cadastrar_usuario():
    print("\n--- CADASTRO DE NOVO USUÁRIO ---")
    user = input("Nome de usuário: ")
    senha = input("Senha: ")
    print("Defina o cargo: (1) Administrador | (2) Vendedor")
    tipo = input("Opção: ")
    cargo = 'admin' if tipo == '1' else 'vendedor'
    
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO usuarios (usuario, senha, cargo) VALUES (?, ?, ?)', (user, senha, cargo))
            conn.commit()
            print(f"\n✅ Usuário '{user}' cadastrado como {cargo}!")
    except sqlite3.IntegrityError:
        print("\n❌ Erro: Este usuário já existe no sistema.")

def fazer_login():
    print("\n--- LOGIN ---")
    user = input("Usuário: ")
    senha = input("Senha: ")
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT cargo FROM usuarios WHERE usuario = ? AND senha = ?', (user, senha))
        resultado = cursor.fetchone()
        if resultado:
            return resultado[0]  # Retorna 'admin' ou 'vendedor'
        return None

# --- FUNÇÕES DE PRODUTOS ---

def listar_produtos():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produtos')
        produtos = cursor.fetchall()
        
        print("\n" + "="*55)
        print(f"{'ID':<4} | {'Nome':<20} | {'Preço (Venda)':<12} | {'Estoque'}")
        print("-" * 55)
        for p in produtos:
            print(f"{p[0]:<4} | {p[1]:<20} | R$ {p[2]:<9.2f} | {p[3]}")
        print("="*55)

def realizar_venda(produto_id, quantidade):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT nome, preco, estoque FROM produtos WHERE id = ?', (produto_id,))
        produto = cursor.fetchone()
        
        if produto and produto[2] >= quantidade:
            total = produto[1] * quantidade
            cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE id = ?', (quantidade, produto_id))
            cursor.execute('INSERT INTO vendas (produto_id, quantidade, total) VALUES (?, ?, ?)', (produto_id, quantidade, total))
            conn.commit()
            print(f"\n💰 Venda concluída! Item: {produto[0]} | Total: R$ {total:.2f}")
        else:
            print("\n❌ Erro: Produto não encontrado ou estoque insuficiente.")

def registrar_compra(produto_id, quantidade, custo_total):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT nome FROM produtos WHERE id = ?', (produto_id,))
        produto = cursor.fetchone()
        
        if produto:
            cursor.execute('UPDATE produtos SET estoque = estoque + ? WHERE id = ?', (quantidade, produto_id))
            cursor.execute('INSERT INTO compras (produto_id, quantidade, custo_total) VALUES (?, ?, ?)', (produto_id, quantidade, custo_total))
            conn.commit()
            print(f"\n📦 Estoque de '{produto[0]}' abastecido com sucesso!")
        else:
            print("\n❌ Erro: Produto não cadastrado.")

# --- MENUS ---

def menu_vendedor():
    """Acesso limitado: Vendedor só vê estoque e vende."""
    while True:
        print("\n--- 🛒 PAINEL DO VENDEDOR ---")
        print("1. Consultar Estoque")
        print("2. Registrar Venda")
        print("3. Fazer Logout")
        op = input("\nEscolha uma opção: ")
        
        if op == '1':
            listar_produtos()
        elif op == '2':
            listar_produtos()
            try:
                id_p = int(input("ID do Produto: "))
                q = int(input("Quantidade: "))
                realizar_venda(id_p, q)
            except ValueError:
                print("⚠️ Erro: Digite apenas números.")
        elif op == '3':
            break

def menu_admin():
    """Acesso total: Gerente faz tudo."""
    while True:
        print("\n--- 🛡️ PAINEL ADMINISTRATIVO ---")
        print("1. Cadastrar Novo Produto")
        print("2. Ver Estoque")
        print("3. Registrar Venda (Saída)")
        print("4. Registrar Compra (Entrada de Estoque)")
        print("5. Fazer Logout")
        op = input("\nEscolha uma opção: ")
        
        try:
            if op == '1':
                n = input("Nome do Produto: ")
                p = float(input("Preço de Venda: "))
                e = int(input("Estoque Inicial: "))
                with sqlite3.connect(DB_NAME) as conn:
                    conn.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?,?,?)', (n, p, e))
                print(f"✅ Produto '{n}' cadastrado!")
            elif op == '2':
                listar_produtos()
            elif op == '3':
                listar_produtos()
                id_p = int(input("ID do Produto: "))
                q = int(input("Qtd: "))
                realizar_venda(id_p, q)
            elif op == '4':
                listar_produtos()
                id_p = int(input("ID do Produto para Reposição: "))
                q = int(input("Qtd comprada: "))
                c = float(input("Custo Total da Compra R$: "))
                registrar_compra(id_p, q, c)
            elif op == '5':
                break
            else:
                print("Opção inválida.")
        except ValueError:
            print("⚠️ Erro: Entrada inválida. Use apenas números para preços e quantidades.")

# --- FLUXO PRINCIPAL ---

def main():
    inicializar_db()
    while True:
        print("\n" + "="*30)
        print("   SISTEMA COMERCIAL 2.0")
        print("="*30)
        print("1. Fazer Login")
        print("2. Criar Nova Conta")
        print("3. Sair do Sistema")
        
        escolha = input("\nEscolha: ")
        
        if escolha == '1':
            cargo = fazer_login()
            if cargo == 'admin':
                print("\n✨ Acesso de Administrador confirmado.")
                menu_admin()
            elif cargo == 'vendedor':
                print("\n✨ Acesso de Vendedor confirmado.")
                menu_vendedor()
            else:
                print("\n❌ Usuário ou senha incorretos.")
        elif escolha == '2':
            cadastrar_usuario()
        elif escolha == '3':
            print("Encerrando programa... Até logo!")
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()