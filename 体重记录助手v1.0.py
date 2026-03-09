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
def load_weight_data():
    """加载体重数据"""
    try:
        if WEIGHT_DATA_FILE.exists():
            df = pd.read_csv(WEIGHT_DATA_FILE)
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'])
            return df
    except Exception as e:
        st.error(f"加载体重数据时出错: {e}")
    return pd.DataFrame(columns=['日期', '体重(kg)'])

def load_target_info():
    """加载目标信息"""
    try:
        if TARGET_INFO_FILE.exists():
            with open(TARGET_INFO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"加载目标信息时出错: {e}")
    return {}

def save_weight_data():
    """保存体重数据到文件"""
    try:
        if not st.session_state.weight_data.empty:
            df = st.session_state.weight_data.copy()
            df['日期'] = pd.to_datetime(df['日期'])
            df.to_csv(WEIGHT_DATA_FILE, index=False)
            return True
    except Exception as e:
        st.error(f"保存体重数据时出错: {e}")
    return False

def save_target_info():
    """保存目标信息到文件"""
    try:
        with open(TARGET_INFO_FILE, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.target_info, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存目标信息时出错: {e}")
    return False

# 初始化session state
if 'initialized' not in st.session_state:
    # 从文件加载数据
    st.session_state.weight_data = load_weight_data()
    st.session_state.target_info = load_target_info()
    st.session_state.initialized = True

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
    
    # 显示数据状态
    if not st.session_state.weight_data.empty:
        st.info(f"📊 当前有 {len(st.session_state.weight_data)} 条体重记录")
        if WEIGHT_DATA_FILE.exists():
            file_size = WEIGHT_DATA_FILE.stat().st_size / 1024
            st.caption(f"数据文件: {file_size:.1f} KB")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 清空数据", type="secondary"):
            if not st.session_state.weight_data.empty or st.session_state.target_info:
                # 确认对话框
                if st.session_state.get('confirm_clear', False):
                    st.session_state.weight_data = pd.DataFrame(columns=['日期', '体重(kg)'])
                    st.session_state.target_info = {}
                    
                    # 删除文件
                    if WEIGHT_DATA_FILE.exists():
                        os.remove(WEIGHT_DATA_FILE)
                    if TARGET_INFO_FILE.exists():
                        os.remove(TARGET_INFO_FILE)
                    
                    st.session_state.confirm_clear = False
                    st.success("数据已清空！")
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("确认要清空所有数据吗？再次点击确认清空。")
            else:
                st.warning("暂无数据可清空")
    
    with col2:
        if st.button("💾 备份数据"):
            if not st.session_state.weight_data.empty:
                # 自动保存当前数据
                save_weight_data()
                if st.session_state.target_info:
                    save_target_info()
                
                # 提供下载
                csv_data = st.session_state.weight_data.to_csv(index=False)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 下载备份",
                    data=csv_data,
                    file_name=f"体重记录_备份_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("暂无数据可备份")
    
    st.divider()
    
    # 数据导入
    st.subheader("📤 导入数据")
    uploaded_file = st.file_uploader(
        "上传CSV文件",
        type=['csv'],
        help="上传包含'日期'和'体重(kg)'列的CSV文件"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = ['日期', '体重(kg)']
            
            if all(col in df.columns for col in required_cols):
                # 转换日期格式
                df['日期'] = pd.to_datetime(df['日期'])
                # 合并数据
                if not st.session_state.weight_data.empty:
                    # 合并并去重
                    combined = pd.concat([st.session_state.weight_data, df])
                    combined = combined.drop_duplicates(subset=['日期'], keep='last')
                    st.session_state.weight_data = combined.sort_values('日期').reset_index(drop=True)
                else:
                    st.session_state.weight_data = df.sort_values('日期').reset_index(drop=True)
                
                # 保存到文件
                save_weight_data()
                st.success(f"✅ 成功导入 {len(df)} 条记录")
                st.rerun()
            else:
                st.error("CSV文件必须包含'日期'和'体重(kg)'列")
        except Exception as e:
            st.error(f"导入失败: {e}")

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
            change_color = "inverse" if change < 0 else "normal"
            st.metric(
                label="体重变化",
                value=f"{last_weight:.1f}kg",
                delta=f"{change:+.1f}kg",
                delta_color=change_color
            )
        elif len(st.session_state.weight_data) == 1:
            weight = st.session_state.weight_data['体重(kg)'].iloc[0]
            st.metric(
                label="当前体重",
                value=f"{weight:.1f}kg",
                delta=None
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
                progress = ((current - target) / (st.session_state.target_info.get('current_weight', current) - target)) * 100
                progress = min(100, max(0, 100 - progress))
            else:
                progress = 100
            st.metric(
                label="目标完成度",
                value=f"{progress:.1f}%",
                delta=None
            )
        elif st.session_state.target_info:
            st.metric(
                label="目标设置",
                value="已设置",
                delta=None
            )
        else:
            st.metric(
                label="目标设置",
                value="未设置",
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
        st.info("👋 欢迎使用体重管理助手！")
        st.write("请先记录您的体重数据。")

# 记录体重
elif menu == "📝 记录体重":
    st.header("📝 记录体重")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 选择日期
        record_date = st.date_input(
            "选择记录日期",
            value=datetime.now().date(),
            help="选择要记录体重的日期"
        )
    
    with col2:
        # 输入体重
        weight = st.number_input(
            "体重 (kg)",
            min_value=30.0,
            max_value=300.0,
            value=70.0,
            step=0.1,
            format="%.1f",
            help="请输入您的体重"
        )
    
    # 提交按钮
    if st.button("✅ 保存记录", type="primary", use_container_width=True):
        # 检查数据是否为空
        if st.session_state.weight_data.empty:
            # 创建新DataFrame
            st.session_state.weight_data = pd.DataFrame({
                '日期': [record_date],
                '体重(kg)': [weight]
            })
            message = f"✅ 已记录 {record_date} 的体重：{weight}kg"
        else:
            # 确保日期格式
            st.session_state.weight_data['日期'] = pd.to_datetime(st.session_state.weight_data['日期'])
            
            # 检查日期是否已存在
            existing_dates = pd.to_datetime(st.session_state.weight_data['日期']).dt.date.tolist()
            
            if record_date in existing_dates:
                # 更新已有记录
                idx = existing_dates.index(record_date)
                st.session_state.weight_data.at[idx, '体重(kg)'] = weight
                message = f"✅ 已更新 {record_date} 的体重记录为 {weight}kg"
            else:
                # 添加新记录
                new_record = pd.DataFrame({
                    '日期': [record_date],
                    '体重(kg)': [weight]
                })
                st.session_state.weight_data = pd.concat(
                    [st.session_state.weight_data, new_record], 
                    ignore_index=True
                )
                message = f"✅ 已记录 {record_date} 的体重：{weight}kg"
        
        # 按日期排序
        st.session_state.weight_data = st.session_state.weight_data.sort_values('日期').reset_index(drop=True)
        
        # 保存到文件（不触发rerun，避免递归）
        if save_weight_data():
            st.success(message)
        else:
            st.error("保存数据时出错，请重试")
    
    # 显示记录表格
    if not st.session_state.weight_data.empty:
        st.subheader("📋 体重记录表")
        
        # 确保日期格式正确
        display_df = st.session_state.weight_data.copy()
        display_df['日期'] = pd.to_datetime(display_df['日期'])
        
        # 计算变化
        display_df['变化'] = display_df['体重(kg)'].diff()
        display_df['变化%'] = (display_df['体重(kg)'].pct_change() * 100).round(2)
        
        # 创建显示用的副本
        display_df_display = display_df.copy()
        display_df_display['日期'] = display_df_display['日期'].dt.strftime('%Y-%m-%d')
        display_df_display['体重(kg)'] = display_df_display['体重(kg)'].apply(lambda x: f"{x:.1f}")
        
        # 格式化变化列
        def format_change(x):
            if pd.isna(x):
                return ""
            return f"{x:+.1f}"
        
        def format_change_percent(x):
            if pd.isna(x):
                return ""
            return f"{x:+.1f}%"
        
        display_df_display['变化'] = display_df_display['变化'].apply(format_change)
        display_df_display['变化%'] = display_df_display['变化%'].apply(format_change_percent)
        
        st.dataframe(
            display_df_display,
            column_config={
                "日期": st.column_config.TextColumn("📅 日期"),
                "体重(kg)": st.column_config.NumberColumn("⚖️ 体重(kg)", format="%.1f"),
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
                options=date_options,
                help="选择要删除的体重记录"
            )
            
            if dates_to_delete:
                col_del1, col_del2 = st.columns([3, 1])
                with col_del2:
                    if st.button("确认删除", type="secondary"):
                        # 转换为datetime格式进行匹配
                        dates_to_delete_dt = pd.to_datetime(dates_to_delete)
                        st.session_state.weight_data = st.session_state.weight_data[
                            ~st.session_state.weight_data['日期'].isin(dates_to_delete_dt)
                        ].reset_index(drop=True)
                        
                        # 保存到文件
                        if save_weight_data():
                            st.success(f"✅ 已删除 {len(dates_to_delete)} 条记录")
                            st.rerun()
                        else:
                            st.error("删除数据时出错")
    else:
        st.info("📝 暂无记录，请先记录您的体重")

# 设置目标
elif menu == "🎯 设置目标":
    st.header("🎯 设置减肥目标")
    
    # 获取当前体重
    if not st.session_state.weight_data.empty:
        current_weight = float(st.session_state.weight_data['体重(kg)'].iloc[-1])
        st.info(f"📊 当前最新体重：**{current_weight:.1f}kg**")
    else:
        current_weight = st.number_input(
            "当前体重 (kg)",
            min_value=30.0,
            max_value=300.0,
            value=70.0,
            step=0.1
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_weight = st.number_input(
            "目标体重 (kg)",
            min_value=30.0,
            max_value=300.0,
            value=60.0,
            step=0.1,
            help="您希望达到的目标体重"
        )
    
    with col2:
        plan_days = st.number_input(
            "计划天数 (天)",
            min_value=1,
            max_value=365,
            value=30,
            help="计划用多少天达到目标"
        )
    
    # 计算信息
    weight_to_lose = current_weight - target_weight
    if plan_days > 0 and weight_to_lose > 0:
        daily_target = weight_to_lose / plan_days
    else:
        daily_target = 0
    
    if weight_to_lose > 0:
        st.success(f"🎯 需要减重: **{weight_to_lose:.1f}kg**")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric(
                "需减重量",
                f"{weight_to_lose:.1f}kg",
                delta=None
            )
        
        with col_b:
            st.metric(
                "每日目标",
                f"{daily_target:.3f}kg/天",
                delta=None
            )
        
        with col_c:
            end_date = datetime.now().date() + timedelta(days=plan_days)
            st.metric(
                "预计完成",
                end_date.strftime("%m-%d"),
                delta=None
            )
    elif weight_to_lose < 0:
        st.warning(f"目标体重 ({target_weight}kg) 低于当前体重 ({current_weight}kg)，您可能需要增重哦！")
    else:
        st.info("您已经达到目标体重！")
    
    # 保存目标
    if st.button("💾 保存目标计划", type="primary", use_container_width=True):
        target_info = {
            'current_weight': float(current_weight),
            'target_weight': float(target_weight),
            'plan_days': int(plan_days),
            'daily_target': float(daily_target),
            'set_date': datetime.now().strftime('%Y-%m-%d'),
            'end_date': (datetime.now().date() + timedelta(days=plan_days)).strftime('%Y-%m-%d')
        }
        
        st.session_state.target_info = target_info
        
        # 保存到文件
        if save_target_info():
            st.success("✅ 目标计划已保存！")
        else:
            st.error("保存目标时出错，请重试")
    
    # 显示当前目标
    if st.session_state.target_info:
        st.divider()
        st.subheader("📋 当前目标")
        info = st.session_state.target_info
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.write(f"**目标体重**: {info.get('target_weight', 0):.1f}kg")
            st.write(f"**计划天数**: {info.get('plan_days', 0)} 天")
        
        with col_info2:
            st.write(f"**每日目标**: {info.get('daily_target', 0):.3f}kg/天")
            if info.get('end_date'):
                st.write(f"**预计完成**: {info['end_date']}")

# 图表分析
elif menu == "📈 图表分析":
    st.header("📈 体重变化图表")
    
    if st.session_state.weight_data.empty:
        st.warning("暂无体重数据，请先记录体重")
    else:
        # 确保数据排序
        weight_data = st.session_state.weight_data.sort_values('日期').copy()
        
        # 创建多个图表
        tab1, tab2, tab3 = st.tabs(["📈 趋势图", "📊 对比图", "🔍 统计信息"])
        
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
                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>体重: %{y:.1f}kg<extra></extra>'
            ))
            
            # 如果有目标，添加目标线
            if st.session_state.target_info:
                target_weight = st.session_state.target_info.get('target_weight', 0)
                fig.add_hline(
                    y=target_weight,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"目标: {target_weight}kg",
                    annotation_position="bottom right"
                )
            
            fig.update_layout(
                title="体重变化趋势图",
                xaxis_title="日期",
                yaxis_title="体重 (kg)",
                template='plotly_white',
                height=500,
                hovermode='x unified',
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # 计算每周/每月平均
            weight_data_resampled = weight_data.copy()
            weight_data_resampled.set_index('日期', inplace=True)
            
            # 选择时间粒度
            period = st.selectbox(
                "选择统计周期",
                ["日", "周", "月"],
                index=0
            )
            
            if period == "周":
                resampled = weight_data_resampled['体重(kg)'].resample('W').mean().reset_index()
                title = "周平均体重"
            elif period == "月":
                resampled = weight_data_resampled['体重(kg)'].resample('M').mean().reset_index()
                title = "月平均体重"
            else:
                resampled = weight_data_resampled.reset_index()
                title = "每日体重"
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=resampled['日期'],
                y=resampled['体重(kg)'],
                name=period,
                marker_color='#4ECDC4',
                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>体重: %{y:.1f}kg<extra></extra>'
            ))
            
            fig2.update_layout(
                title=title,
                height=500,
                template='plotly_white',
                showlegend=False
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:
            col_stat1, col_stat2 = st.columns([2, 1])
            
            with col_stat1:
                # 计算统计指标
                stats = {
                    '平均体重': f"{weight_data['体重(kg)'].mean():.2f}kg",
                    '最高体重': f"{weight_data['体重(kg)'].max():.2f}kg ({weight_data['日期'][weight_data['体重(kg)'].idxmax()].strftime('%m-%d')})",
                    '最低体重': f"{weight_data['体重(kg)'].min():.2f}kg ({weight_data['日期'][weight_data['体重(kg)'].idxmin()].strftime('%m-%d')})",
                    '体重范围': f"{weight_data['体重(kg)'].max() - weight_data['体重(kg)'].min():.2f}kg",
                    '记录天数': f"{len(weight_data)} 天",
                    '时间跨度': f"{(weight_data['日期'].iloc[-1] - weight_data['日期'].iloc[0]).days + 1} 天"
                }
                
                if len(weight_data) > 1:
                    changes = weight_data['体重(kg)'].diff().dropna()
                    stats.update({
                        '总变化': f"{weight_data['体重(kg)'].iloc[-1] - weight_data['体重(kg)'].iloc[0]:+.2f}kg",
                        '平均日变化': f"{changes.mean():+.3f}kg/天",
                        '最大单日变化': f"{changes.max():+.2f}kg",
                        '最小单日变化': f"{changes.min():+.2f}kg"
                    })
                
                # 显示统计表
                st.subheader("📊 统计摘要")
                stats_df = pd.DataFrame(list(stats.items()), columns=['统计项', '数值'])
                st.dataframe(stats_df, hide_index=True, use_container_width=True)
            
            with col_stat2:
                st.subheader("📈 近期趋势")
                
                if len(weight_data) > 1:
                    # 最近7天或所有数据
                    recent_days = min(7, len(weight_data))
                    recent_data = weight_data.tail(recent_days).copy()
                    
                    # 计算变化
                    if len(recent_data) > 1:
                        recent_change = recent_data['体重(kg)'].iloc[-1] - recent_data['体重(kg)'].iloc[0]
                        avg_daily_change = recent_change / (len(recent_data) - 1)
                        
                        if recent_change < 0:
                            st.success(f"📉 最近{recent_days}天: {recent_change:+.1f}kg")
                            st.metric("平均日变化", f"{avg_daily_change:+.3f}kg", delta=None)
                        elif recent_change > 0:
                            st.warning(f"📈 最近{recent_days}天: {recent_change:+.1f}kg")
                            st.metric("平均日变化", f"{avg_daily_change:+.3f}kg", delta=None)
                        else:
                            st.info(f"📊 最近{recent_days}天: 无变化")
                    
                    # 简单折线图
                    fig_simple = go.Figure()
                    fig_simple.add_trace(go.Scatter(
                        x=recent_data['日期'].dt.strftime('%m-%d'),
                        y=recent_data['体重(kg)'],
                        mode='lines+markers',
                        line=dict(color='#118AB2', width=2),
                        marker=dict(size=8)
                    ))
                    
                    fig_simple.update_layout(
                        title=f"最近{recent_days}天体重",
                        height=250,
                        template='plotly_white',
                        showlegend=False,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    
                    st.plotly_chart(fig_simple, use_container_width=True)

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
        
        # 计算关键指标
        current_weight = float(weight_data['体重(kg)'].iloc[-1])
        target_weight = float(target_info.get('target_weight', 0))
        daily_target = float(target_info.get('daily_target', 0))
        plan_days = int(target_info.get('plan_days', 30))
        
        # 进度概览
        col_overview1, col_overview2, col_overview3 = st.columns(3)
        
        with col_overview1:
            remaining = max(0, current_weight - target_weight)
            st.metric(
                "还需减重",
                f"{remaining:.1f}kg",
                delta=None
            )
        
        with col_overview2:
            if daily_target > 0:
                days_left = int(remaining / daily_target) if daily_target > 0 else 0
                st.metric(
                    "预计还需",
                    f"{days_left} 天",
                    delta=None
                )
            else:
                st.metric("每日目标", "0kg", delta=None)
        
        with col_overview3:
            if daily_target > 0:
                completion_date = datetime.now().date() + timedelta(days=days_left)
                st.metric(
                    "预计完成",
                    completion_date.strftime("%m-%d"),
                    delta=None
                )
        
        # 预测图表
        st.subheader("📈 未来趋势预测")
        
        # 生成预测数据
        last_date = weight_data['日期'].iloc[-1]
        prediction_days = min(plan_days, 90)  # 最多预测90天
        
        future_dates = [last_date + timedelta(days=i) for i in range(1, prediction_days + 1)]
        predicted_weights = []
        
        for i in range(1, prediction_days + 1):
            pred_weight = current_weight - (daily_target * i)
            if pred_weight < target_weight:
                pred_weight = target_weight
            predicted_weights.append(pred_weight)
        
        # 创建预测图表
        fig = go.Figure()
        
        # 历史数据（最后14天或全部）
        show_days = min(14, len(weight_data))
        recent_history = weight_data.tail(show_days)
        
        fig.add_trace(go.Scatter(
            x=recent_history['日期'],
            y=recent_history['体重(kg)'],
            mode='lines+markers',
            name='历史记录',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=8)
        ))
        
        # 预测数据
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=predicted_weights,
            mode='lines',
            name='预测趋势',
            line=dict(color='#118ABB', width=3, dash='dash')
        ))
        
        # 添加目标线
        fig.add_hline(
            y=target_weight,
            line_dash="dot",
            line_color="green",
            annotation_text=f"目标体重: {target_weight}kg",
            annotation_position="bottom right"
        )
        
        # 添加当前体重线
        fig.add_hline(
            y=current_weight,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"当前体重: {current_weight}kg",
            annotation_position="top right"
        )
        
        fig.update_layout(
            title=f"体重预测 ({show_days}天历史 + {prediction_days}天预测)",
            xaxis_title="日期",
            yaxis_title="体重 (kg)",
            template='plotly_white',
            height=500,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 预测详情表格
        st.subheader("📋 详细预测表")
        
        # 分页显示预测
        page_size = st.selectbox("每页显示天数", [7, 14, 30], index=1)
        num_pages = (prediction_days + page_size - 1) // page_size
        
        if num_pages > 1:
            page = st.number_input("页码", 1, num_pages, 1, key="prediction_page")
            start_idx = (page - 1) * page_size
            end_idx = min(page * page_size, prediction_days)
        else:
            page = 1
            start_idx = 0
            end_idx = prediction_days
        
        page_dates = future_dates[start_idx:end_idx]
        page_weights = predicted_weights[start_idx:end_idx]
        
        # 创建预测表格
        predict_data = []
        for i, (date, weight) in enumerate(zip(page_dates, page_weights)):
            day_num = start_idx + i + 1
            days_from_start = (date - last_date).days
            weight_to_target = weight - target_weight
            
            predict_data.append({
                '预测天数': f"第{day_num}天",
                '日期': date.strftime('%Y-%m-%d'),
                '星期': date.strftime('%a'),
                '预测体重': f"{weight:.2f}kg",
                '距目标': f"{weight_to_target:+.2f}kg",
                '日目标量': f"{daily_target:.3f}kg"
            })
        
        predict_df = pd.DataFrame(predict_data)
        st.dataframe(predict_df, hide_index=True, use_container_width=True)
        
        if num_pages > 1:
            st.caption(f"第 {page}/{num_pages} 页，显示第 {start_idx+1}-{end_idx} 天预测")
        
        # 激励信息
        st.divider()
        
        if remaining > 0:
            if daily_target > 0:
                daily_calorie_deficit = daily_target * 7700  # 1kg脂肪≈7700大卡
                st.info(f"💡 **减重小贴士**：要达到每日减重{daily_target:.3f}kg的目标，您需要创造约**{daily_calorie_deficit:.0f}大卡**的热量缺口。")
                st.write("这相当于：")
                col_tip1, col_tip2 = st.columns(2)
                with col_tip1:
                    st.write("🏃 跑步60-90分钟")
                    st.write("🚴 骑行90-120分钟")
                with col_tip2:
                    st.write("🥗 减少一顿正餐")
                    st.write("🍎 用水果代替零食")
            
            # 随机鼓励语
            encouragements = [
                "💪 **坚持就是胜利**！每一小步都是进步，积累起来就是巨大的成功！",
                "🌟 **每天进步一点点**，一个月后您会感谢现在努力的自己！",
                "🌈 **健康减肥不在一时**，养成好习惯才是长久之计！",
                "🎯 **设定小目标**，完成一个就给自己一个小奖励！",
                "🚀 **您正在正确的道路上**，继续前进！"
            ]
            
            st.success(np.random.choice(encouragements))
        else:
            st.success("🎉 **恭喜您已达到目标体重**！请继续保持健康的生活习惯！")

# 页脚
st.divider()

# 显示数据状态
col_footer1, col_footer2, col_footer3 = st.columns([2, 2, 1])

with col_footer1:
    if not st.session_state.weight_data.empty:
        latest_date = st.session_state.weight_data['日期'].iloc[-1]
        if isinstance(latest_date, pd.Timestamp):
            latest_date = latest_date.strftime('%Y-%m-%d')
        latest_weight = st.session_state.weight_data['体重(kg)'].iloc[-1]
        st.caption(f"📅 最新记录：{latest_date} - {latest_weight:.1f}kg")

with col_footer2:
    if st.session_state.target_info:
        target = st.session_state.target_info.get('target_weight', 0)
        st.caption(f"🎯 目标体重：{target}kg")

with col_footer3:
    st.caption("⚖️ v2.1")

st.caption("体重管理助手 | 数据自动保存 | 程序编写：房星宇")
