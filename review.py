import chess

class GameReviewer:
    def __init__(self, engine_client):
        self.engine = engine_client

    def analyze_game(self, move_history):
        if not self.engine:
            return []

        board = chess.Board()
        results = []

        # เริ่มต้นประเมินคะแนนจากกระดานว่าง
        prev_eval = self._get_eval(board)

        for move in move_history:
            # 1. หา Best Move ของ Engine ในตานั้นๆ
            best_info = self.engine.analyse_position(board, think_time=0.05)
            engine_best = best_info.get("best_move") if best_info else None

            # 2. จำลองการเดินหมาก
            board.push(move)
            curr_eval = self._get_eval(board)

            # 3. คำนวณความเสียหาย (Loss) โดยเทียบกับคะแนนก่อนเดิน
            # คะแนนเป็นมุมมองของ White เสมอ
            if board.turn == chess.BLACK:  # ตาที่ผ่านมาคือ White เดิน
                diff = prev_eval - curr_eval
            else:  # ตาที่ผ่านมาคือ Black เดิน
                diff = curr_eval - prev_eval

            # 4. จำแนกประเภทตาเดิน (Move Classification)
            move_class = "book"
            if move == engine_best:
                move_class = "best"
            elif diff <= 20:
                move_class = "excellent"
            elif diff <= 50:
                move_class = "good"
            elif diff <= 100:
                move_class = "inaccuracy"
            elif diff <= 300:
                move_class = "mistake"
            else:
                move_class = "blunder"

            results.append({
                "move": move,
                "class": move_class,
                "score": curr_eval
            })

            prev_eval = curr_eval

        return results

    def _get_eval(self, board):
        """Helper function เพื่อดึงคะแนน CP หรือ Mate"""
        info = self.engine.analyse_position(board, think_time=0.05)
        if not info: return 0

        mate = info.get("mate")
        cp = info.get("cp")

        if mate is not None:
            return 2000 if mate > 0 else -2000
        return cp if cp is not None else 0