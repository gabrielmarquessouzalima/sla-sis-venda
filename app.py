import sqlite3
import os
import hashlib
import shutil
import csv
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

# --- CONFIGURAÇÃO ---
DB_NAME = 'comercial_v31.db'#NÃO MUDAR ESSA LINHA!!!
BACKUP_DIR = 'backups'

class SistemaComercial:
    def __init__(self):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        self.inicializar_db_completo()
        self.criar_usuario_padrao()
    
    def hash_senha(self, senha: str) -> str:
        salt = "sistema_comercial_v4_2024"
        return hashlib.sha256((senha + salt).encode()).hexdigest()
    
    def inicializar_db_completo(self):
        """Cria/atualiza TODAS as tabelas corretamente"""
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            # 1. USUÁRIOS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL,
                    cargo TEXT NOT NULL CHECK (cargo IN ('admin', 'vendedor')),
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. PRODUTOS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    preco REAL NOT NULL CHECK (preco > 0),
                    estoque INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0),
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 3. VENDAS (CORRIGIDO - com coluna usuario)
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
            
            # 4. COMPRAS
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
            print("✅ Banco de dados inicializado!")
    
    def criar_usuario_padrao(self):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM usuarios WHERE usuario = 'admin'")
            if not cursor.fetchone():
                senha_hash = self.hash_senha('admin123')
                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, cargo) VALUES (?, ?, ?)",
                    ('admin', senha_hash, 'admin')
                )
                conn.commit()
    
    # --- AUTENTICAÇÃO ---
    def fazer_login(self) -> Optional[Tuple[str, str]]:
        print("\n" + "="*35)
        print("           🔐 LOGIN")
        print("="*35)
        
        usuario = input("👤 Usuário: ").strip()
        senha = input("🔒 Senha: ").strip()
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT usuario, cargo FROM usuarios WHERE usuario = ? AND senha = ?',
                (usuario, self.hash_senha(senha))
            )
            resultado = cursor.fetchone()
            return resultado
    
    def cadastrar_usuario(self):
        print("\n" + "="*40)
        print("         ➕ NOVO USUÁRIO")
        print("="*40)
        
        usuario = input("👤 Nome de usuário: ").strip()
        senha = input("🔒 Senha: ").strip()
        print("📋 Cargo: 1=Admin | 2=Vendedor")
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
            print(f"✅ '{usuario}' criado como {cargo_final.upper()}!")
        except sqlite3.IntegrityError:
            print("❌ Usuário já existe!")
    
    # --- PRODUTOS ---
    def listar_produtos(self):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM produtos ORDER BY nome')
            produtos = cursor.fetchall()
            
            if not produtos:
                print("\n📦 Nenhum produto!")
                return
            
            print("\n" + "="*60)
            print(f"{'ID':<4} | {'PRODUTO':<20} | {'PREÇO R$':<10} | {'ESTOQUE'}")
            print("-"*60)
            for p in produtos:
                status = "🚨" if p[3] < 10 else "✅"
                print(f"{p[0]:<4} | {p[1]:<20} | {p[2]:<9.2f} | {p[3]:<8} {status}")
            print("="*60)
    
    def estoque_critico(self):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, estoque FROM produtos WHERE estoque < 10 ORDER BY estoque')
            criticos = cursor.fetchall()
            if criticos:
                print("\n⚠️  ESTOQUE CRÍTICO:")
                for p in criticos:
                    print(f"🚨 {p[0]}: {p[1]} unidades")
    
    def cadastrar_produto(self):
        print("\n📦 NOVO PRODUTO")
        nome = input("Nome: ").strip()
        try:
            preco = float(input("Preço R$: "))
            estoque = int(input("Estoque inicial: "))
            
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)',
                    (nome, preco, estoque)
                )
                conn.commit()
            print(f"✅ '{nome}' cadastrado!")
        except ValueError:
            print("❌ Números inválidos!")
    
    # --- OPERAÇÕES ---
    def realizar_venda(self, produto_id: int, quantidade: int, usuario: str):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, preco, estoque FROM produtos WHERE id = ?', (produto_id,))
            produto = cursor.fetchone()
            
            if not produto:
                print("❌ Produto não encontrado!")
                return
            
            if produto[2] < quantidade:
                print(f"❌ Estoque insuficiente! {produto[2]} disponíveis")
                return
            
            total = produto[1] * quantidade
            cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE id = ?', (quantidade, produto_id))
            cursor.execute(
                'INSERT INTO vendas (produto_id, quantidade, total, usuario) VALUES (?, ?, ?, ?)',
                (produto_id, quantidade, total, usuario)
            )
            conn.commit()
            
            print(f"\n💰 VENDA OK!")
            print(f"   {produto[0]} x{quantidade} = R${total:.2f}")
    
    def registrar_compra(self, produto_id: int, quantidade: int, custo_total: float, usuario: str):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM produtos WHERE id = ?', (produto_id,))
            produto = cursor.fetchone()
            
            if not produto:
                print("❌ Produto não encontrado!")
                return
            
            custo_unit = custo_total / quantidade
            cursor.execute('UPDATE produtos SET estoque = estoque + ? WHERE id = ?', (quantidade, produto_id))
            cursor.execute(
                'INSERT INTO compras (produto_id, quantidade, custo_unitario, custo_total, usuario) VALUES (?, ?, ?, ?, ?)',
                (produto_id, quantidade, custo_unit, custo_total, usuario)
            )
            conn.commit()
            
            print(f"\n📦 COMPRA OK!")
            print(f"   {produto[0]} x{quantidade} = R${custo_total:.2f}")
    
    # --- RELATÓRIOS ---
    def relatorio_vendas(self):
        hoje = datetime.now().strftime('%Y-%m-%d')
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.nome, v.quantidade, v.total, v.data, v.usuario
                FROM vendas v JOIN produtos p ON v.produto_id = p.id 
                WHERE DATE(v.data) = ? ORDER BY v.data DESC
            ''', (hoje,))
            vendas = cursor.fetchall()
            
            if not vendas:
                print("\n📊 Nenhuma venda hoje!")
                return
            
            print("\n" + "="*70)
            print(f"{'PRODUTO':<20} | {'QTD':<5} | {'TOTAL':<10} | {'USUÁRIO':<10} | {'DATA'}")
            print("-"*70)
            total_dia = 0
            for v in vendas:
                print(f"{v[0]:<20} | {v[1]:<5} | R${v[2]:<9.2f} | {v[4]:<10} | {v[3][:16]}")
                total_dia += v[2]
            print("-"*70)
            print(f"{'TOTAL DO DIA:':<45} R$ {total_dia:>9.2f}")
            print("="*70)
    
    # --- MENUS ---
    def menu_vendedor(self, usuario: str):
        while True:
            print("\n" + "="*40)
            print(f"     🛒 VENDEDOR: {usuario}")
            print("="*40)
            print("1. 📋 Estoque")
            print("2. 💰 Venda")
            print("3. 📊 Vendas Hoje")
            print("4. 🚪 Sair")
            
            op = input("\n👉 ").strip()
            if op == '1':
                self.listar_produtos()
                self.estoque_critico()
            elif op == '2':
                self.listar_produtos()
                try:
                    pid = int(input("ID: "))
                    qtd = int(input("Qtd: "))
                    self.realizar_venda(pid, qtd, usuario)
                except:
                    print("❌ Erro!")
            elif op == '3':
                self.relatorio_vendas()
            elif op == '4':
                break
            input("\n⏸️ Enter...")
    
    def menu_admin(self, usuario: str):
        while True:
            print("\n" + "="*45)
            print(f"   🛡️ ADMIN: {usuario}")
            print("="*45)
            print("1. ➕ Produto")
            print("2. 📋 Estoque")
            print("3. 💰 Venda")
            print("4. 📦 Compra")
            print("5. 📊 Relatório")
            print("6. 👥 Usuário")
            print("7. 🚪 Sair")
            
            op = input("\n👉 ").strip()
            if op == '1':
                self.cadastrar_produto()
            elif op == '2':
                self.listar_produtos()
                self.estoque_critico()
            elif op == '3':
                self.listar_produtos()
                try:
                    pid = int(input("ID: "))
                    qtd = int(input("Qtd: "))
                    self.realizar_venda(pid, qtd, usuario)
                except:
                    print("❌ Erro!")
            elif op == '4':
                self.listar_produtos()
                try:
                    pid = int(input("ID: "))
                    qtd = int(input("Qtd: "))
                    custo = float(input("Custo total: "))
                    self.registrar_compra(pid, qtd, custo, usuario)
                except:
                    print("❌ Erro!")
            elif op == '5':
                self.relatorio_vendas()
            elif op == '6':
                self.cadastrar_usuario()
            elif op == '7':
                break
            input("\n⏸️ Enter...")
    
    def main(self):
        print("🚀 SISTEMA COMERCIAL v4.0 🚀")
        print("Admin padrão: admin / admin123")
        
        while True:
            print("\n" + "="*40)
            print("     🎯 MENU PRINCIPAL")
            print("="*40)
            print("1. 🔐 Login")
            print("2. ➕ Usuário")
            print("3. ❌ Sair")
            
            op = input("\n👉 ").strip()
            
            if op == '1':
                cred = self.fazer_login()
                if cred:
                    usuario, cargo = cred
                    print(f"\n✅ {cargo.upper()} logado!")
                    if cargo == 'admin':
                        self.menu_admin(usuario)
                    else:
                        self.menu_vendedor(usuario)
                else:
                    print("❌ Login inválido!")
                input("\n⏸️ Enter...")
            elif op == '2':
                self.cadastrar_usuario()
                input("\n⏸️ Enter...")
            elif op == '3':
                print("👋 Até logo!")
                break

if __name__ == "__main__":
    app = SistemaComercial()
    app.main()
