import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
import json
import os
from pathlib import Path
warnings.filterwarnings('ignore')

# 设置页面
st.set_page_config(
    page_title="体重管理助手",
    page_icon="⚖️",
    layout="wide"
)

# 应用标题
st.title("⚖️ 体重管理助手")
st.markdown("记录体重变化，制定减肥计划，跟踪进度预测")

# 数据文件路径
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
WEIGHT_DATA_FILE = DATA_DIR / "weight_data.csv"
TARGET_INFO_FILE = DATA_DIR / "target_info.json"

# 加载数据函数
@st.cache_data(ttl=300)
def load_weight_data():
    """加载体重数据"""
    if WEIGHT_DATA_FILE.exists():
        try:
            df = pd.read_csv(WEIGHT_DATA_FILE, parse_dates=['日期'])
            return df
        except Exception as e:
            st.warning(f"加载体重数据时出错: {e}")
    return pd.DataFrame(columns=['日期', '体重(kg)'])

@st.cache_data(ttl=300)
def load_target_info():
    """加载目标信息"""
    if TARGET_INFO_FILE.exists():
        try:
            with open(TARGET_INFO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"加载目标信息时出错: {e}")
    return {}

def save_weight_data(df):
    """保存体重数据"""
    try:
        df.to_csv(WEIGHT_DATA_FILE, index=False, encoding='utf-8')
        st.rerun()
    except Exception as e:
        st.error(f"保存体重数据时出错: {e}")

def save_target_info(info):
    """保存目标信息"""
    try:
        with open(TARGET_INFO_FILE, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        st.rerun()
    except Exception as e:
        st.error(f"保存目标信息时出错: {e}")

# 初始化session state
if 'weight_data' not in st.session_state:
    st.session_state.weight_data = load_weight_data()

if 'target_info' not in st.session_state:
    st.session_state.target_info = load_target_info()

# 数据备份提醒
if not WEIGHT_DATA_FILE.exists() and not TARGET_INFO_FILE.exists():
    st.info("📁 首次使用，数据将自动保存到本地文件中")
    st.caption(f"数据保存位置: {DATA_DIR.absolute()}")

# 侧边栏
with st.sidebar:
    st.header("📊 功能菜单")
    
    menu = st.radio(
        "选择功能",
        ["🏠 主页概览", "📝 记录体重", "🎯 设置目标", "📈 图表分析", "🔮 进度预测"]
    )
    
    st.divider()
    
    # 数据管理
    st.subheader("📁 数据管理")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 清空数据", type="secondary"):
            if st.session_state.weight_data.empty and not st.session_state.target_info:
                st.warning("暂无数据可清空")
            else:
                st.session_state.weight_data = pd.DataFrame(columns=['日期', '体重(kg)'])
                st.session_state.target_info = {}
                # 删除文件
                if WEIGHT_DATA_FILE.exists():
                    WEIGHT_DATA_FILE.unlink()
                if TARGET_INFO_FILE.exists():
                    TARGET_INFO_FILE.unlink()
                st.success("数据已清空！")
                st.rerun()
    
    with col2:
        if st.button("📥 导入数据"):
            uploaded_file = st.file_uploader("选择CSV文件", type=['csv'], key="upload_data")
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file, parse_dates=['日期'])
                    st.session_state.weight_data = df
                    save_weight_data(df)
                    st.success(f"成功导入 {len(df)} 条记录")
                except Exception as e:
                    st.error(f"导入失败: {e}")
    
    if st.button("💾 导出数据", use_container_width=True):
        if not st.session_state.weight_data.empty:
            csv = st.session_state.weight_data.to_csv(index=False)
            st.download_button(
                label="📤 下载CSV文件",
                data=csv,
                file_name=f"体重记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("暂无数据可导出")
    
    st.divider()
    
    # 数据统计
    st.subheader("📈 数据统计")
    if not st.session_state.weight_data.empty:
        st.write(f"📅 记录总数: {len(st.session_state.weight_data)} 条")
        st.write(f"📅 时间范围: {st.session_state.weight_data['日期'].min().strftime('%Y-%m-%d')} 至 {st.session_state.weight_data['日期'].max().strftime('%Y-%m-%d')}")
    
    if st.session_state.target_info:
        st.write(f"🎯 目标体重: {st.session_state.target_info.get('target_weight', 0)}kg")

# 主页概览
if menu == "🏠 主页概览":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="总记录天数",
            value=len(st.session_state.weight_data),
            delta=None
        )
    
    with col2:
        if len(st.session_state.weight_data) >= 2:
            first_weight = st.session_state.weight_data['体重(kg)'].iloc[0]
            last_weight = st.session_state.weight_data['体重(kg)'].iloc[-1]
            change = last_weight - first_weight
            st.metric(
                label="体重变化",
                value=f"{last_weight:.1f}kg",
                delta=f"{change:+.1f}kg" if change != 0 else "0.0kg"
            )
        else:
            st.metric(
                label="体重变化",
                value="0.0kg",
                delta="0.0kg"
            )
    
    with col3:
        if st.session_state.target_info and not st.session_state.weight_data.empty:
            current = st.session_state.weight_data['体重(kg)'].iloc[-1]
            target = st.session_state.target_info.get('target_weight', 0)
            if current > target:
                progress = 100 - ((current - target) / (current - target + 0.001)) * 100
            else:
                progress = 100
            st.metric(
                label="目标完成度",
                value=f"{progress:.1f}%",
                delta=None
            )
        else:
            st.metric(
                label="目标完成度",
                value="0%",
                delta=None
            )
    
    # 快速图表
    if not st.session_state.weight_data.empty:
        st.subheader("📊 最近变化趋势")
        
        # 确保日期排序
        weight_data_sorted = st.session_state.weight_data.sort_values('日期').copy()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=weight_data_sorted['日期'],
            y=weight_data_sorted['体重(kg)'],
            mode='lines+markers',
            name='体重',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=8)
        ))
        
        # 添加目标线
        if st.session_state.target_info:
            target_weight = st.session_state.target_info.get('target_weight')
            if target_weight:
                fig.add_hline(
                    y=target_weight,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"目标: {target_weight}kg",
                    annotation_position="bottom right"
                )
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            xaxis_title="日期",
            yaxis_title="体重(kg)",
            hovermode='x unified',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👆 请先记录体重数据")

# 记录体重
elif menu == "📝 记录体重":
    st.header("📝 记录体重")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 选择日期
        record_date = st.date_input(
            "选择记录日期",
            datetime.now().date(),
            help="选择要记录体重的日期"
        )
    
    with col2:
        # 输入体重
        weight = st.number_input(
            "体重 (kg)",
            min_value=30.0,
            max_value=200.0,
            value=60.0,
            step=0.1,
            format="%.1f",
            help="请输入您的体重"
        )
    
    # 提交按钮
    if st.button("✅ 保存记录", type="primary", use_container_width=True):
        new_record = pd.DataFrame({
            '日期': [record_date],
            '体重(kg)': [weight]
        })
        
        # 检查是否已有该日期的记录
        if not st.session_state.weight_data.empty:
            # 确保日期格式一致
            st.session_state.weight_data['日期'] = pd.to_datetime(st.session_state.weight_data['日期']).dt.date
            existing_dates = st.session_state.weight_data['日期'].tolist()
            
            if record_date in existing_dates:
                # 更新已有记录
                idx = existing_dates.index(record_date)
                st.session_state.weight_data.at[idx, '体重(kg)'] = weight
                st.success(f"✅ 已更新 {record_date} 的体重记录为 {weight}kg")
            else:
                # 添加新记录
                st.session_state.weight_data = pd.concat([st.session_state.weight_data, new_record], ignore_index=True)
                st.success(f"✅ 已记录 {record_date} 的体重：{weight}kg")
        else:
            st.session_state.weight_data = new_record
            st.success(f"✅ 已记录 {record_date} 的体重：{weight}kg")
        
        # 按日期排序
        st.session_state.weight_data['日期'] = pd.to_datetime(st.session_state.weight_data['日期'])
        st.session_state.weight_data = st.session_state.weight_data.sort_values('日期').reset_index(drop=True)
        
        # 保存到文件
        save_weight_data(st.session_state.weight_data)
    
    # 显示记录表格
    if not st.session_state.weight_data.empty:
        st.subheader("📋 体重记录表")
        
        # 确保日期格式正确
        display_df = st.session_state.weight_data.copy()
        display_df['日期'] = pd.to_datetime(display_df['日期'])
        
        # 计算变化
        display_df['变化'] = display_df['体重(kg)'].diff()
        display_df['变化%'] = (display_df['体重(kg)'].pct_change() * 100).round(2)
        
        # 格式化显示
        display_df_display = display_df.copy()
        display_df_display['日期'] = display_df_display['日期'].dt.strftime('%Y-%m-%d')
        display_df_display['体重(kg)'] = display_df_display['体重(kg)'].apply(lambda x: f"{x:.1f}")
        display_df_display['变化'] = display_df_display['变化'].apply(lambda x: f"{x:+.1f}" if pd.notnull(x) else "")
        display_df_display['变化%'] = display_df_display['变化%'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "")
        
        st.dataframe(
            display_df_display,
            column_config={
                "日期": st.column_config.TextColumn("📅 日期"),
                "体重(kg)": st.column_config.TextColumn("⚖️ 体重(kg)"),
                "变化": st.column_config.TextColumn("📈 变化(kg)"),
                "变化%": st.column_config.TextColumn("📊 变化%")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # 删除记录功能
        if len(st.session_state.weight_data) > 0:
            st.subheader("🗑️ 删除记录")
            
            # 获取日期列表
            date_options = display_df_display['日期'].tolist()
            
            dates_to_delete = st.multiselect(
                "选择要删除的日期记录",
                date_options,
                help="选择要删除的体重记录"
            )
            
            if dates_to_delete and st.button("删除选中的记录", type="secondary"):
                # 转换为datetime格式进行匹配
                dates_to_delete_dt = pd.to_datetime(dates_to_delete)
                st.session_state.weight_data = st.session_state.weight_data[
                    ~st.session_state.weight_data['日期'].isin(dates_to_delete_dt)
                ].reset_index(drop=True)
                
                # 保存到文件
                save_weight_data(st.session_state.weight_data)
                st.success(f"✅ 已删除 {len(dates_to_delete)} 条记录")
    else:
        st.info("📝 暂无记录，请先记录您的体重")

# 设置目标
elif menu == "🎯 设置目标":
    st.header("🎯 设置减肥目标")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not st.session_state.weight_data.empty:
            current_weight = st.session_state.weight_data['体重(kg)'].iloc[-1]
            st.info(f"当前最新体重：**{current_weight:.1f}kg**")
        else:
            st.warning("暂无体重记录")
            current_weight = st.number_input(
                "当前体重 (kg)",
                min_value=30.0,
                max_value=200.0,
                value=70.0,
                step=0.1
            )
    
    with col2:
        target_weight = st.number_input(
            "目标体重 (kg)",
            min_value=30.0,
            max_value=200.0,
            value=60.0,
            step=0.1,
            help="您希望达到的目标体重"
        )
    
    col3, col4 = st.columns(2)
    
    with col3:
        plan_days = st.number_input(
            "计划天数 (天)",
            min_value=1,
            max_value=365,
            value=30,
            help="计划用多少天达到目标"
        )
    
    with col4:
        start_date = st.date_input(
            "计划开始日期",
            datetime.now().date() if st.session_state.weight_data.empty else st.session_state.weight_data['日期'].iloc[-1].date(),
            help="减肥计划开始日期"
        )
    
    # 计算信息
    weight_to_lose = current_weight - target_weight
    daily_target = weight_to_lose / plan_days if plan_days > 0 and weight_to_lose > 0 else 0
    
    st.divider()
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.metric("需减重量", f"{weight_to_lose:.1f}kg")
    
    with col_b:
        st.metric("每日目标", f"{daily_target:.2f}kg/天")
    
    with col_c:
        end_date = start_date + timedelta(days=plan_days)
        st.metric("预计完成", end_date.strftime("%Y-%m-%d"))
    
    # 保存目标
    if st.button("💾 保存目标计划", type="primary", use_container_width=True):
        st.session_state.target_info = {
            'current_weight': float(current_weight),
            'target_weight': float(target_weight),
            'plan_days': int(plan_days),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'daily_target': daily_target
        }
        save_target_info(st.session_state.target_info)
        st.success("✅ 目标计划已保存！")
    
    # 显示当前目标
    if st.session_state.target_info:
        st.divider()
        st.subheader("📋 当前目标")
        info = st.session_state.target_info
        st.write(f"**目标体重**: {info.get('target_weight', 0)}kg")
        st.write(f"**计划天数**: {info.get('plan_days', 0)} 天")
        st.write(f"**开始日期**: {info.get('start_date', '未设置')}")
        st.write(f"**每日目标**: {info.get('daily_target', 0):.3f}kg/天")

# 图表分析
elif menu == "📈 图表分析":
    st.header("📈 体重变化图表")
    
    if st.session_state.weight_data.empty:
        st.warning("暂无体重数据，请先记录体重")
    else:
        # 确保数据排序
        weight_data = st.session_state.weight_data.sort_values('日期').copy()
        
        # 创建多个图表
        tab1, tab2, tab3 = st.tabs(["📈 折线图", "📊 柱状图", "🔍 详细分析"])
        
        with tab1:
            fig = go.Figure()
            
            # 添加体重线
            fig.add_trace(go.Scatter(
                x=weight_data['日期'],
                y=weight_data['体重(kg)'],
                mode='lines+markers',
                name='体重',
                line=dict(color='#FF6B6B', width=3),
                marker=dict(size=8, color='#FF6B6B'),
                hovertemplate='日期: %{x|%Y-%m-%d}<br>体重: %{y:.1f}kg<extra></extra>'
            ))
            
            # 如果有目标，添加目标线
            if st.session_state.target_info:
                fig.add_hline(
                    y=st.session_state.target_info.get('target_weight', 0),
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"目标体重: {st.session_state.target_info.get('target_weight', 0)}kg",
                    annotation_position="bottom right"
                )
            
            fig.update_layout(
                title="体重变化趋势",
                xaxis_title="日期",
                yaxis_title="体重 (kg)",
                template='plotly_white',
                height=500,
                hovermode='x unified',
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # 计算每日变化
            weight_data['变化'] = weight_data['体重(kg)'].diff()
            
            fig2 = make_subplots(rows=2, cols=1, vertical_spacing=0.15)
            
            # 体重柱状图
            fig2.add_trace(
                go.Bar(
                    x=weight_data['日期'],
                    y=weight_data['体重(kg)'],
                    name='体重',
                    marker_color='#4ECDC4',
                    hovertemplate='日期: %{x|%Y-%m-%d}<br>体重: %{y:.1f}kg<extra></extra>'
                ),
                row=1, col=1
            )
            
            # 变化柱状图
            fig2.add_trace(
                go.Bar(
                    x=weight_data['日期'][1:],
                    y=weight_data['变化'][1:],
                    name='日变化',
                    marker_color='#FFD166',
                    hovertemplate='日期: %{x|%Y-%m-%d}<br>变化: %{y:+.1f}kg<extra></extra>'
                ),
                row=2, col=1
            )
            
            fig2.update_layout(
                title="体重与变化分析",
                height=600,
                showlegend=True,
                template='plotly_white'
            )
            
            fig2.update_yaxes(title_text="体重 (kg)", row=1, col=1)
            fig2.update_yaxes(title_text="日变化 (kg)", row=2, col=1)
            
            st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("统计摘要")
                
                stats_df = pd.DataFrame({
                    '统计项': ['平均体重', '最高体重', '最低体重', '体重范围', '总记录天数', '平均日变化'],
                    '数值': [
                        f"{weight_data['体重(kg)'].mean():.1f}kg",
                        f"{weight_data['体重(kg)'].max():.1f}kg",
                        f"{weight_data['体重(kg)'].min():.1f}kg",
                        f"{weight_data['体重(kg)'].max() - weight_data['体重(kg)'].min():.1f}kg",
                        f"{len(weight_data)} 天",
                        f"{weight_data['变化'][1:].mean():.2f}kg" if len(weight_data) > 1 else "0.00kg"
                    ]
                })
                
                st.dataframe(stats_df, hide_index=True, use_container_width=True)
            
            with col2:
                st.subheader("最近变化")
                
                if len(weight_data) > 1:
                    # 取最近7天或所有数据
                    recent_count = min(7, len(weight_data))
                    recent_changes = weight_data.tail(recent_count).copy()
                    recent_changes['日期'] = recent_changes['日期'].dt.strftime('%m-%d')
                    
                    fig3 = go.Figure()
                    fig3.add_trace(go.Scatter(
                        x=recent_changes['日期'],
                        y=recent_changes['体重(kg)'],
                        mode='lines+markers+text',
                        name='最近体重',
                        line=dict(color='#118AB2', width=2),
                        marker=dict(size=10),
                        text=recent_changes['体重(kg)'].round(1),
                        textposition="top center"
                    ))
                    
                    fig3.update_layout(
                        title=f"最近{recent_count}天体重",
                        height=300,
                        template='plotly_white',
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig3, use_container_width=True)
                    
                    # 显示变化统计
                    if recent_count > 1:
                        total_change = recent_changes['体重(kg)'].iloc[-1] - recent_changes['体重(kg)'].iloc[0]
                        avg_change = total_change / (recent_count - 1)
                        st.metric("最近变化", f"{total_change:+.1f}kg", f"平均{avg_change:+.2f}kg/天")

# 进度预测
elif menu == "🔮 进度预测":
    st.header("🔮 减肥进度预测")
    
    if st.session_state.weight_data.empty:
        st.warning("暂无体重数据，请先记录体重")
    elif not st.session_state.target_info:
        st.warning("请先设置减肥目标")
    else:
        # 获取数据
        weight_data = st.session_state.weight_data.sort_values('日期').copy()
        target_info = st.session_state.target_info
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 计划信息")
            st.write(f"**当前体重**: {target_info.get('current_weight', 0):.1f}kg")
            st.write(f"**目标体重**: {target_info.get('target_weight', 0):.1f}kg")
            st.write(f"**计划天数**: {target_info.get('plan_days', 0)} 天")
            st.write(f"**每日目标**: {target_info.get('daily_target', 0):.3f}kg/天")
        
        with col2:
            st.subheader("📊 进度概览")
            
            # 计算实际进度
            if len(weight_data) >= 2:
                actual_days = (weight_data['日期'].iloc[-1] - weight_data['日期'].iloc[0]).days
                actual_change = weight_data['体重(kg)'].iloc[-1] - weight_data['体重(kg)'].iloc[0]
                expected_change = target_info.get('daily_target', 0) * actual_days
                
                if expected_change != 0:
                    progress = (actual_change / expected_change * 100)
                else:
                    progress = 0
                
                st.metric("实际减重", f"{actual_change:+.2f}kg")
                st.metric("预期减重", f"{expected_change:+.2f}kg")
                st.metric("进度差异", f"{(actual_change - expected_change):+.2f}kg")
        
        st.divider()
        
        # 预测图表
        st.subheader("📈 未来预测")
        
        # 分页显示
        days_per_page = st.slider("每页显示天数", 7, 90, 30, 7)
        
        # 创建预测数据
        last_date = weight_data['日期'].iloc[-1]
        last_weight = weight_data['体重(kg)'].iloc[-1]
        target_weight = target_info.get('target_weight', 0)
        plan_days = target_info.get('plan_days', 30)
        daily_target = target_info.get('daily_target', 0)
        
        # 生成预测日期
        future_dates = [last_date + timedelta(days=i) for i in range(1, plan_days + 1)]
        predicted_weights = [max(target_weight, last_weight - daily_target * i) for i in range(1, plan_days + 1)]
        
        # 分页处理
        num_pages = (plan_days + days_per_page - 1) // days_per_page
        
        if num_pages > 1:
            page = st.number_input("选择页码", 1, num_pages, 1, key="page_input")
            start_idx = (page - 1) * days_per_page
            end_idx = min(page * days_per_page, plan_days)
            
            page_dates = future_dates[start_idx:end_idx]
            page_weights = predicted_weights[start_idx:end_idx]
            
            st.caption(f"显示第 {page} 页，第 {start_idx+1}-{end_idx} 天预测")
        else:
            page_dates = future_dates
            page_weights = predicted_weights
        
        # 创建预测图表
        fig = go.Figure()
        
        # 历史数据
        fig.add_trace(go.Scatter(
            x=weight_data['日期'],
            y=weight_data['体重(kg)'],
            mode='lines+markers',
            name='历史记录',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=8)
        ))
        
        # 预测数据
        fig.add_trace(go.Scatter(
            x=page_dates,
            y=page_weights,
            mode='lines+markers',
            name='预测趋势',
            line=dict(color='#118AB2', width=3, dash='dash'),
            marker=dict(size=6, symbol='circle-open')
        ))
        
        # 添加目标线
        fig.add_hline(
            y=target_weight,
            line_dash="dot",
            line_color="green",
            annotation_text=f"目标体重: {target_weight}kg",
            annotation_position="bottom right"
        )
        
        # 添加预计达成日期
        if daily_target > 0 and last_weight > target_weight:
            days_to_goal = int((last_weight - target_weight) / daily_target)
            if 0 < days_to_goal <= plan_days:
                goal_date = last_date + timedelta(days=days_to_goal)
                fig.add_vline(
                    x=goal_date,
                    line_dash="dash",
                    line_color="purple",
                    annotation_text=f"预计达成: {goal_date.strftime('%m-%d')}",
                    annotation_position="top right"
                )
        
        fig.update_layout(
            title=f"体重预测 ({page_dates[0].strftime('%m-%d')} 至 {page_dates[-1].strftime('%m-%d')})",
            xaxis_title="日期",
            yaxis_title="体重 (kg)",
            template='plotly_white',
            height=500,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 预测表格
        st.subheader("📋 详细预测表")
        
        predict_df = pd.DataFrame({
            '日期': [d.strftime('%Y-%m-%d') for d in page_dates],
            '预测体重(kg)': [f"{w:.2f}" for w in page_weights],
            '日目标(kg)': [f"{daily_target:.3f}" for _ in page_weights],
            '距目标(kg)': [f"{(w - target_weight):.2f}" for w in page_weights]
        })
        
        st.dataframe(predict_df, hide_index=True, use_container_width=True)
        
        # 添加鼓舞人心的信息
        st.divider()
        st.subheader("💪 保持动力！")
        
        progress_text = [
            "🚀 你正在朝着目标前进！每天进步一点点，积累就是巨大的成功！",
            "💧 健康的生活方式比短期节食更重要，坚持就是胜利！",
            "🏃 记住，减肥是马拉松，不是短跑。保持耐心，享受过程！",
            "🥗 均衡饮食和适度运动是健康减肥的最佳组合！",
            "🎯 设定合理的小目标，完成一个就奖励自己一下！"
        ]
        
        st.info(np.random.choice(progress_text))

# 页脚
st.divider()
st.caption("📱 体重管理助手 v2.0 | 数据自动保存在本地文件中 | 程序编写：房星宇")

# 显示数据信息
with st.sidebar:
    st.divider()
    st.caption("💾 数据已自动保存")
    if WEIGHT_DATA_FILE.exists():
        file_size = WEIGHT_DATA_FILE.stat().st_size
        st.caption(f"数据文件: {file_size/1024:.1f} KB")
