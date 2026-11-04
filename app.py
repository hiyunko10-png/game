"""내신 로드맵 | 실행: streamlit run app.py

학기 평균만으로 실제 9등급제 성적을 복원할 수 없습니다.
이 앱은 공식 환산이 아닌 선형 비교 척도(2*x-1)를 사용합니다.
모든 학기의 비중은 동일하며, 목표는 9등급 참고 척도 기준입니다.
"""
from decimal import Decimal, ROUND_FLOOR
import html
import pandas as pd
import streamlit as st

SEMESTERS = ["1학년 1학기", "1학년 2학기", "2학년 1학기", "2학년 2학기", "3학년 1학기"]
MODES = {
    "페이스 유지": ("equal", "남은 학기마다 비슷한 목표로 꾸준하게."),
    "차근차근 상승": ("improve", "처음에는 여유 있게, 뒤로 갈수록 더 좋은 성적으로."),
    "초반 스퍼트": ("sprint", "초반에 집중하고, 뒤에는 조금 더 여유 있게."),
}


def to_cents(value):
    return int(Decimal(str(value)) * 100)


def convert_grade(value):
    """공식 환산이 아닌 선형 참고 척도. 결과는 0.01 단위 정수."""
    return 2 * to_cents(value) - 100


def required_budget(known, target):
    """최종 평균 <= 목표를 만족하는 남은 학기 합의 최댓값."""
    return int((Decimal(str(target)) * 500).to_integral_value(rounding=ROUND_FLOOR)) - sum(known)


def make_plan(total, n, mode):
    """정수 0.01 단위로 합계와 범위를 보존하는 학기 목표 생성.

    낮을수록 좋은 성적. improve는 비증가, sprint는 비감소.
    가능한 범위 안에서 인접 학기 격차를 약 0.8등급 이하로 제한.
    """
    if n == 0:
        return []
    if not 100 * n <= total <= 900 * n:
        raise ValueError("목표 합계가 유효 범위를 벗어났습니다.")
    base, remainder = divmod(total, n)
    values = [base] * (n - remainder) + [base + 1] * remainder
    if mode != "equal" and n > 1:
        headroom = min(min(values) - 100, 900 - max(values))
        step = min(40, headroom // (n - 1))
        values = [v + (2 * i - (n - 1)) * step for i, v in enumerate(values)]
    if mode == "improve":
        values.reverse()
    assert sum(values) == total and all(100 <= x <= 900 for x in values)
    return values


def main():
    st.set_page_config(page_title="내신 로드맵", page_icon="🎯", layout="centered")
    st.markdown("""<style>
    .stApp {background: #f5f7fc;}
    .block-container {max-width: 1020px; padding-top: 2rem;}
    .st-key-score_header {position: sticky; top: 3.75rem; z-index: 90;
      background: #ffffff; border: 1px solid #e1e6f0; border-radius: 20px;
      padding: 18px 22px; box-shadow: 0 8px 26px rgba(30,50,100,.08);}
    div[data-testid="stMetricValue"] {color: #3159cb;}
    .eyebrow {font-size: 12px; letter-spacing: .12em; color: #61708e; font-weight: 700;}
    @media(max-width: 640px) {
      .st-key-score_header {top: 3.5rem; padding: 12px;}
      div[data-testid="stMetricValue"] {font-size: 1.65rem;}
    }
    </style>""", unsafe_allow_html=True)
    header = st.container(key="score_header")
    st.title("🎯 내신 로드맵")
    st.write("지금의 성적에서 목표까지, 나에게 맞는 학기별 페이스를 찾아보세요.")
    st.warning("참고용 시뮬레이터입니다. 5등급제 학기 평균만으로 실제 9등급제 성적을 알 수 없습니다. 아래 수치는 공식 환산등급이나 대학 입시 산출점수가 아닙니다.")

    with st.expander("① 성적과 목표 입력", expanded=True):
        last = st.selectbox("성적이 나온 마지막 학기", ["아직 성적이 없어요"] + SEMESTERS, index=2,
                            help="선택한 학기까지만 입력합니다. 이후 학기의 과거 입력값은 계산에서 제외됩니다.")
        completed = 0 if last == "아직 성적이 없어요" else SEMESTERS.index(last) + 1
        known5 = []
        for i in range(completed):
            value = st.number_input(f"{SEMESTERS[i]} 평균 · 5등급제", min_value=1.0, max_value=5.0,
                                    value=2.5, step=0.01, format="%.2f", key=f"semester_{i}")
            known5.append(value)
        target = st.number_input("최종 목표 평균 · 9등급 참고 척도", min_value=1.0, max_value=9.0,
                                 value=3.0, step=0.01, format="%.2f",
                                 help="3학년 1학기까지 총 5개 학기의 평균입니다. 숫자가 작을수록 좋은 성적입니다.")
        st.caption(f"입력 완료 {completed}/5학기 · 남은 학기 {5-completed}개 · 모든 학기 동일 비중")

    known = [convert_grade(v) for v in known5]
    n = 5 - completed
    current = sum(known) / (100 * completed) if completed else None
    with header:
        st.markdown('<div class="eyebrow">MY GRADE · 현재 성적 요약</div>', unsafe_allow_html=True)
        a, b, c = st.columns(3)
        a.metric("현재 평균 · 9등급 참고값", f"{current:.2f}" if current is not None else "—")
        b.metric("최종 목표 · 9등급 참고값", f"{target:.2f}")
        c.metric("남은 학기", f"{n}개")
        st.caption("⚠️ 공식 환산 아님 · 선형 비교값 = 5등급 평균 × 2 − 1 · 숫자가 낮을수록 우수")

    with st.expander("계산 기준과 꼭 알아둘 점"):
        st.markdown("""
- **선형 참고 척도:** `9등급 참고값 = 2 × 5등급 평균 − 1`입니다. 1→1, 2→3, 3→5, 4→7, 5→9로 연결하는 앱 자체의 단순 비교 척도입니다.
- 두 등급제의 석차 비율은 다릅니다. 이 수식은 **석차 비율을 반영한 환산이 아니며**, 같은 평균이어도 실제 성적 분포에 따라 결과가 달라집니다.
- **목표는 9등급 참고 척도로 입력**합니다. 로드맵의 5등급 목표는 역산식 `(참고값+1)/2`로 함께 표시합니다.
- 1학년 1학기부터 3학년 1학기까지 **총 5학기를 동일 비중**으로 계산합니다. 과목별 학점, 대학별 반영비율, 성취도는 반영하지 않습니다.
- 필요한 남은 평균 = `(목표 × 5 − 완료 학기 참고값 합계) ÷ 남은 학기 수`.
- 학기별 목표는 **표시된 수치 이하**를 의미합니다. 목표 최종등급과 같거나 더 좋은 결과를 달성하도록 0.01단위로 배분합니다.
- 5등급 역산값은 소수 셋째 자리까지 표시합니다. 실제 학기 평균은 과목 구성에 따라 해당 수치를 정확히 만들 수 없을 수 있습니다.
- 상승·스퍼트 모드는 남은 학기 수와 1~9 범위 안에서 차이를 만듭니다. 경계에 가까우면 모드 간 차이가 줄거나 사라집니다.
""")
        st.caption("입시 판단에는 학교생활기록부와 지원 대학의 공식 모집요강을 확인하세요.")

    if completed:
        with st.expander("입력 성적 확인"):
            st.dataframe(pd.DataFrame({"학기": SEMESTERS[:completed],
                "입력 평균 · 5등급제": [f"{v:.2f}" for v in known5],
                "9등급 참고값": [f"{v/100:.2f}" for v in known]}), hide_index=True, use_container_width=True)

    if n == 0:
        st.subheader("🏁 다섯 학기 입력 완료")
        if sum(known) <= to_cents(target) * 5:
            st.success(f"최종 평균 참고값 {current:.2f} · 목표를 달성했어요!")
        else:
            st.info(f"최종 평균 참고값 {current:.2f} · 목표 {target:.2f}에는 도달하지 못했어요. 반영 기간의 남은 학기가 없어 새 로드맵은 만들 수 없습니다.")
        return

    budget = required_budget(known, target)
    best = (sum(known) + 100*n) / 500
    worst = (sum(known) + 900*n) / 500
    feasible = budget >= 100*n
    if not feasible:
        st.error(f"현재 입력과 계산 가정으로는 목표 {target:.2f} 달성이 불가능해요. 남은 학기 모두 1.00이어도 최종 참고값은 {best:.3f}입니다.")
        st.caption("아래는 목표 달성안이 아니라 가능한 최선의 계획입니다. 목표를 조정하면 세 가지 모드가 다시 계산됩니다.")
        total = 100*n
    else:
        total = min(budget, 900*n)
        need = budget / (100*n)
        if budget >= 900*n:
            st.success(f"목표 달성 여유가 있어요! 남은 학기 모두 9.00이어도 최종 {worst:.3f}로 목표 이내입니다.")
            st.caption("모든 학기를 최저 성적으로 보내라는 추천이 아니라, 현재 성적에 따른 수학적 여유를 뜻합니다.")
        else:
            st.success(f"목표 도전 가능! 남은 {n}학기의 평균 참고값을 {need:.3f} 이하로 맞추면 됩니다.")
        st.caption(f"남은 학기 성적에 따른 최종 평균 범위: {best:.3f} ~ {worst:.3f} · 9등급 참고 척도")

    st.subheader("🧭 나의 학기별 로드맵")
    st.caption("각 탭을 눌러 세 가지 전략을 비교하세요. 학기별 목표는 모두 해당 숫자 이하입니다.")
    tabs = st.tabs(list(MODES))
    for tab, (label, (mode, description)) in zip(tabs, MODES.items()):
        with tab:
            st.markdown(f"### {html.escape(label)}")
            st.write(description)
            plan = make_plan(total, n, mode)
            final = (sum(known) + sum(plan)) / 500
            x, y = st.columns(2)
            x.metric("계획대로 달성 시 · 최종 참고값", f"{final:.3f}")
            y.metric("남은 학기 목표 평균 · 참고값", f"{sum(plan)/(n*100):.3f}")
            if len(set(plan)) == 1 or n == 1:
                st.caption("남은 학기가 하나이거나 성적 범위의 경계에 있어 모드별 계획이 동일할 수 있습니다.")
            if not feasible:
                st.warning("목표 미달 · 달성 가능한 최선의 로드맵")
            frame = pd.DataFrame({
                "학기": SEMESTERS[completed:],
                "목표 · 9등급 참고값 이하": [f"{v/100:.2f}" for v in plan],
                "목표 · 5등급 평균 이하": [f"{(v+100)/200:.3f}" for v in plan],
            })
            st.dataframe(frame, hide_index=True, use_container_width=True)
            st.caption("예: 9등급 참고값 3.00 이하 ↔ 5등급 평균 2.000 이하. 실제 9등급 석차등급을 뜻하지 않습니다.")
            chart = pd.DataFrame({
                "입력 성적 · 참고값": [v/100 for v in known] + [None]*n,
                "남은 목표 · 참고값": [None]*completed + [v/100 for v in plan],
                "최종 목표 평균선": [target]*5,
            }, index=SEMESTERS)
            st.line_chart(chart, y_label="9등급 참고값 · 낮을수록 우수", use_container_width=True)
            st.caption("목표 평균선은 최종 평균의 기준선이며, 각 학기의 필수 성적선은 아닙니다.")
            st.download_button("이 모드의 로드맵 CSV 다운로드", data=frame.to_csv(index=False).encode("utf-8-sig"),
                               file_name=f"grade_roadmap_{mode}.csv", mime="text/csv", key=f"download_{mode}")
    st.divider()
    st.caption("입력값을 파일이나 외부 데이터베이스에 저장하지 않습니다. 새로고침하면 초기화될 수 있습니다. 공유 기기에서는 이용 후 탭을 닫아주세요.")


if __name__ == "__main__":
    main()
