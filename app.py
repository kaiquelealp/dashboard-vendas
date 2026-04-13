import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
from io import BytesIO
import json

# ============================================================================
# CONFIGURAÇÃO INICIAL - TEMA E PALETA V4 COMPANY
# ============================================================================
st.set_page_config(
    page_title="Sales Rejection Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta V4 Company
V4_RED = "#E31E24"  # Vermelho principal
V4_WHITE = "#FFFFFF"  # Branco
V4_DARK = "#1a1a1a"  # Escuro para texto
V4_LIGHT_GRAY = "#f5f5f5"  # Fundo claro

# CSS customizado com identidade V4
st.markdown(f"""
    <style>
        :root {{
            --primary-color: {V4_RED};
            --background-color: {V4_WHITE};
            --text-color: {V4_DARK};
        }}
        
        .main {{
            background-color: {V4_LIGHT_GRAY};
        }}
        
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, {V4_RED} 0%, #c41a1f 100%);
            color: {V4_WHITE};
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .insight-box {{
            background-color: {V4_RED};
            color: {V4_WHITE};
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            font-weight: 500;
            border-left: 5px solid #c41a1f;
        }}
        
        .header-title {{
            color: {V4_RED};
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .stButton > button {{
            background-color: {V4_RED};
            color: {V4_WHITE};
            border: none;
            border-radius: 5px;
            font-weight: 600;
            padding: 10px 20px;
        }}
        
        .stButton > button:hover {{
            background-color: #c41a1f;
        }}
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# ============================================================================

def init_database():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect('sales_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales_rejections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            rejection_date TEXT NOT NULL,
            objection_reason TEXT NOT NULL,
            lost_value REAL,
            observations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_database()

# ============================================================================
# FUNÇÕES DE BANCO DE DADOS
# ============================================================================

def add_rejection(client_name, rejection_date, objection_reason, lost_value, observations):
    """Adiciona um novo registro de rejeição ao banco"""
    conn = sqlite3.connect('sales_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO sales_rejections 
        (client_name, rejection_date, objection_reason, lost_value, observations)
        VALUES (?, ?, ?, ?, ?)
    ''', (client_name, rejection_date, objection_reason, lost_value, observations))
    conn.commit()
    conn.close()

def get_all_rejections():
    """Retorna todos os registros de rejeição"""
    conn = sqlite3.connect('sales_data.db')
    df = pd.read_sql_query('SELECT * FROM sales_rejections ORDER BY rejection_date DESC', conn)
    conn.close()
    return df

def delete_rejection(rejection_id):
    """Deleta um registro de rejeição"""
    conn = sqlite3.connect('sales_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM sales_rejections WHERE id = ?', (rejection_id,))
    conn.commit()
    conn.close()

def clear_all_data():
    """Limpa todos os dados do banco"""
    conn = sqlite3.connect('sales_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM sales_rejections')
    conn.commit()
    conn.close()

# ============================================================================
# FUNÇÕES DE ANÁLISE E INSIGHTS
# ============================================================================

def generate_insights(df):
    """Gera insights automáticos baseado nos dados"""
    if df.empty:
        return "Nenhum dado disponível para análise. Comece adicionando registros de rejeições."
    
    insights = []
    
    # Insight 1: Objeção mais comum
    objection_counts = df['objection_reason'].value_counts()
    top_objection = objection_counts.index[0]
    top_percentage = (objection_counts.iloc[0] / len(df)) * 100
    insights.append(f"🎯 **Objeção Crítica**: '{top_objection}' foi responsável por {top_percentage:.1f}% das perdas. Revise sua estratégia para este ponto.")
    
    # Insight 2: Valor total perdido
    if 'lost_value' in df.columns and df['lost_value'].notna().any():
        total_lost = df['lost_value'].sum()
        avg_lost = df['lost_value'].mean()
        insights.append(f"💰 **Impacto Financeiro**: R$ {total_lost:,.2f} perdidos no total (média: R$ {avg_lost:,.2f} por negócio).")
    
    # Insight 3: Tendência do mês
    df['rejection_date'] = pd.to_datetime(df['rejection_date'])
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_month_data = df[(df['rejection_date'].dt.month == current_month) & 
                            (df['rejection_date'].dt.year == current_year)]
    
    if len(current_month_data) > 0:
        insights.append(f"📅 **Mês Atual**: {len(current_month_data)} negócios perdidos este mês.")
    
    # Insight 4: Recomendação
    if top_objection == "Preço":
        insights.append("💡 **Recomendação**: Considere revisar sua abordagem de valor ou oferecer condições especiais para competir melhor.")
    elif top_objection == "Agenda":
        insights.append("💡 **Recomendação**: Melhore o timing de abordagem e qualifique melhor os leads antes do contato.")
    elif top_objection == "Decisor":
        insights.append("💡 **Recomendação**: Invista em técnicas de mapeamento de stakeholders e envolvimento do decisor desde o início.")
    elif top_objection == "Concorrente":
        insights.append("💡 **Recomendação**: Fortaleça seu posicionamento competitivo e diferenciais únicos.")
    elif top_objection == "Falta de Fit":
        insights.append("💡 **Recomendação**: Melhore sua qualificação de leads para focar em prospects com real aderência.")
    
    return "\n\n".join(insights)

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

# Header com logo e título
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"<h1 class='header-title'>📊 Sales Rejection Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: {V4_RED}; font-size: 1.1rem;'>Análise e Gestão de Negócios Perdidos</p>", unsafe_allow_html=True)

st.markdown("---")

# Abas principais
tab1, tab2, tab3, tab4 = st.tabs(["📝 Registrar Rejeição", "📊 Dashboard", "📋 Histórico", "⚙️ Configurações"])

# ============================================================================
# ABA 1: FORMULÁRIO DE ENTRADA
# ============================================================================
with tab1:
    st.subheader("Registrar Nova Rejeição de Venda")
    
    with st.form("rejection_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input(
                "Nome do Cliente/Empresa",
                placeholder="Digite o nome do cliente ou empresa",
                help="Identificação do cliente que rejeitou a proposta"
            )
            
            rejection_date = st.date_input(
                "Data da Perda",
                value=datetime.now(),
                help="Quando ocorreu a rejeição"
            )
            
            objection_reason = st.selectbox(
                "Motivo da Objeção",
                options=["Agenda", "Preço", "Decisor", "Concorrente", "Falta de Fit", "Outros"],
                help="Selecione a principal razão da rejeição"
            )
        
        with col2:
            lost_value = st.number_input(
                "Valor Perdido (R$)",
                min_value=0.0,
                step=100.0,
                help="Valor da proposta (opcional)"
            )
            
            observations = st.text_area(
                "Observações",
                placeholder="Adicione detalhes sobre a rejeição...",
                height=100,
                help="Contexto adicional sobre a rejeição"
            )
        
        # Botão de submissão
        submitted = st.form_submit_button(
            "✅ Registrar Rejeição",
            use_container_width=True
        )
        
        if submitted:
            if not client_name:
                st.error("❌ Por favor, preencha o nome do cliente/empresa.")
            else:
                add_rejection(
                    client_name=client_name,
                    rejection_date=str(rejection_date),
                    objection_reason=objection_reason,
                    lost_value=lost_value if lost_value > 0 else None,
                    observations=observations
                )
                st.success(f"✅ Rejeição de '{client_name}' registrada com sucesso!")
                st.balloons()

# ============================================================================
# ABA 2: DASHBOARD COM GRÁFICOS E INSIGHTS
# ============================================================================
with tab2:
    df = get_all_rejections()
    
    if df.empty:
        st.info("📭 Nenhum dado disponível. Comece registrando rejeições na aba 'Registrar Rejeição'.")
    else:
        # INSIGHTS AUTOMÁTICOS
        st.markdown(f"<div class='insight-box'>{generate_insights(df)}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # MÉTRICAS RÁPIDAS
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class='metric-card'>
                    <h3>Total de Perdas</h3>
                    <h2>{len(df)}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            top_objection = df['objection_reason'].value_counts().index[0]
            st.markdown(f"""
                <div class='metric-card'>
                    <h3>Objeção Crítica</h3>
                    <h2>{top_objection}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            current_month_data = df[
                (pd.to_datetime(df['rejection_date']).dt.month == datetime.now().month) &
                (pd.to_datetime(df['rejection_date']).dt.year == datetime.now().year)
            ]
            st.markdown(f"""
                <div class='metric-card'>
                    <h3>Perdas Este Mês</h3>
                    <h2>{len(current_month_data)}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            if 'lost_value' in df.columns and df['lost_value'].notna().any():
                total_value = df['lost_value'].sum()
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>Valor Perdido</h3>
                        <h2>R$ {total_value:,.0f}</h2>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>Valor Perdido</h3>
                        <h2>-</h2>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # GRÁFICOS
        col1, col2 = st.columns(2)
        
        # Gráfico de Pizza - Distribuição de Objeções
        with col1:
            st.subheader("📊 Distribuição de Objeções")
            objection_dist = df['objection_reason'].value_counts()
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=objection_dist.index,
                values=objection_dist.values,
                marker=dict(
                    colors=[V4_RED, '#c41a1f', '#ff6b6b', '#ff8888', '#ffaaaa', '#ffcccc'],
                    line=dict(color=V4_WHITE, width=2)
                ),
                textposition='inside',
                textinfo='label+percent'
            )])
            
            fig_pie.update_layout(
                height=400,
                showlegend=True,
                paper_bgcolor=V4_LIGHT_GRAY,
                plot_bgcolor=V4_LIGHT_GRAY,
                font=dict(size=12, color=V4_DARK)
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Gráfico de Barras - Negócios Perdidos por Mês
        with col2:
            st.subheader("📈 Negócios Perdidos por Mês")
            df['rejection_date'] = pd.to_datetime(df['rejection_date'])
            df['year_month'] = df['rejection_date'].dt.to_period('M')
            monthly_data = df.groupby('year_month').size().reset_index(name='count')
            monthly_data['year_month'] = monthly_data['year_month'].astype(str)
            
            fig_bar = go.Figure(data=[go.Bar(
                x=monthly_data['year_month'],
                y=monthly_data['count'],
                marker=dict(color=V4_RED),
                text=monthly_data['count'],
                textposition='outside'
            )])
            
            fig_bar.update_layout(
                height=400,
                xaxis_title="Mês",
                yaxis_title="Quantidade",
                paper_bgcolor=V4_LIGHT_GRAY,
                plot_bgcolor=V4_LIGHT_GRAY,
                font=dict(size=12, color=V4_DARK),
                showlegend=False
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)

# ============================================================================
# ABA 3: HISTÓRICO DE REGISTROS
# ============================================================================
with tab3:
    st.subheader("📋 Histórico de Rejeições")
    
    df = get_all_rejections()
    
    if df.empty:
        st.info("📭 Nenhum registro disponível.")
    else:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_objection = st.multiselect(
                "Filtrar por Objeção",
                options=df['objection_reason'].unique(),
                default=df['objection_reason'].unique()
            )
        
        with col2:
            filter_client = st.text_input("Buscar por Cliente")
        
        with col3:
            filter_date_range = st.date_input(
                "Intervalo de Datas",
                value=(df['rejection_date'].min(), df['rejection_date'].max()),
                key="date_range"
            )
        
        # Aplicar filtros
        df_filtered = df[df['objection_reason'].isin(filter_objection)]
        
        if filter_client:
            df_filtered = df_filtered[df_filtered['client_name'].str.contains(filter_client, case=False, na=False)]
        
        # Exibir tabela
        st.dataframe(
            df_filtered[['client_name', 'rejection_date', 'objection_reason', 'lost_value', 'observations']],
            use_container_width=True,
            hide_index=True
        )
        
        # Opção de deletar registros
        st.markdown("---")
        st.subheader("🗑️ Gerenciar Registros")
        
        if st.button("Deletar Último Registro"):
            if not df.empty:
                last_id = df.iloc[-1]['id']
                delete_rejection(last_id)
                st.success("✅ Registro deletado com sucesso!")
                st.rerun()

# ============================================================================
# ABA 4: CONFIGURAÇÕES E EXPORTAÇÃO/IMPORTAÇÃO
# ============================================================================
with tab4:
    st.subheader("⚙️ Configurações e Dados")
    
    col1, col2 = st.columns(2)
    
    # EXPORTAÇÃO
    with col1:
        st.markdown("### 📥 Exportar Dados")
        
        df = get_all_rejections()
        
        if not df.empty:
            # Exportar para Excel
            if st.button("📊 Exportar para Excel"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Rejeições', index=False)
                
                output.seek(0)
                st.download_button(
                    label="⬇️ Baixar Excel",
                    data=output.getvalue(),
                    file_name=f"sales_rejections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Exportar para CSV
            if st.button("📄 Exportar para CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Baixar CSV",
                    data=csv,
                    file_name=f"sales_rejections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("Nenhum dado para exportar.")
    
    # IMPORTAÇÃO
    with col2:
        st.markdown("### 📤 Importar Dados")
        
        uploaded_file = st.file_uploader(
            "Selecione um arquivo Excel ou CSV",
            type=['xlsx', 'csv'],
            help="Importe dados de rejeições de um arquivo Excel ou CSV"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.xlsx'):
                    df_import = pd.read_excel(uploaded_file)
                else:
                    df_import = pd.read_csv(uploaded_file)
                
                st.write("Prévia dos dados a importar:")
                st.dataframe(df_import, use_container_width=True)
                
                if st.button("✅ Confirmar Importação"):
                    conn = sqlite3.connect('sales_data.db')
                    df_import.to_sql('sales_rejections', conn, if_exists='append', index=False)
                    conn.close()
                    st.success("✅ Dados importados com sucesso!")
                    st.rerun()
            
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {str(e)}")
    
    # LIMPEZA DE DADOS
    st.markdown("---")
    st.markdown("### 🧹 Gerenciamento de Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Limpar Todos os Dados", help="Esta ação não pode ser desfeita!"):
            if st.checkbox("Tenho certeza que desejo limpar todos os dados"):
                clear_all_data()
                st.success("✅ Todos os dados foram removidos!")
                st.rerun()
    
    with col2:
        st.info("💡 **Dica**: Sempre faça backup dos seus dados antes de limpar.")
    
    # INFORMAÇÕES DO SISTEMA
    st.markdown("---")
    st.markdown("### ℹ️ Informações do Sistema")
    
    df_info = get_all_rejections()
    st.write(f"**Total de Registros**: {len(df_info)}")
    st.write(f"**Banco de Dados**: SQLite (sales_data.db)")
    st.write(f"**Última Atualização**: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")

# ============================================================================
# RODAPÉ
# ============================================================================
st.markdown("---")
st.markdown(f"""
    <div style='text-align: center; color: {V4_RED}; font-weight: 600; margin-top: 20px;'>
        <p>Sales Rejection Dashboard v1.0 | Desenvolvido com ❤️ para V4 Company</p>
    </div>
""", unsafe_allow_html=True)
