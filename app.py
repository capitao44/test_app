import streamlit as st
import pandas as pd
import json
import os
import hashlib # Para hashing de senhas
from datetime import datetime

# --- Configurações de Arquivos e Pastas ---
USERS_FILE = 'users.json'
USERS_DATA_DIR = 'users_data' # Pasta para armazenar dados de cada usuário

# Cria a pasta users_data se ela não existir
if not os.path.exists(USERS_DATA_DIR):
    os.makedirs(USERS_DATA_DIR)

# --- Funções de Autenticação e Dados ---

def hash_password(password):
    """Gera o hash SHA256 de uma senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def carregar_usuarios():
    """
    Carrega os usuários, suas senhas (texto puro) e hashes.
    Garante que o formato seja um dicionário aninhado para cada usuário.
    """
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Verifica se o formato é o esperado (dicionário de dicionários)
                # Se encontrar um formato antigo (string direta), ele será tratado
                # implicitamente ao tentar acessar password_hash.
                # Para uma migração mais robusta, poderíamos iterar e converter.
                # Mas ao deletar users.json e recriar, já resolve.
                return data
            except json.JSONDecodeError:
                # Se o arquivo estiver corrompido, retorna um dicionário vazio
                return {}
    return {}

def salvar_usuarios(users):
    """Salva os usuários, suas senhas (texto puro) e hashes."""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def carregar_dividas_usuario(username):
    """Carrega as dívidas de um usuário específico."""
    user_data_file = os.path.join(USERS_DATA_DIR, f"{username}.json")
    if os.path.exists(user_data_file):
        with open(user_data_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    # Garante que todos os campos padrão existam e transacoes seja lista
                    for item in data:
                        item.setdefault("nome", "Dívida Sem Nome")
                        item.setdefault("valor_original", 0.0)
                        item.setdefault("valor_atual", item["valor_original"])
                        item.setdefault("paga", False)
                        item.setdefault("data_criacao", datetime.now().strftime("%Y-%m-%d"))
                        item.setdefault("ult_atualizacao", datetime.now().strftime("%Y-%m-%d"))
                        item.setdefault("transacoes", []) 
                    return data
            except json.JSONDecodeError:
                st.error(f"Erro ao ler os dados de dívidas de '{username}'. JSON inválido.")
    return []

def salvar_dividas_usuario(username, dividas):
    """Salva as dívidas de um usuário específico."""
    user_data_file = os.path.join(USERS_DATA_DIR, f"{username}.json")
    with open(user_data_file, 'w', encoding='utf-8') as f:
        json.dump(dividas, f, indent=4, ensure_ascii=False)

def deletar_dados_usuario(username):
    """Deleta o arquivo de dados de um usuário específico."""
    user_data_file = os.path.join(USERS_DATA_DIR, f"{username}.json")
    if os.path.exists(user_data_file):
        os.remove(user_data_file)
        return True
    return False

# --- Configuração da Página Streamlit ---
st.set_page_config(layout="centered")
st.title("💸 Dashboard de Controle de Dívidas")

# --- Gerenciamento de Estado da Sessão ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'dividas_lista' not in st.session_state:
    st.session_state.dividas_lista = []

# --- Telas de Login/Cadastro ou Dashboard ---

if not st.session_state.logged_in:
    st.subheader("Acesse ou Cadastre-se")

    login_tab, signup_tab = st.tabs(["Login", "Cadastrar"])

    with login_tab:
        with st.form("form_login"):
            login_username = st.text_input("Nome de Usuário", key="login_username_input")
            login_password = st.text_input("Senha", type="password", key="login_password_input")
            login_submitted = st.form_submit_button("Entrar")

            if login_submitted:
                users = carregar_usuarios()
                # Verifica se o usuário existe e se o valor é um dicionário antes de tentar acessar a chave
                if login_username in users and isinstance(users[login_username], dict):
                    if users[login_username]["password_hash"] == hash_password(login_password):
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        # Carrega as dívidas do usuário logado
                        st.session_state.dividas_lista = carregar_dividas_usuario(login_username) 
                        st.success(f"Bem-vindo(a), {login_username}!")
                        st.rerun() # Recarrega a página para mostrar o dashboard
                    else:
                        st.error("Nome de usuário ou senha inválidos.")
                else:
                    st.error("Nome de usuário ou senha inválidos.") # Trata caso de usuário não existente ou formato inválido
                    
    with signup_tab:
        with st.form("form_signup"):
            signup_username = st.text_input("Novo Nome de Usuário", key="signup_username_input")
            signup_password = st.text_input("Nova Senha", type="password", key="signup_password_input")
            signup_confirm_password = st.text_input("Confirme a Senha", type="password", key="signup_confirm_password")
            signup_submitted = st.form_submit_button("Cadastrar")

            if signup_submitted:
                users = carregar_usuarios()
                if not signup_username:
                    st.error("O nome de usuário não pode ser vazio.")
                elif signup_username in users:
                    st.error("Nome de usuário já existe. Por favor, escolha outro.")
                elif not signup_password:
                    st.error("A senha não pode ser vazia.")
                elif signup_password != signup_confirm_password:
                    st.error("As senhas não coincidem.")
                else:
                    users[signup_username] = {
                        "password_plain": signup_password, # !!! AVISO DE SEGURANÇA: Senha em texto puro !!!
                        "password_hash": hash_password(signup_password)
                    }
                    salvar_usuarios(users)
                    # Cria o arquivo de dados vazio para o novo usuário
                    salvar_dividas_usuario(signup_username, []) 
                    st.success(f"Usuário '{signup_username}' cadastrado com sucesso! Agora você pode fazer login.")
                    st.rerun()

else: # Usuário está logado, mostra o Dashboard ou Painel Admin
    st.sidebar.write(f"Conectado como: **{st.session_state.username}**")
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.dividas_lista = []
        st.info("Você saiu da sua conta.")
        st.rerun()

    # --- Lógica para o Painel de Administração ---
    ADMIN_USERNAME = "admin" # Define o nome de usuário do administrador

    if st.session_state.username == ADMIN_USERNAME:
        st.header("👑 Painel de Administração")
        st.warning("⚠️ **AVISO DE SEGURANÇA:** As senhas estão sendo armazenadas em texto puro para esta demonstração. Não faça isso em produção real!")
        st.write(f"Bem-vindo, Administrador **{ADMIN_USERNAME}**! Aqui você pode gerenciar usuários e seus dados.")

        users_all = carregar_usuarios()
        
        st.markdown("---")
        st.subheader("Gerenciamento de Usuários")

        # Visualização de Todos os Usuários (incluindo senhas em texto puro e hashes)
        if users_all:
            users_data_for_display = []
            for u_name, u_info in users_all.items():
                users_data_for_display.append({
                    "Nome de Usuário": u_name,
                    "Senha (Texto Puro)": u_info.get("password_plain", "N/A"), # AVISO: EXTREMAMENTE INSEGURO!
                    "Hash da Senha": u_info.get("password_hash", "N/A")
                })
            df_users_creds = pd.DataFrame(users_data_for_display)
            st.table(df_users_creds)
        else:
            st.info("Nenhum usuário cadastrado ainda.")

        # --- Adicionar Novo Usuário (pelo Admin) ---
        st.markdown("#### Adicionar Novo Usuário")
        with st.form("form_add_user_admin", clear_on_submit=True):
            add_username = st.text_input("Nome de Usuário (Novo)", key="admin_add_username")
            add_password = st.text_input("Senha (Nova)", type="password", key="admin_add_password")
            add_confirm_password = st.text_input("Confirme a Senha (Nova)", type="password", key="admin_add_confirm_password")
            add_user_submitted = st.form_submit_button("Adicionar Usuário")

            if add_user_submitted:
                if not add_username:
                    st.error("O nome de usuário não pode ser vazio.")
                elif add_username in users_all:
                    st.error("Nome de usuário já existe. Por favor, escolha outro.")
                elif not add_password:
                    st.error("A senha não pode ser vazia.")
                elif add_password != add_confirm_password:
                    st.error("As senhas não coincidem.")
                else:
                    users_all[add_username] = {
                        "password_plain": add_password, # !!! AVISO DE SEGURANÇA: Senha em texto puro !!!
                        "password_hash": hash_password(add_password)
                    }
                    salvar_usuarios(users_all)
                    salvar_dividas_usuario(add_username, []) # Cria arquivo de dados para o novo usuário
                    st.success(f"Usuário '{add_username}' adicionado com sucesso!")
                    st.rerun()

        # --- Excluir Usuário (pelo Admin) ---
        st.markdown("#### Excluir Usuário")
        users_to_delete = [u for u in users_all.keys() if u != ADMIN_USERNAME] # Não permite deletar o próprio admin
        if users_to_delete:
            delete_username = st.selectbox("Selecione o usuário para excluir:", [""] + users_to_delete, key="admin_delete_user_select")
            if delete_username:
                if st.button(f"Excluir Usuário '{delete_username}'", key=f"btn_delete_user_{delete_username}", type="secondary"):
                    st.warning(f"❗ Clique novamente para CONFIRMAR a exclusão de '{delete_username}' e SEUS DADOS. Esta ação é irreversível.")
                    if st.button(f"CONFIRMAR EXCLUSÃO DE '{delete_username}'", key=f"confirm_delete_user_{delete_username}", type="primary"):
                        if delete_username in users_all:
                            del users_all[delete_username]
                            salvar_usuarios(users_all)
                            deletar_dados_usuario(delete_username) # Deleta o arquivo de dados do usuário
                            st.success(f"Usuário '{delete_username}' e seus dados foram excluídos com sucesso.")
                            st.rerun()
                        else:
                            st.error("Usuário não encontrado.")
        else:
            st.info("Nenhum usuário comum para excluir.")


        st.markdown("---")
        st.subheader("Detalhes das Dívidas por Usuário")

        # Seleciona um usuário para ver as dívidas detalhadamente
        user_names_for_select_data = [u for u in users_all.keys() if u != ADMIN_USERNAME] # Não mostra o próprio admin
        if user_names_for_select_data:
            selected_user_for_admin_detail = st.selectbox(
                "Selecione um usuário para ver/gerenciar suas dívidas:",
                [""] + user_names_for_select_data,
                key="admin_select_user_detail"
            )

            if selected_user_for_admin_detail:
                st.markdown(f"### Dívidas de {selected_user_for_admin_detail}")
                user_dividas_details = carregar_dividas_usuario(selected_user_for_admin_detail)

                if user_dividas_details:
                    df_user_dividas_details = pd.DataFrame(user_dividas_details)
                    # Formata as colunas para exibição amigável
                    df_user_dividas_details['Valor Original'] = df_user_dividas_details['valor_original'].apply(lambda x: f"R$ {x:.2f}")
                    df_user_dividas_details['Valor Restante'] = df_user_dividas_details['valor_atual'].apply(lambda x: f"R$ {x:.2f}")
                    df_user_dividas_details['Status'] = df_user_dividas_details['paga'].apply(lambda x: "✅ Paga" if x else "⏳ Pendente")
                    
                    # Exibe a tabela de dívidas do usuário selecionado
                    st.table(df_user_dividas_details[['nome', 'Valor Original', 'Valor Restante', 'Status', 'data_criacao', 'ult_atualizacao']].rename(columns={
                        'nome': 'Dívida',
                        'data_criacao': 'Criada em',
                        'ult_atualizacao': 'Última Atualização'
                    }))
                    
                    st.markdown("---")
                    st.subheader(f"Histórico de Transações Detalhado de {selected_user_for_admin_detail}")
                    
                    # Para ver o histórico de transações de uma dívida específica desse usuário
                    dividas_desse_usuario_nomes = [d['nome'] for d in user_dividas_details]
                    if dividas_desse_usuario_nomes:
                        divida_admin_view_hist = st.selectbox(
                            f"Selecione uma dívida de **{selected_user_for_admin_detail}** para ver o histórico de transações:",
                            [""] + dividas_desse_usuario_nomes,
                            key=f"admin_view_transactions_for_{selected_user_for_admin_detail}"
                        )
                        
                        if divida_admin_view_hist:
                            divida_obj_admin_hist = next((d for d in user_dividas_details if d['nome'] == divida_admin_view_hist), None)
                            if divida_obj_admin_hist and divida_obj_admin_hist['transacoes']:
                                df_admin_transacoes = pd.DataFrame(divida_obj_admin_hist['transacoes'])
                                df_admin_transacoes['Valor'] = df_admin_transacoes['valor'].apply(lambda x: f"R$ {x:.2f}")
                                st.table(df_admin_transacoes[['data', 'tipo', 'Valor', 'descricao']].rename(columns={
                                    'data': 'Data/Hora',
                                    'tipo': 'Tipo de Transação',
                                    'descricao': 'Descrição'
                                }))
                            else:
                                st.info(f"Nenhuma transação registrada para a dívida '{divida_admin_view_hist}' de {selected_user_for_admin_detail}.")
                    else:
                        st.info(f"Nenhuma dívida cadastrada para {selected_user_for_admin_detail} para exibir o histórico.")

                else:
                    st.info(f"O usuário **{selected_user_for_admin_detail}** não tem dívidas cadastradas.")
        else:
            st.info("Nenhum usuário comum cadastrado para exibir detalhes de dívidas.")

    else: # Usuário comum, exibe o dashboard normal
        st.markdown("---")
        st.header("➕ Adicionar Nova Dívida")
        with st.form("form_nova_divida", clear_on_submit=True):
            nome_nova_divida = st.text_input("Nome da Dívida", placeholder="Ex: Aluguel, Cartão de Crédito", key="add_nome_divida_user")
            valor_inicial_nova_divida = st.number_input("Valor Inicial (R$)", min_value=0.0, step=0.01, value=0.0, key="add_valor_divida_user")
            
            submitted = st.form_submit_button("Adicionar Dívida")
            if submitted:
                if nome_nova_divida:
                    if any(d['nome'].lower() == nome_nova_divida.lower() for d in st.session_state.dividas_lista):
                        st.warning(f"Já existe uma dívida com o nome '{nome_nova_divida}'. Por favor, escolha outro nome.")
                    else:
                        nova_divida = {
                            "nome": nome_nova_divida,
                            "valor_original": valor_inicial_nova_divida,
                            "valor_atual": valor_inicial_nova_divida,
                            "paga": False,
                            "data_criacao": datetime.now().strftime("%Y-%m-%d"),
                            "ult_atualizacao": datetime.now().strftime("%Y-%m-%d"),
                            "transacoes": []
                        }
                        st.session_state.dividas_lista.append(nova_divida)
                        salvar_dividas_usuario(st.session_state.username, st.session_state.dividas_lista)
                        st.success(f"Dívida '{nome_nova_divida}' adicionada com sucesso!")
                        st.rerun()
                else:
                    st.error("O nome da dívida não pode ser vazio.")

        st.markdown("---")
        st.header("📋 Suas Dívidas")

        if not st.session_state.dividas_lista:
            st.info("Nenhuma dívida cadastrada. Use o formulário acima para adicionar uma.")
        else:
            df_display = pd.DataFrame(st.session_state.dividas_lista)
            df_display = df_display.drop(columns=['transacoes'], errors='ignore') 

            df_display['Valor Original'] = df_display['valor_original'].apply(lambda x: f"R$ {x:.2f}")
            df_display['Valor Restante'] = df_display['valor_atual'].apply(lambda x: f"R$ {x:.2f}")
            df_display['Status'] = df_display['paga'].apply(lambda x: "✅ Paga" if x else "⏳ Pendente")
            
            st.table(df_display[['nome', 'Valor Original', 'Valor Restante', 'Status', 'ult_atualizacao']].rename(columns={
                'nome': 'Dívida',
                'ult_atualizacao': 'Última Atualização'
            }))

            total_pendente = sum(d['valor_atual'] for d in st.session_state.dividas_lista if not d['paga'])
            total_pago = sum(d['valor_original'] - d['valor_atual'] for d in st.session_state.dividas_lista if d['paga'] or d['valor_original'] > d['valor_atual'])
            total_original = sum(d['valor_original'] for d in st.session_state.dividas_lista)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Dívidas Originais", f"R$ {total_original:.2f}")
            with col2:
                st.metric("Total Pendente", f"R$ {total_pendente:.2f}", delta=f"R$ {-total_pendente:.2f}")
            with col3:
                st.metric("Total Pago/Amortizado", f"R$ {total_pago:.2f}")

        st.markdown("---")
        st.header("🔧 Gerenciar Dívida Individual")

        if st.session_state.dividas_lista:
            nomes_dividas = [d['nome'] for d in st.session_state.dividas_lista]
            divida_selecionada_nome = st.selectbox("Selecione a Dívida para Gerenciar", nomes_dividas, key="select_divida_gerenciar_user")

            divida_index = next((i for i, d in enumerate(st.session_state.dividas_lista) if d['nome'] == divida_selecionada_nome), -1)
            
            if divida_index != -1:
                divida_obj = st.session_state.dividas_lista[divida_index]

                st.subheader(f"Dívida: {divida_obj['nome']}")
                st.write(f"**A dívida com {divida_obj['nome']} está em R$ {divida_obj['valor_atual']:.2f}** (Original: R$ {divida_obj['valor_original']:.2f})")
                
                status_atual = "Paga" if divida_obj['paga'] else "Pendente"
                st.info(f"Status Atual: **{status_atual}**")

                st.markdown("##### Ações sobre o Saldo:")
                col_ajuste_valor, col_pagamento = st.columns(2)

                with col_ajuste_valor:
                    st.markdown("###### Ajustar Saldo (Aumentar/Diminuir):")
                    min_limite_negativo = -1.797e+308 
                    valor_ajuste = st.number_input("Valor para Aumentar ou Diminuir (R$)",
                                                 min_value=min_limite_negativo,
                                                 step=0.01,
                                                 value=0.0,
                                                 key=f"ajuste_{divida_obj['nome']}_user")
                    descricao_ajuste = st.text_input("Descrição do Ajuste (opcional)", key=f"desc_ajuste_{divida_obj['nome']}_user")

                    if st.button(f"Aplicar Ajuste a '{divida_obj['nome']}'", key=f"btn_ajustar_{divida_obj['nome']}_user"):
                        st.session_state.dividas_lista[divida_index]['valor_atual'] += valor_ajuste
                        if not divida_obj['paga'] and valor_ajuste > 0:
                            st.session_state.divida_lista[divida_index]['valor_original'] += valor_ajuste
                        
                        st.session_state.dividas_lista[divida_index]['paga'] = False
                        st.session_state.dividas_lista[divida_index]['ult_atualizacao'] = datetime.now().strftime("%Y-%m-%d")
                        
                        tipo_ajuste = "Aumento" if valor_ajuste >= 0 else "Diminuição"
                        st.session_state.dividas_lista[divida_index]['transacoes'].append({
                            "tipo": tipo_ajuste,
                            "valor": abs(valor_ajuste),
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "descricao": descricao_ajuste
                        })
                        
                        salvar_dividas_usuario(st.session_state.username, st.session_state.dividas_lista)
                        st.success(f"Dívida '{divida_obj['nome']}' ajustada. Novo valor: R$ {st.session_state.dividas_lista[divida_index]['valor_atual']:.2f}.")
                        st.rerun()

                with col_pagamento:
                    st.markdown("###### Registrar Pagamento:")
                    valor_pagamento = st.number_input("Valor do Pagamento (R$)", min_value=0.0, step=0.01, value=0.0, key=f"pagamento_{divida_obj['nome']}_user")
                    descricao_pagamento = st.text_input("Descrição do Pagamento (opcional)", key=f"desc_pagamento_{divida_obj['nome']}_user")

                    if st.button(f"Registrar Pagamento a '{divida_obj['nome']}'", key=f"btn_pagar_{divida_obj['nome']}_user"):
                        if valor_pagamento > 0:
                            st.session_state.dividas_lista[divida_index]['valor_atual'] -= valor_pagamento
                            if st.session_state.dividas_lista[divida_index]['valor_atual'] <= 0:
                                st.session_state.dividas_lista[divida_index]['valor_atual'] = 0.0
                                st.session_state.dividas_lista[divida_index]['paga'] = True
                                st.success(f"Dívida '{divida_obj['nome']}' liquidada!")
                            else:
                                st.success(f"Pagamento de R$ {valor_pagamento:.2f} aplicado à dívida '{divida_obj['nome']}'.")
                            
                            st.session_state.dividas_lista[divida_index]['ult_atualizacao'] = datetime.now().strftime("%Y-%m-%d")
                            
                            st.session_state.dividas_lista[divida_index]['transacoes'].append({
                                "tipo": "Pagamento",
                                "valor": valor_pagamento,
                                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "descricao": descricao_pagamento
                            })

                            salvar_dividas_usuario(st.session_state.username, st.session_state.dividas_lista)
                            st.rerun()
                        else:
                            st.warning("Por favor, insira um valor de pagamento maior que zero.")

                st.markdown("---")
                st.markdown("##### Outras Ações:")
                col_status, col_excluir = st.columns(2)

                with col_status:
                    if divida_obj['paga']:
                        if st.button(f"Marcar como Pendente", key=f"btn_pendente_{divida_obj['nome']}_user"):
                            st.session_state.dividas_lista[divida_index]['paga'] = False
                            st.session_state.dividas_lista[divida_index]['ult_atualizacao'] = datetime.now().strftime("%Y-%m-%d")
                            salvar_dividas_usuario(st.session_state.username, st.session_state.dividas_lista)
                            st.success(f"Dívida '{divida_obj['nome']}' marcada como pendente.")
                            st.rerun()
                    else:
                        if st.button(f"Marcar como Paga", key=f"btn_paga_{divida_obj['nome']}_user"):
                            st.session_state.dividas_lista[divida_index]['paga'] = True
                            if st.session_state.dividas_lista[divida_index]['valor_atual'] > 0:
                                st.session_state.dividas_lista[divida_index]['valor_atual'] = 0.0
                            st.session_state.dividas_lista[divida_index]['ult_atualizacao'] = datetime.now().strftime("%Y-%m-%d")
                            salvar_dividas_usuario(st.session_state.username, st.session_state.dividas_lista)
                            st.success(f"Dívida '{divida_obj['nome']}' marcada como paga.")
                            st.rerun()

                with col_excluir:
                    if st.button(f"Excluir Dívida '{divida_obj['nome']}'", key=f"btn_excluir_btn_{divida_obj['nome']}_user", type="secondary"):
                        st.warning(f"❗ Clique novamente para CONFIRMAR a exclusão de '{divida_obj['nome']}'. Esta ação é irreversível.")
                        if st.button(f"CONFIRMAR EXCLUSÃO", key=f"confirm_delete_{divida_obj['nome']}_user", type="primary"):
                            del st.session_state.dividas_lista[divida_index]
                            salvar_dividas_usuario(st.session_state.username, st.session_state.dividas_lista)
                            st.success(f"Dívida '{divida_obj['nome']}' excluída.")
                            st.rerun()

                st.markdown("---")
                st.header("📜 Histórico de Transações")
                if divida_obj['transacoes']:
                    df_transacoes = pd.DataFrame(divida_obj['transacoes'])
                    df_transacoes['Valor'] = df_transacoes['valor'].apply(lambda x: f"R$ {x:.2f}")
                    st.table(df_transacoes[['data', 'tipo', 'Valor', 'descricao']].rename(columns={
                        'data': 'Data/Hora',
                        'tipo': 'Tipo de Transação',
                        'descricao': 'Descrição'
                    }))
                else:
                    st.info("Nenhuma transação registrada para esta dívida ainda.")

            else:
                st.warning("Dívida selecionada não encontrada ou removida. Por favor, recarregue a página.")
        else:
            st.info("Nenhuma dívida para gerenciar. Adicione uma nova dívida acima.")