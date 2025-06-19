import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import sqlite3
import debugpy
import sys
import os

# 调试入口（仅在独立Streamlit环境中启用调试器）
is_streamlit_env = getattr(st, '_is_running_with_streamlit', False)
is_pycharm_debug = 'pydevd' in sys.modules

# 调试配置（仅在独立Streamlit环境且非PyCharm调试模式下生效）
if is_streamlit_env and not is_pycharm_debug:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("调试器已启动，等待连接...")

# 初始化全局设置
st.set_page_config(page_title="网格长能力画像系统", layout="wide")
st.title("乡镇网格长绩效与能力画像评估系统")

# 数据库文件路径
DB_FILE = 'grid_leaders.db'

# 数据库连接与初始化
def init_database():
    """初始化SQLite数据库并创建表结构"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 创建网格长表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grid_leaders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        area TEXT NOT NULL
    )
    ''')

    # 创建评估记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        leader_id INTEGER,
        date TEXT NOT NULL,
        professional_skill INTEGER,
        index_mastery INTEGER,
        management_execution INTEGER,
        communication_coordination INTEGER,
        marketing_ability INTEGER,
        FOREIGN KEY (leader_id) REFERENCES grid_leaders (id)
    )
    ''')

    # 创建能力提升计划表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS improvement_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        leader_id INTEGER,
        dimension TEXT NOT NULL,
        target_score INTEGER,
        FOREIGN KEY (leader_id) REFERENCES grid_leaders (id)
    )
    ''')

    conn.commit()
    conn.close()


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# 初始化数据库
init_database()


# 数据库操作函数
def get_all_leaders():
    """获取所有网格长"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM grid_leaders')
    leaders = cursor.fetchall()
    conn.close()
    return leaders


def get_leader_by_name(name):
    """根据姓名获取网格长"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM grid_leaders WHERE name =?', (name,))
    leader = cursor.fetchone()
    conn.close()
    return leader


def get_leader_assessments(leader_id):
    """获取网格长的所有评估记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM assessments WHERE leader_id =? ORDER BY date DESC',
        (leader_id,)
    )
    assessments = cursor.fetchall()
    conn.close()
    return assessments


def add_leader(name, area):
    """添加新网格长"""
    # 验证姓名和辖区是否为空
    if not name or not area:
        st.error("姓名和辖区不能为空，请重新输入。")
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO grid_leaders (name, area) VALUES (?,?)', (name, area))
    conn.commit()
    conn.close()


def add_assessment(leader_id, date, scores):
    """添加评估记录"""
    # 验证分数是否在 0 到 100 之间
    for score in scores.values():
        if score < 0 or score > 100:
            st.error("分数必须在 0 到 100 之间，请重新输入。")
            return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO assessments (leader_id, date, professional_skill, index_mastery, 
                   management_execution, communication_coordination, marketing_ability) 
                   VALUES (?,?,?,?,?,?,?)''',
        (leader_id, date, scores["专业技术能力"], scores["指标掌控能力"],
         scores["管理执行能力"], scores["沟通协调能力"], scores["市场营销能力"])
    )
    conn.commit()
    conn.close()


def update_assessment(assessment_id, scores):
    """修改评估记录"""
    # 验证分数是否在 0 到 100 之间
    for score in scores.values():
        if score < 0 or score > 100:
            st.error("分数必须在 0 到 100 之间，请重新输入。")
            return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''UPDATE assessments 
           SET professional_skill = ?, index_mastery = ?, 
               management_execution = ?, communication_coordination = ?, marketing_ability = ?
           WHERE id = ?''',
        (scores["专业技术能力"], scores["指标掌控能力"],
         scores["管理执行能力"], scores["沟通协调能力"], scores["市场营销能力"], assessment_id)
    )
    conn.commit()
    conn.close()


def save_improvement_plan(leader_id, dimension, target_score):
    """保存能力提升计划"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO improvement_plans (leader_id, dimension, target_score) VALUES (?,?,?)',
        (leader_id, dimension, target_score)
    )
    conn.commit()
    conn.close()


# 初始化示例数据
def init_sample_data():
    """初始化示例数据到数据库"""
    # 检查是否已有数据
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM grid_leaders')
    leaders_count = cursor.fetchone()[0]
    conn.close()

    if leaders_count == 0:
        # 添加示例网格长
        add_leader("张明", "东风社区")
        add_leader("李红", "河西社区")

        # 获取网格长ID
        leader1 = get_leader_by_name("张明")
        leader2 = get_leader_by_name("李红")

        # 添加评估记录
        add_assessment(leader1["id"], "2023-09-30", {
            "专业技术能力": 82, "指标掌控能力": 76,
            "管理执行能力": 85, "沟通协调能力": 79,
            "市场营销能力": 68
        })

        add_assessment(leader2["id"], "2023-09-30", {
            "专业技术能力": 88, "指标掌控能力": 92,
            "管理执行能力": 75, "沟通协调能力": 85,
            "市场营销能力": 78
        })


# 初始化示例数据
init_sample_data()

# 能力维度配置
DIMENSIONS = [
    "专业技术能力", "指标掌控能力",
    "管理执行能力", "沟通协调能力",
    "市场营销能力"
]

WEIGHTS = {
    "专业技术能力": 0.25,
    "指标掌控能力": 0.25,
    "管理执行能力": 0.20,
    "沟通协调能力": 0.20,
    "市场营销能力": 0.10
}

THRESHOLDS = {
    "优秀": 90,
    "良好": 80,
    "合格": 70,
    "待改进": 60
}

# 改进建议库
IMPROVEMENT_TIPS = {
    "专业技术能力": [
        "参加政策法规专题培训（每月至少1次）",
        "每日学习'政策一点通'平台更新内容",
        "建立个人业务知识库，记录疑难问题解决方案",
        "向业务骨干请教典型案例处理方法"
    ],
    "指标掌控能力": [
        "使用指标跟踪表每日监控关键数据",
        "每周分析指标波动原因并制定对策",
        "优先处理高权重指标相关任务",
        "学习基础数据分析方法（Excel/PowerBI）"
    ],
    "管理执行能力": [
        "使用甘特图进行任务分解和时间管理",
        "建立每日工作清单并设置优先级",
        "实施'PDCA'循环改进工作流程",
        "每周召开15分钟网格员站会同步进展"
    ],
    "沟通协调能力": [
        "主动走访关键居民（每周5户以上）",
        "学习'非暴力沟通'技巧并实践",
        "建立跨部门联系人清单定期维护关系",
        "重要沟通前准备提纲和解决方案草案"
    ],
    "市场营销能力": [
        "设计社区活动宣传方案（图文+短视频）",
        "挖掘辖区资源建立合作名录",
        "在居民群定期推送服务信息（每周3次）",
        "组织'网格开放日'提升居民参与度"
    ]
}

# 界面布局
with st.sidebar:
    st.header("网格长管理")
    leaders = get_all_leaders()
    leader_names = [leader["name"] for leader in leaders]
    search_term = st.text_input("搜索网格长")
    if search_term:
        leader_names = [name for name in leader_names if search_term.lower() in name.lower()]
    selected_name = st.selectbox(
        "选择网格长",
        options=leader_names
    )

    # 获取当前选中网格长
    current_leader = get_leader_by_name(selected_name)
    if current_leader is None:
        st.error("未找到该网格长，请检查输入。")
        st.stop()
    leader_id = current_leader["id"]

    st.divider()
    st.subheader("添加新评估")
    assessment_date = st.date_input("评估日期", datetime.today())
    new_scores = {}
    for dim in DIMENSIONS:
        new_scores[dim] = st.slider(
            f"{dim}得分",
            min_value=0, max_value=100, value=80
        )

    if st.button("提交评估"):
        add_assessment(
            leader_id,
            str(assessment_date),
            new_scores
        )
        st.success(f"{selected_name}的评估数据已更新！")

    st.divider()
    st.subheader("修改评估数据")
    assessments = get_leader_assessments(leader_id)
    if assessments:
        assessment_dates = [assessment["date"] for assessment in assessments]
        selected_date = st.selectbox("选择评估日期", assessment_dates)
        selected_assessment = next((a for a in assessments if a["date"] == selected_date), None)
        if selected_assessment:
            edit_scores = {}
            # 映射中文维度名称到数据库列名
            dim_to_db_col = {
                "专业技术能力": "professional_skill",
                "指标掌控能力": "index_mastery",
                "管理执行能力": "management_execution",
                "沟通协调能力": "communication_coordination",
                "市场营销能力": "marketing_ability"
            }
            for dim in DIMENSIONS:
                # 使用正确的列名从数据库记录中获取值
                db_col_name = dim_to_db_col[dim]
                edit_scores[dim] = st.slider(
                    f"{dim}得分",
                    min_value=0, max_value=100,
                    value=selected_assessment[db_col_name],
                    key=f"edit_{dim}"
                )
            if st.button("保存修改"):
                update_assessment(selected_assessment["id"], edit_scores)
                st.success(f"{selected_name}在{selected_date}的评估数据已更新！")

    st.divider()
    st.subheader("导入Excel数据")
    uploaded_file = st.file_uploader("选择Excel文件", type=["xlsx", "xls","csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            for index, row in df.iterrows():
                name = row["姓名"]
                area = row["辖区"]
                date = str(row["评估日期"])
                scores = {
                    "专业技术能力": row["专业技术能力"],
                    "指标掌控能力": row["指标掌控能力"],
                    "管理执行能力": row["管理执行能力"],
                    "沟通协调能力": row["沟通协调能力"],
                    "市场营销能力": row["市场营销能力"]
                }
                leader = get_leader_by_name(name)
                if leader is None:
                    add_leader(name, area)
                    leader = get_leader_by_name(name)
                add_assessment(leader["id"], date, scores)
            st.success("数据导入成功！")
        except Exception as e:
            st.error(f"数据导入失败: {e}")
def read_excel_file(file_path):
    """读取Excel文件，自动处理格式问题"""
    try:
        # 尝试使用openpyxl读取.xlsx文件
        df = pd.read_excel(file_path, engine='openpyxl')
        print("成功使用openpyxl读取文件")
        return df
    except Exception as e:
        print(f"使用openpyxl失败: {e}")
        try:
            # 尝试使用xlrd读取.xls文件
            df = pd.read_excel(file_path, engine='xlrd')
            print("成功使用xlrd读取文件")
            return df
        except Exception as e2:
            print(f"使用xlrd失败: {e2}")
            print("请检查文件格式或路径是否正确")
            return None

# 使用示例
file_path = 'your_data.xlsx'
df = read_excel_file(file_path)

if df is not None:
    print(f"数据基本信息：")
    df.info()


# 主显示区
assessments = get_leader_assessments(leader_id)
current_scores = None

if assessments:
    current_scores = {
        "专业技术能力": assessments[0]["professional_skill"],
        "指标掌控能力": assessments[0]["index_mastery"],
        "管理执行能力": assessments[0]["management_execution"],
        "沟通协调能力": assessments[0]["communication_coordination"],
        "市场营销能力": assessments[0]["marketing_ability"],
        "date": assessments[0]["date"]
    }

if current_scores:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader(f"{current_leader['name']} - {current_leader['area']}")

        # 计算综合得分
        total_score = sum(
            current_scores[dim] * WEIGHTS[dim]
            for dim in DIMENSIONS
        )

        # 综合得分展示
        score_color = (
            "green" if total_score >= 85
            else "orange" if total_score >= 75
            else "red"
        )
        st.markdown(f"""
        <div style="text-align:center; padding:20px; border-radius:10px; background:#f0f2f6">
            <h3>综合能力得分</h3>
            <h1 style="color:{score_color}">{total_score:.1f}<span style="font-size:20px">/100</span></h1>
            <p>{'优秀' if total_score >= 85 else '良好' if total_score >= 75 else '待提升'}</p>
        </div>
        """, unsafe_allow_html=True)

        # 能力等级分布
        st.subheader("能力等级分布")
        level_counts = {"优秀": 0, "良好": 0, "合格": 0, "待改进": 0}
        for dim in DIMENSIONS:
            score = current_scores[dim]
            if score >= THRESHOLDS["优秀"]:
                level_counts["优秀"] += 1
            elif score >= THRESHOLDS["良好"]:
                level_counts["良好"] += 1
            elif score >= THRESHOLDS["合格"]:
                level_counts["合格"] += 1
            else:
                level_counts["待改进"] += 1

        level_df = pd.DataFrame({
            "等级": level_counts.keys(),
            "数量": level_counts.values()
        })
        st.bar_chart(level_df.set_index("等级"))

    with col2:
        # 雷达图展示
        st.subheader("能力维度分析")
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[current_scores[dim] for dim in DIMENSIONS],
            theta=DIMENSIONS,
            fill='toself',
            name='当前能力值'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # 短板分析
        st.subheader("短板分析与改进建议")
        weaknesses = sorted(
            [(dim, current_scores[dim]) for dim in DIMENSIONS],
            key=lambda x: x[1]
        )[:2]  # 取最弱的2项

        for dim, score in weaknesses:
            with st.expander(f"{dim} ({score}分) 改进建议"):
                st.warning(f"当前能力值低于{'优秀' if score < 90 else '良好' if score < 80 else '合格'}水平")

                # 显示改进建议
                for i, tip in enumerate(IMPROVEMENT_TIPS[dim][:3]):
                    st.markdown(f"{i + 1}. {tip}")

                # 进度跟踪
                st.progress(score / 100, f"能力提升进度 ({score}→{min(100, score + 15)})")

                # 设置提升目标
                target = st.slider(
                    f"{dim}提升目标",
                    min_value=score, max_value=100,
                    value=min(100, score + 15), key=dim
                )
                if st.button(f"保存{dim}提升目标"):
                    save_improvement_plan(leader_id, dim, target)
                    st.success(f"{dim}提升目标已保存！")

# 历史趋势分析
st.divider()
st.subheader("能力发展轨迹")
if len(assessments) > 1:
    history_data = []
    for assessment in assessments:
        # 修改这里，使用正确的列名
        score_dict = {
            "date": assessment["date"],
            "专业技术能力": assessment["professional_skill"],
            "指标掌控能力": assessment["index_mastery"],
            "管理执行能力": assessment["management_execution"],
            "沟通协调能力": assessment["communication_coordination"],
            "市场营销能力": assessment["marketing_ability"],
        }
        score_dict["综合得分"] = sum(
            score_dict[dim] * WEIGHTS[dim]
            for dim in DIMENSIONS
        )
        history_data.append(score_dict)

    history_df = pd.DataFrame(history_data)
    history_df = history_df.set_index("date")

    # 趋势图
    tab1, tab2 = st.tabs(["维度趋势", "综合趋势"])
    with tab1:
        selected_dims = st.multiselect(
            "选择观察维度",
            DIMENSIONS, default=DIMENSIONS[:2]
        )
        st.line_chart(history_df[selected_dims])

    with tab2:
        st.line_chart(history_df["综合得分"])
else:
    st.info("至少需要2次评估数据才能显示趋势分析")

# 数据管理功能
st.sidebar.divider()
st.sidebar.subheader("数据管理")
if st.sidebar.button("导出当前数据 (CSV)"):
    # 从数据库获取所有数据
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            gl.name as "姓名", 
            gl.area as "辖区", 
            a.date as "评估日期",
            a.professional_skill as "专业技术能力",
            a.index_mastery as "指标掌控能力",
            a.management_execution as "管理执行能力",
            a.communication_coordination as "沟通协调能力",
            a.marketing_ability as "市场营销能力"
        FROM grid_leaders gl
        JOIN assessments a ON gl.id = a.leader_id
    ''')
    data = cursor.fetchall()
    conn.close()

    df = pd.DataFrame([dict(row) for row in data])
    if not df.empty:
        # 计算综合得分
        df["综合得分"] = df.apply(lambda row: sum(
            row[dim] * WEIGHTS[dim] for dim in DIMENSIONS
        ), axis=1)

        st.sidebar.download_button(
            label="下载CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="网格长评估数据.csv",
            mime="text/csv"
        )

if st.sidebar.button("重置示例数据"):
    # 清空数据库
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM assessments')
    cursor.execute('DELETE FROM grid_leaders')
    cursor.execute('DELETE FROM improvement_plans')
    conn.commit()
    conn.close()

    # 重新初始化示例数据
    init_sample_data()
    st.rerun()


# 团队对比分析
def compare_leaders():
    fig = go.Figure()
    leaders = get_all_leaders()
    for leader in leaders:
        assessments = get_leader_assessments(leader["id"])
        if assessments:
            current_scores = {
                "专业技术能力": assessments[0]["professional_skill"],
                "指标掌控能力": assessments[0]["index_mastery"],
                "管理执行能力": assessments[0]["management_execution"],
                "沟通协调能力": assessments[0]["communication_coordination"],
                "市场营销能力": assessments[0]["marketing_ability"]
            }
            fig.add_trace(go.Scatterpolar(
                r=[current_scores[dim] for dim in DIMENSIONS],
                theta=DIMENSIONS,
                fill='toself',
                name=leader["name"]
            ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="不同网格长的对比雷达图"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 柱状图对比综合得分
    leader_scores = []
    for leader in leaders:
        assessments = get_leader_assessments(leader["id"])
        if assessments:
            current_scores = {
                "专业技术能力": assessments[0]["professional_skill"],
                "指标掌控能力": assessments[0]["index_mastery"],
                "管理执行能力": assessments[0]["management_execution"],
                "沟通协调能力": assessments[0]["communication_coordination"],
                "市场营销能力": assessments[0]["marketing_ability"]
            }
            total_score = sum(
                current_scores[dim] * WEIGHTS[dim]
                for dim in DIMENSIONS
            )
            leader_scores.append({
                "name": leader["name"],
                "score": total_score
            })
    score_df = pd.DataFrame(leader_scores)
    fig_bar = px.bar(score_df, x="name", y="score", title="不同网格长综合得分对比")
    st.plotly_chart(fig_bar, use_container_width=True)


# 智能诊断报告
def generate_report():
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # 报告标题
    p.setFont('Helvetica-Bold', 20)
    p.drawString(100, 750, '乡镇网格长绩效与能力画像评估报告')
    p.setFont('Helvetica', 12)

    y_position = 700
    leaders = get_all_leaders()
    for leader in leaders:
        assessments = get_leader_assessments(leader["id"])
        if assessments:
            current_scores = assessments[0]
            p.drawString(100, y_position, f"网格长: {leader['name']} - {leader['area']}")
            y_position -= 20

            # 映射数据库列名到中文维度名称
            score_mapping = {
                "专业技术能力": current_scores["professional_skill"],
                "指标掌控能力": current_scores["index_mastery"],
                "管理执行能力": current_scores["management_execution"],
                "沟通协调能力": current_scores["communication_coordination"],
                "市场营销能力": current_scores["marketing_ability"]
            }

            # 计算综合得分
            total_score = sum(
                score_mapping[dim] * WEIGHTS[dim]
                for dim in DIMENSIONS
            )
            p.drawString(100, y_position, f"综合得分: {total_score:.1f}")
            y_position -= 20

            for dim in DIMENSIONS:
                p.drawString(100, y_position, f"{dim}: {score_mapping[dim]}分")
                y_position -= 20
            y_position -= 30

    p.save()
    buffer.seek(0)
    st.download_button(
        label="下载PDF评估报告",
        data=buffer,
        file_name="评估报告.pdf",
        mime="application/pdf"
    )


# 移动端适配
st.write("""
<style>
@media (max-width: 600px) {
    /* 调整侧边栏宽度 */
    [data-testid="stSidebar"] {
        width: 100% !important;
    }
    /* 调整列布局 */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column;
    }
    /* 调整图表大小 */
    [data-testid="stPlotlyChart"] {
        width: 100% !important;
    }
}
</style>
""", unsafe_allow_html=True)

# 添加功能按钮
if st.button("团队对比分析"):
    compare_leaders()

if st.button("生成智能诊断报告"):
    generate_report()
