import chess
import chess.engine

# ถ้าไฟล์อยู่ที่ engine/stockfish/stockfish.exe ใช้ path แบบนี้
ENGINE_PATH = r"engine/stockfish/stockfish.exe"

def main():
    # สร้างกระดานเริ่มเกม
    board = chess.Board()

    # เปิดเอนจิน
    engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

    # ให้ Stockfish วิเคราะห์ตำแหน่งเริ่มเกม
    info = engine.analyse(board, chess.engine.Limit(depth=10))
    score = info["score"].pov(chess.WHITE).score(mate_score=10000)

    print("Engine run OK ✅")
    print("Evaluation from start position:", score, "centipawns")

    engine.quit()

if __name__ == "__main__":
    main()
