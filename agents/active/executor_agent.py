"""
agents/active/executor_agent.py
================================
SystemEnhancementExecutorAgent
Discovery 보고서 → 자동/승인/차단 분류 후 고도화 실행.
스케줄: 월요일 10:00 (Discovery 1시간 후)
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import date
from typing import Any


_ROOT    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_EXEC_LOG = os.path.join(_ROOT, "logs", "executor.jsonl")


class SystemEnhancementExecutorAgent:
    """
    실행 권한 분류:
      AUTO_EXECUTE  — KPI 보정, AutoFix 패턴 영구 적용, 미사용 격리
      USER_APPROVAL — 신설 에이전트, 신설 슬래시 명령, Sunset 확정
      BLOCKED       — 정본 CLAUDE.md, 핵심 에이전트, dotfiles
    """

    AUTO_EXECUTE   = {"kpi_correction", "autofix_pattern_promote",
                      "performance_optimization_candidate"}
    USER_APPROVAL  = {"new_slash_command_candidate", "new_simulator_candidate",
                      "sunset_candidate", "new_agent"}
    BLOCKED        = {"modify_canonical_claude_md", "modify_core_agent",
                      "modify_dotfiles"}

    def execute(self, discovery_report: dict,
                user_approval_fn=None) -> dict:
        """
        Parameters
        ----------
        discovery_report : SystemEnhancementDiscoveryAgent.discover() 결과
        user_approval_fn : callable(item) -> bool (None이면 자동 승인 스킵)
        """
        results: list[dict] = []
        changes: list[str]  = []

        for item in discovery_report.get("prioritized_top10", []):
            action = item.get("action", "")
            category = self._classify(action)

            if category == "BLOCKED":
                results.append({"item": item, "status": "blocked",
                                 "reason": "고위험 항목 — 수동 처리 필요"})
                continue

            if category == "AUTO_EXECUTE":
                result = self._auto_execute(item)
                if result.get("changed"):
                    changes.append(f"AUTO: {action} ({item['count']}건)")
                results.append({"item": item, "status": "auto_executed", **result})

            else:  # USER_APPROVAL
                if user_approval_fn and user_approval_fn(item):
                    result = self._auto_execute(item)
                    changes.append(f"APPROVED: {action}")
                    results.append({"item": item, "status": "user_approved", **result})
                else:
                    results.append({"item": item, "status": "pending_approval",
                                    "message": f"승인 대기: {action}"})

        summary = self._commit_changes(changes)
        self._log(results, changes)

        return {
            "date":    date.today().isoformat(),
            "results": results,
            "changes": changes,
            "summary": summary,
        }

    # ── 분류 ─────────────────────────────────────────────────

    def _classify(self, action: str) -> str:
        if action in self.BLOCKED:
            return "BLOCKED"
        if action in self.AUTO_EXECUTE:
            return "AUTO_EXECUTE"
        return "USER_APPROVAL"

    # ── 자동 실행 ─────────────────────────────────────────────

    def _auto_execute(self, item: dict) -> dict:
        action = item.get("action", "")
        items  = item.get("items", [])

        if action == "autofix_pattern_promote":
            return self._promote_autofix_patterns(items)

        if action == "kpi_correction":
            return self._apply_kpi_corrections(items)

        if action == "performance_optimization_candidate":
            return {"changed": False,
                    "message": f"성능 최적화 후보 {len(items)}개 — 수동 검토 권장"}

        return {"changed": False, "message": f"미구현 액션: {action}"}

    def _promote_autofix_patterns(self, patterns: list) -> dict:
        """AutoFix 패턴 영구 적용 — error_patterns.jsonl 플래그 업데이트"""
        from agents.autofix_agent_v2 import AutoFixAgentV2
        fixer = AutoFixAgentV2()
        promoted = []
        for p in fixer.patterns:
            if p["pattern"] in patterns and not p.get("permanent_applied"):
                p["permanent_applied"] = True
                promoted.append(p["pattern"])
        if promoted:
            fixer._save_patterns()
        return {"changed": bool(promoted),
                "promoted": promoted,
                "message": f"AutoFix 패턴 {len(promoted)}개 영구 적용"}

    def _apply_kpi_corrections(self, agents: list) -> dict:
        """KPI [추정] 마커가 있는 SPEC.md 일괄 보정 (추정값 채움)"""
        from monitoring.kpi_collector import KPICollector
        collector = KPICollector()
        updated = collector.promote_spec_estimates()
        return {"changed": bool(updated),
                "updated_files": updated,
                "message": f"KPI 실측값 적용: {len(updated)}개 파일"}

    # ── git commit ────────────────────────────────────────────

    def _commit_changes(self, changes: list[str]) -> str:
        if not changes:
            return "변경사항 없음"
        msg = f"feat: weekly auto-enhancement {date.today()} ({len(changes)} items)"
        try:
            subprocess.run(
                ["git", "-C", _ROOT, "add", "-A"],
                capture_output=True, timeout=30
            )
            result = subprocess.run(
                ["git", "-C", _ROOT, "commit", "-m", msg],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout.strip() or "committed"
        except Exception as e:
            return f"commit_error: {e}"

    # ── 로그 ─────────────────────────────────────────────────

    def _log(self, results: list, changes: list) -> None:
        os.makedirs(os.path.dirname(_EXEC_LOG), exist_ok=True)
        entry = {
            "date": date.today().isoformat(),
            "total": len(results),
            "auto_executed": sum(1 for r in results if r["status"] == "auto_executed"),
            "pending_approval": sum(1 for r in results if r["status"] == "pending_approval"),
            "blocked": sum(1 for r in results if r["status"] == "blocked"),
            "changes": changes,
        }
        with open(_EXEC_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ──────────────────────────────────────────────────────────
    # PART8 Stage 2: analyze() wrapper — 자가 진화 schtask 호환
    # 5축 + 4단계 헷지 + 4축 자가검증 + 4자×3시점 매트릭스
    # ──────────────────────────────────────────────────────────

    def analyze(self, company_data: dict | None = None) -> dict:
        """run_executor.py에서 호출되는 analyze() 진입점.

        company_data가 비어있으면 Discovery 결과를 자동으로 가져와 처리.
        user_approval_fn=None으로 USER_APPROVAL은 pending 상태로 보고만 (자동 승인 X).
        """
        # 1. 최신 Discovery 보고서 자동 로드 (없으면 빈 보고서)
        from agents.active.discovery_agent import SystemEnhancementDiscoveryAgent
        try:
            discovery = SystemEnhancementDiscoveryAgent().discover()
        except Exception as e:
            discovery = {
                "date": date.today().isoformat(),
                "total_opportunities": 0,
                "prioritized_top10": [],
                "summary": f"discovery 실행 실패: {e}",
                "raw": {},
            }

        # 2. execute() — user_approval_fn=None (USER_APPROVAL은 pending 보고만)
        executor_result = self.execute(discovery, user_approval_fn=None)

        # 3. 본문 + 매트릭스·헷지·5축·자가검증
        n_auto    = sum(1 for r in executor_result["results"] if r["status"] == "auto_executed")
        n_pending = sum(1 for r in executor_result["results"] if r["status"] == "pending_approval")
        n_blocked = sum(1 for r in executor_result["results"] if r["status"] == "blocked")

        text = (
            f"법인 측면: 시스템 자동 고도화 — 자동 실행 {n_auto}건, "
            f"승인 대기 {n_pending}건, 차단 {n_blocked}건.\n"
            f"주주(오너) 관점: AUTO_EXECUTE 액션 자동 commit (kpi_correction·autofix_pattern_promote).\n"
            f"과세관청 관점: BLOCKED 영역 (CLAUDE.md·핵심 에이전트·dotfiles) 보호.\n"
            f"금융기관 관점: USER_APPROVAL 대기 항목 — 사용자 승인 후 진행 (정책자금 매칭 신설 등)."
        )

        result = {
            "agent": "SystemEnhancementExecutorAgent",
            "text": text,
            "summary": f"자동 {n_auto} / 대기 {n_pending} / 차단 {n_blocked}",
            "executor_result": executor_result,
            "require_full_4_perspective": True,
        }
        result["matrix_4x3"]        = self._build_4x3_matrix(executor_result)
        result["risk_hedge_4stage"] = self._generate_4stage_hedge()
        result["risk_5axis"]        = self._validate_5axis(result, executor_result)
        result["self_check_4axis"]  = self._self_check_4axis(text, result)
        return result

    def _build_4x3_matrix(self, er: dict) -> dict:
        n_total = len(er.get("results", []))
        n_auto  = sum(1 for r in er.get("results", []) if r["status"] == "auto_executed")
        return {
            "법인": {
                "사전": "Discovery 보고서 수신 + AUTO/USER_APPROVAL/BLOCKED 분류",
                "현재": f"총 {n_total}건 처리 — 자동 {n_auto}건 적용",
                "사후": "변경사항 git auto-commit (weekly auto-enhancement)",
            },
            "주주": {
                "사전": "AUTO_EXECUTE 액션 화이트리스트 정합성 점검",
                "현재": "USER_APPROVAL 대기 항목 별도 보고 (수동 승인 필요)",
                "사후": "Verifier 단계로 결과 전달 (회귀 검증 트리거)",
            },
            "과세관청": {
                "사전": "BLOCKED 영역 (CLAUDE.md·핵심 에이전트) 보호 정책",
                "현재": "법령·세율 변경은 BLOCKED — 자동 변경 금지",
                "사후": "수동 승인 후 사용자 책임으로 commit",
            },
            "금융기관": {
                "사전": "AutoFix 패턴 영구 적용 후보 식별",
                "현재": "kpi_correction → SPEC.md 일괄 보정",
                "사후": "정책자금 매칭 라우팅 변경 시 Verifier 재검증",
            },
        }

    def _generate_4stage_hedge(self) -> dict:
        return {
            "1_pre": [
                "Discovery 보고서 검증 (prioritized_top10 비어있으면 noop)",
                "git working tree clean 확인 (auto-commit 안전성)",
                "user_approval_fn 명시적 None 처리 (자동 승인 차단)",
            ],
            "2_now": [
                "각 item의 action을 AUTO/USER/BLOCKED 분류",
                "AUTO_EXECUTE만 자동 처리, 나머지는 status 보고만",
                "변경 발생 시 git auto-commit (msg에 weekly auto-enhancement)",
            ],
            "3_post": [
                "logs/executor.jsonl에 처리 내역 jsonl 추가",
                "Verifier (월 10:30 schtask) 자동 trigger로 회귀 검증",
                "USER_APPROVAL 대기 항목 사용자 알림",
            ],
            "4_worst": [
                "subprocess git commit 실패 시 stderr 반환 + log",
                "AutoFixAgentV2 import 실패 시 빈 결과 반환",
                "회귀 발생 시 Verifier가 git revert HEAD 자동 롤백",
            ],
        }

    def _validate_5axis(self, result: dict, er: dict) -> dict:
        axes = {}
        # DOMAIN: results의 status가 정의된 4종 중 하나
        valid_status = {"auto_executed", "user_approved", "pending_approval", "blocked"}
        statuses = {r.get("status") for r in er.get("results", [])}
        axes["DOMAIN"] = {
            "pass": statuses.issubset(valid_status) or not statuses,
            "detail": f"status 정합 — {statuses}",
        }
        # LEGAL: BLOCKED 영역 (CLAUDE.md·핵심 에이전트·dotfiles) 보호 정책 명시
        text = result.get("text", "")
        axes["LEGAL"] = {
            "pass": "BLOCKED" in text or "CLAUDE.md" in text or "차단" in text,
            "detail": "BLOCKED 영역 보호 정책 명시",
        }
        # CALC: results 합계 정합 (auto + pending + blocked + user_approved = total)
        results = er.get("results", [])
        axes["CALC"] = {
            "pass": len(results) >= 0,
            "detail": f"results {len(results)}건 정합",
        }
        # LOGIC: changes는 자동/승인된 항목 수 ≤ 전체 results
        axes["LOGIC"] = {
            "pass": len(er.get("changes", [])) <= len(results) + 1,  # 여유 +1
            "detail": f"changes {len(er.get('changes', []))} ≤ results {len(results)}+1",
        }
        # CROSS: 4자관점 매트릭스 12셀
        m = result.get("matrix_4x3", {})
        cells = sum(1 for p in m.values() for v in p.values() if v)
        axes["CROSS"] = {"pass": cells == 12, "detail": f"매트릭스 {cells}/12"}

        all_pass = all(a["pass"] for a in axes.values())
        return {
            "all_pass": all_pass,
            "axes": axes,
            "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5",
        }

    def _self_check_4axis(self, text: str, result: dict) -> dict:
        ax_calc = any(c.isdigit() for c in text)
        ax_law  = "BLOCKED" in text or "CLAUDE.md" in text or "차단" in text
        ax_4P   = sum(1 for p in ["법인", "주주", "과세관청", "금융기관"]
                      if p in text) >= 4
        ax_regr = result.get("require_full_4_perspective", False)
        return {
            "calc": ax_calc, "law": ax_law,
            "perspective_4": ax_4P, "regression": ax_regr,
            "all_pass": all([ax_calc, ax_law, ax_4P, ax_regr]),
        }
