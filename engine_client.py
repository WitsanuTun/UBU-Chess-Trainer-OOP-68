import os
import chess
import chess.engine
from pathlib import Path


class EngineClient:
    def __init__(self, engine_path=None, elo=1200, think_time=0.2):
        if engine_path is None:
            # Auto-detect engine path
            base_dir = Path(__file__).resolve().parent
            engine_path = base_dir / "engine/stockfish/stockfish.exe"

        self.engine_path = str(engine_path)
        self.think_time = float(think_time)
        self.elo = elo

        self._engine = None
        self._opened = False

        self.open()
        # เรียก set_elo ทันทีหลังจากเปิด
        self.set_elo(elo)

    def open(self):
        if self._opened:
            return

        if not os.path.exists(self.engine_path):
            raise FileNotFoundError(f"Engine not found at: {self.engine_path}")

        try:
            self._engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            self._opened = True
            # ไม่เรียก _apply_elo_to_engine() ที่นี่ รอให้ __init__ เรียก set_elo เอง
        except Exception as e:
            print(f"Failed to start engine: {e}")

    def close(self):
        if self._opened and self._engine:
            try:
                self._engine.quit()
            except:
                pass
        self._engine = None
        self._opened = False

    def set_elo(self, elo):
        # รับค่าดิบมาก่อน
        self.elo = int(elo)
        if self._opened:
            self._apply_elo_to_engine()

    def _apply_elo_to_engine(self):
        if not self._engine: return

        options = self._engine.options
        config = {}

        # Option 1: UCI_LimitStrength (Standard for Stockfish 11+)
        if "UCI_LimitStrength" in options and "UCI_Elo" in options:
            # [FIXED] ดึงค่า Min/Max จริงจาก Engine มาเช็คก่อน
            min_elo = options["UCI_Elo"].min
            max_elo = options["UCI_Elo"].max

            # บังคับค่าให้อยู่ในช่วงที่ Engine รับได้ (Clamp)
            # ถ้าขอ 1200 แต่ Engine รับต่ำสุด 1320 -> มันจะส่ง 1320 ไปแทน
            target_elo = max(min_elo, min(self.elo, max_elo))

            config["UCI_LimitStrength"] = True
            config["UCI_Elo"] = target_elo

        # Option 2: Skill Level (Older Stockfish)
        elif "Skill Level" in options:
            # Map ELO 100-3200 to Skill Level 0-20
            skill = int((self.elo - 100) / (3200 - 100) * 20)
            config["Skill Level"] = max(0, min(20, skill))

        if config:
            try:
                self._engine.configure(config)
            except Exception as e:
                print(f"Warning: Could not configure engine Elo: {e}")

    def choose_move(self, board):
        if not self._opened: self.open()
        if board.is_game_over(): return None

        limit = chess.engine.Limit(time=self.think_time)
        try:
            result = self._engine.play(board, limit)
            return result.move
        except chess.engine.EngineTerminatedError:
            # Retry once if engine crashed
            self.close()
            self.open()
            return self._engine.play(board, limit).move
        except:
            return None

    def analyse_position(self, board, think_time=None):
        if not self._opened: self.open()

        limit = chess.engine.Limit(time=think_time or self.think_time)
        try:
            info = self._engine.analyse(board, limit, info=chess.engine.INFO_ALL)
        except chess.engine.EngineTerminatedError:
            self.close()
            self.open()
            try:
                info = self._engine.analyse(board, limit, info=chess.engine.INFO_ALL)
            except:
                return None

        # Extract Score
        score_obj = info["score"].pov(chess.WHITE)
        mate = score_obj.mate()
        cp = score_obj.score() if mate is None else None

        # Extract Best Move
        pv = info.get("pv", [])
        best_move = pv[0] if pv else None

        return {
            "cp": cp,
            "mate": mate,
            "best_move": best_move
        }

    def __del__(self):
        self.close()