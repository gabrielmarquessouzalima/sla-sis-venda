import sqlite3
import os
from datetime import datetime
from typing import Optional, Tuple

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DB_NAME = 'comercial_v3.db'

class SistemaComercial:
    def __init__(self):
        self.inicializar_db()
    
    def inicializar_db(self):
        """Cria o banco de dados e as tabelas necessárias se não existirem."""
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            # Tabela de Usuários (melhorada com hash de senha)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL,
                    cargo TEXT NOT NULL CHECK (cargo IN ('admin', 'vendedor')),
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de Produtos (melhorada)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    preco REAL NOT NULL CHECK (preco > 0),
                    estoque INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0),
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de Vendas (melhorada)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                    total REAL NOT NULL CHECK (total > 0),
                    usuario TEXT NOT NULL,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                )
            ''')
            
            # Tabela de Compras (melhorada)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                    custo_unitario REAL NOT NULL CHECK (custo_unitario > 0),
                    custo_total REAL NOT NULL CHECK (custo_total > 0),
                    usuario TEXT NOT NULL,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                )
            ''')
            conn.commit()
    
    # --- HASH DE SENHA SIMPLES (para produção, use bcrypt) ---
    def hash_senha(self, senha: str) -> str:
        """Hash simples para senhas (para produção, use bcrypt)"""
        return senha  # Placeholder - substitua por hash real
    
    # --- AUTENTICAÇÃO MELHORADA ---
    def cadastrar_usuario(self):
        print("\n" + "="*40)
        print("         CADASTRO DE USUÁRIO")
        print("="*40)
        usuario = input("👤 Nome de usuário: ").strip()
        if not usuario:
            print("❌ Nome de usuário não pode estar vazio!")
            return
        
        senha = input("🔒 Senha: ").strip()
        if len(senha) < 4:
            print("❌ Senha deve ter pelo menos 4 caracteres!")
            return
        
        print("📋 Cargo: (1) Administrador | (2) Vendedor")
        cargo = input("Opção: ").strip()
        cargo_final = 'admin' if cargo == '1' else 'vendedor'
        
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO usuarios (usuario, senha, cargo) VALUES (?, ?, ?)',
                    (usuario, self.hash_senha(senha), cargo_final)
                )
                conn.commit()
                print(f"\n✅ Usuário '{usuario}' cadastrado como {cargo_final.upper()}!")
        except sqlite3.IntegrityError:
            print(f"\n❌ Usuário '{usuario}' já existe!")
    
    def fazer_login(self) -> Optional[str]:
        print("\n" + "="*30)
        print("              LOGIN")
        print("="*30)
        usuario = input("👤 Usuário: ").strip()
        senha = input("🔒 Senha: ").strip()
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT cargo FROM usuarios WHERE usuario = ? AND senha = ?',
                (usuario, self.hash_senha(senha))
            )
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
    
    # --- RELATÓRIOS AVANÇADOS ---
    def relatorio_vendas(self):
        """Relatório de vendas do dia"""
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            hoje = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT p.nome, v.quantidade, v.total, v.data 
                FROM vendas v 
                JOIN produtos p ON v.produto_id = p.id 
                WHERE DATE(v.data) = ?
                ORDER BY v.data DESC
            ''', (hoje,))
            vendas = cursor.fetchall()
            
            if not vendas:
                print("\n📊 Nenhuma venda hoje.")
                return
            
            print("\n" + "="*60)
            print(f"{'PRODUTO':<20} | {'QTD':<5} | {'TOTAL':<10} | {'DATA'}")
            print("-"*60)
            total_dia = 0
            for venda in vendas:
                print(f"{venda[0]:<20} | {venda[1]:<5} | R${venda[2]:<9.2f} | {venda[3][:16]}")
                total_dia += venda[2]
            print("-"*60)
            print(f"{'TOTAL DO DIA:':<36} R$ {total_dia:>9.2f}")
            print("="*60)
    
    def estoque_critico(self):
        """Produtos com estoque baixo (< 10)"""
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nome, preco, estoque FROM produtos 
                WHERE estoque < 10 AND estoque > 0
                ORDER BY estoque ASC
            ''')
            criticos = cursor.fetchall()
            
            if criticos:
                print("\n⚠️  ESTOQUE CRÍTICO:")
                print("-"*40)
                for p in criticos:
                    print(f"🚨 {p[0]}: {p[2]} unidades")
    
    # --- PRODUTOS MELHORADOS ---
    def listar_produtos(self, mostrar_critico=False):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM produtos ORDER BY nome')
            produtos = cursor.fetchall()
            
            if not produtos:
                print("\n📦 Nenhum produto cadastrado.")
                return
            
            print("\n" + "="*60)
            print(f"{'ID':<4} | {'PRODUTO':<20} | {'PREÇO R$':<10} | {'ESTOQUE':<8}")
            print("-"*60)
            for p in produtos:
                status = "🚨" if p[3] < 10 else "✅"
                print(f"{p[0]:<4} | {p[1]:<20} | {p[2]:<9.2f} | {p[3]:<8} {status}")
            print("="*60)
            
            if mostrar_critico:
                self.estoque_critico()
    
    def cadastrar_produto(self):
        print("\n📦 NOVO PRODUTO")
        nome = input("Nome: ").strip()
        try:
            preco = float(input("Preço de venda R$: "))
            estoque = int(input("Estoque inicial: "))
            
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)',
                    (nome, preco, estoque)
                )
                conn.commit()
                print(f"\n✅ '{nome}' cadastrado com sucesso!")
        except ValueError:
            print("❌ Erro: Use números válidos!")
    
    def realizar_venda(self, produto_id: int, quantidade: int, usuario: str):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, preco, estoque FROM produtos WHERE id = ?', (produto_id,))
            produto = cursor.fetchone()
            
            if not produto:
                print("\n❌ Produto não encontrado!")
                return
            
            if produto[2] < quantidade:
                print(f"\n❌ Estoque insuficiente! Disponível: {produto[2]}")
                return
            
            total = produto[1] * quantidade
            cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE id = ?', (quantidade, produto_id))
            cursor.execute(
                'INSERT INTO vendas (produto_id, quantidade, total, usuario) VALUES (?, ?, ?, ?)',
                (produto_id, quantidade, total, usuario)
            )
            conn.commit()
            print(f"\n💰 VENDA CONCLUÍDA!")
            print(f"   Produto: {produto[0]}")
            print(f"   Qtd: {quantidade} | Total: R$ {total:.2f}")
    
    def registrar_compra(self, produto_id: int, quantidade: int, custo_total: float, usuario: str):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM produtos WHERE id = ?', (produto_id,))
            produto = cursor.fetchone()
            
            if not produto:
                print("\n❌ Produto não encontrado!")
                return
            
            custo_unitario = custo_total / quantidade
            cursor.execute('UPDATE produtos SET estoque = estoque + ? WHERE id = ?', (quantidade, produto_id))
            cursor.execute(
                'INSERT INTO compras (produto_id, quantidade, custo_unitario, custo_total, usuario) VALUES (?, ?, ?, ?, ?)',
                (produto_id, quantidade, custo_unitario, custo_total, usuario)
            )
            conn.commit()
            print(f"\n📦 COMPRA REGISTRADA!")
            print(f"   Produto: {produto[0]}")
            print(f"   Qtd: {quantidade} | Custo: R$ {custo_total:.2f}")

    # --- MENUS MELHORADOS ---
    def menu_vendedor(self, usuario: str):
        while True:
            print("\n" + "="*35)
            print("       🛒 PAINEL VENDEDOR")
            print("       Usuário:", usuario)
            print("="*35)
            print("1. 📋 Ver Estoque")
            print("2. 💰 Registrar Venda")
            print("3. 📊 Vendas do Dia")
            print("4. 🚪 Logout")
            
            op = input("\n👉 Escolha: ").strip()
            
            if op == '1':
                self.listar_produtos(True)
            elif op == '2':
                self.listar_produtos()
                try:
                    id_p = int(input("ID do produto: "))
                    qtd = int(input("Quantidade: "))
                    self.realizar_venda(id_p, qtd, usuario)
                except ValueError:
                    print("❌ Digite apenas números!")
            elif op == '3':
                self.relatorio_vendas()
            elif op == '4':
                break
            input("\n⏸️  Enter para continuar...")
    
    def menu_admin(self, usuario: str):
        while True:
            print("\n" + "="*40)
            print("     🛡️ PAINEL ADMINISTRATIVO")
            print("     Usuário:", usuario)
            print("="*40)
            print("1. ➕ Cadastrar Produto")
            print("2. 📋 Ver Estoque")
            print("3. 💰 Registrar Venda")
            print("4. 📦 Registrar Compra")
            print("5. 📊 Relatório Vendas")
            print("6. 👥 Gerenciar Usuários")
            print("7. 🚪 Logout")
            
            op = input("\n👉 Escolha: ").strip()
            
            if op == '1':
                self.cadastrar_produto()
            elif op == '2':
                self.listar_produtos(True)
            elif op == '3':
                self.listar_produtos()
                try:
                    id_p = int(input("ID produto: "))
                    qtd = int(input("Quantidade: "))
                    self.realizar_venda(id_p, qtd, usuario)
                except ValueError:
                    print("❌ Digite números!")
            elif op == '4':
                self.listar_produtos()
                try:
                    id_p = int(input("ID produto: "))
                    qtd = int(input("Quantidade comprada: "))
                    custo = float(input("Custo total R$: "))
                    self.registrar_compra(id_p, qtd, custo, usuario)
                except ValueError:
                    print("❌ Digite números!")
            elif op == '5':
                self.relatorio_vendas()
            elif op == '6':
                self.cadastrar_usuario()
            elif op == '7':
                break
            input("\n⏸️  Enter para continuar...")

    def main(self):
        print("🚀 Iniciando Sistema Comercial v3.0...")
        while True:
            print("\n" + "="*40)
            print("     SISTEMA COMERCIAL PROFISSIONAL")
            print("="*40)
            print("1. 🔐 Login")
            print("2. ➕ Novo Usuário")
            print("3. ❌ Sair")
            
            escolha = input("\n👉 Opção: ").strip()
            
            if escolha == '1':
                cargo = self.fazer_login()
                if cargo == 'admin':
                    print("\n✨ Acesso ADMINISTRATIVO confirmado!")
                    self.menu_admin("ADMIN")
                elif cargo == 'vendedor':
                    print("\n✨ Acesso VENDEDOR confirmado!")
                    usuario = self.fazer_login()  # Pega o usuário logado
                    self.menu_vendedor(usuario)
                else:
                    print("\n❌ Credenciais inválidas!")
                input("\n⏸️  Enter para continuar...")
            elif escolha == '2':
                self.cadastrar_usuario()
                input("\n⏸️  Enter para continuar...")
            elif escolha == '3':
                print("\n👋 Até logo!")
                break

if __name__ == "__main__":
    app = SistemaComercial()
    app.main()
