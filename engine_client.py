# engine_client.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import chess
import chess.engine


class EngineClient:
    """
    ตัวห่อ Stockfish แบบง่าย ๆ

    ใช้ได้ 3 อย่างหลัก ๆ
    - set_elo(): ตั้งระดับความเก่ง (map ไปเป็น UCI_Elo / Skill Level)
    - choose_move(): ให้คอมเดิน 1 ท่า
    - analyse_position(): ให้คอมประเมินตำแหน่งปัจจุบัน (eval bar / best move)
    """

    def __init__(
        self,
        engine_path: Optional[str] = None,
        elo: int = 1200,
        think_time: float = 0.2,
    ) -> None:
        # หา path engine เองถ้าไม่ได้ส่งมา
        if engine_path is None:
            base_dir = Path(__file__).resolve().parent
            engine_path = base_dir / "engine/stockfish/stockfish.exe"

        self.engine_path = str(engine_path)
        self.think_time = float(think_time)

        self._engine: Optional[chess.engine.SimpleEngine] = None
        self._opened = False

        self.elo = 1200
        self.set_elo(elo)

        self.open()

    # ------------------------------------------------------------------
    #  เปิด / ปิด engine
    # ------------------------------------------------------------------
    def open(self) -> None:
        if self._opened:
            return

        if not os.path.exists(self.engine_path):
            raise FileNotFoundError(
                f"ไม่พบ engine ที่ {self.engine_path} "
                f"(อย่าลืมแตกไฟล์ stockfish แล้วชี้ path ให้ถูก)"
            )

        self._engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        self._opened = True
        self._apply_elo_to_engine()

    def close(self) -> None:
        if self._opened and self._engine is not None:
            try:
                self._engine.quit()
            except Exception:
                pass
        self._engine = None
        self._opened = False

    def __del__(self) -> None:
        self.close()

    # ------------------------------------------------------------------
    #  การตั้งค่า ELO / think_time
    # ------------------------------------------------------------------
    def set_think_time(self, seconds: float) -> None:
        self.think_time = max(0.01, float(seconds))

    def set_elo(self, elo: int) -> None:
        elo = int(elo)
        elo = max(100, min(elo, 3200))
        self.elo = elo

        if self._opened and self._engine is not None:
            self._apply_elo_to_engine()

    def _apply_elo_to_engine(self) -> None:
        if not self._opened or self._engine is None:
            return

        info = self._engine.options
        updates = {}

        # 1) UCI_Elo / UCI_LimitStrength ถ้ามี
        if "UCI_LimitStrength" in info and "UCI_Elo" in info:
            min_elo = info["UCI_Elo"].min
            max_elo = info["UCI_Elo"].max
            target_elo = max(min_elo, min(max_elo, self.elo))

            updates["UCI_LimitStrength"] = True
            updates["UCI_Elo"] = target_elo

        # 2) Skill Level 0–20 (บางเวอร์ชันของ stockfish มี)
        if "Skill Level" in info:
            elo_min, elo_max = 100, 3200
            ratio = (self.elo - elo_min) / (elo_max - elo_min)
            skill = int(round(ratio * 20))
            skill = max(0, min(20, skill))
            updates["Skill Level"] = skill

        if updates:
            self._engine.configure(updates)

    # ------------------------------------------------------------------
    #  ให้คอมเดิน (เล่นกับ engine)
    # ------------------------------------------------------------------
    def choose_move(self, board: chess.Board) -> Optional[chess.Move]:
        """
        ให้ engine คิดแล้วคืน move 1 ท่า
        ถ้าเดินไม่ได้ (เช่น เมต/ตัน) คืน None
        """
        if not self._opened or self._engine is None:
            self.open()

        if board.is_game_over():
            return None

        limit = chess.engine.Limit(time=self.think_time)

        try:
            result = self._engine.play(board, limit)
        except chess.engine.EngineTerminatedError:
            self.close()
            self.open()
            result = self._engine.play(board, limit)

        return result.move

    # ------------------------------------------------------------------
    #  วิเคราะห์ตำแหน่ง (ใช้กับ Review mode / eval bar)
    # ------------------------------------------------------------------
    def analyse_position(
        self,
        board: chess.Board,
        think_time: Optional[float] = None,
    ) -> Optional[dict]:
        """
        วิเคราะห์ตำแหน่งบนกระดาน แล้วคืน dict:

        {
            "cp":   int | None   # centipawn จากมุมมองฝั่งขาว
            "mate": int | None   # mate in N (ถ้าเป็น mate)
            "best_move": chess.Move | None
        }
        """
        if think_time is None:
            think_time = self.think_time

        if not self._opened or self._engine is None:
            self.open()

        limit = chess.engine.Limit(time=think_time)

        try:
            info = self._engine.analyse(board, limit, info=chess.engine.INFO_ALL)
        except chess.engine.EngineTerminatedError:
            self.close()
            self.open()
            info = self._engine.analyse(board, limit, info=chess.engine.INFO_ALL)

        score_obj = info["score"].pov(chess.WHITE)
        mate = score_obj.mate()
        cp = None if mate is not None else score_obj.score()

        pv = info.get("pv", [])
        best_move = pv[0] if pv else None

        return {
            "cp": cp,
            "mate": mate,
            "best_move": best_move,
        }
