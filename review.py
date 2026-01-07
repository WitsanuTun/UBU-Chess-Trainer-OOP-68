import chess


class GameReviewer:
    def __init__(self, engine_client):
        self.engine = engine_client

    def analyze_game(self, move_history):
        """
        :param move_history: list ของ chess.Move
        :return: list ของ dict ผลลัพธ์
        """
        if not self.engine:
            return []

        board = chess.Board()
        results = []

        # 1. เริ่มวิเคราะห์จากตำแหน่งแรก
        prev_eval = self._get_eval(board)

        for move in move_history:
            # 1.1 หา Best Move ของ Engine ในตานี้ (เพื่อเทียบ)
            best_info = self.engine.analyse_position(board, think_time=0.05)
            engine_best = best_info.get("best_move") if best_info else None

            # 1.2 เดินหมากจริงในกระดานจำลอง
            board.push(move)

            # 1.3 ประเมินคะแนนหลังเดิน
            curr_eval = self._get_eval(board)

            # 1.4 คำนวณความเสียหาย (Loss)
            # คะแนนเป็นมุมมองของ White เสมอ ต้องกลับด้านถ้าเป็นตาดำ
            # ถ้าเป็นตาดำ: (คะแนนเก่า - คะแนนใหม่) ถ้าเป็นบวกแปลว่าดีขึ้น
            if board.turn == chess.BLACK:  # ตาที่ผ่านมาคือ White
                diff = prev_eval - curr_eval
            else:  # ตาที่ผ่านมาคือ Black
                diff = curr_eval - prev_eval

            # 1.5 จำแนกประเภท
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
        info = self.engine.analyse_position(board, think_time=0.05)
        if not info: return 0
        mate = info.get("mate")
        cp = info.get("cp")
        if mate is not None:
            return 2000 if mate > 0 else -2000
        return cp if cp is not None else 0