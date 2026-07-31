import cv2, os, sys, io,time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess

# exe化の際、noconsoleでエラーになるのを回避するために必要
buffer = io.StringIO()
sys.stdout = buffer
sys.stderr = buffer

# Tkinterウィンドウの作成
root = tk.Tk()
# この行はmessageboxを最前面に表示するために必要
root.attributes('-topmost', True)
# メインウィンドウを非表示化
root.withdraw()  

# ファイル選択ダイアログ
tk.messagebox.showinfo('ファイル選択', 'モザイク処理するファイルを選択してください')
inputMovie = filedialog.askopenfilename(filetypes=[("動画ファイル", "*")])

# プログレスバーを表示するためのサブウィンドウ
progress_win = tk.Toplevel()
progress_win.title("")
progress_win.geometry("300x100")
progress_win.resizable(False, False)

# ラベルを配置
label = ttk.Label(progress_win, text="頑張ってます…", font=("YuMincho", 15))
label.pack(pady=10)

# プログレスバー配置
progress = ttk.Progressbar(progress_win, mode="determinate", length=250)
progress.pack()

# ぼかし処理関数
def blur_face(img, passes=4):
    h, w = img.shape[:2]
    # 顔の短辺に応じてぼかし強度を決める（奇数にする必要あり）
    k = max(15, (min(h, w) // 3) | 1)
    
    blurred = img
    for _ in range(passes):
        blurred = cv2.GaussianBlur(blurred, (k, k), 0)
        
    return blurred

# モザイク処理（動画処理部分）
def process_video():
    try:
        global inputMovie

        if not inputMovie:
            tk.messagebox.showinfo('ファイル未選択', 'ファイルが選択されなかったため、終了します')
            progress_win.destroy()
            root.quit()
            return  

        # Nuitkaでパッケージ化された場合、sys._MEIPASSを使用
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        # ONNXモデルのパスを設定
        model_path = os.path.join(base_path, "face_detection_yunet_2023mar.onnx")

        # ffmpegのパスを設定
        ffmpeg_path = os.path.join(base_path, "ffmpeg.exe")
        
        # OpenCVのYuNetモデルをロード
        yunet_model = cv2.FaceDetectorYN.create(model_path, "", (320, 320), 0.6, 0.3, 5000)

        cap = cv2.VideoCapture(inputMovie)
        fmt = cv2.VideoWriter_fourcc(*"mp4v")
        # FPSとサイズ(縦・横)は元動画から取得
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        size = (width, height)

        # 検出間引き・ダウンスケール用の変数
        DETECT_EVERY = 5          # 何フレームおきに検出するか
        DETECT_WIDTH = 640        # 検出用にリサイズする幅
        scale = DETECT_WIDTH / width
        detect_size = (DETECT_WIDTH, int(height * scale))
        yunet_model.setInputSize(detect_size) 
        frame_idx = 0
        last_faces = None

        # 動画の総フレーム数を取得し、初期値=0でプログレスバーを設定
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        progress["maximum"] = total_frames
        progress["value"] = 0

        # 出力ファイル設定
        dirname = os.path.dirname(inputMovie)
        basename = os.path.splitext(os.path.basename(inputMovie))[0]
        outputMovie = os.path.join(dirname, f"{basename}_mosaiced.mp4")

        # 出力ファイル設定
        dirname = os.path.dirname(inputMovie)
        basename = os.path.splitext(os.path.basename(inputMovie))[0]
        finalOutputPath = os.path.join(dirname, f"{basename}_out.mp4")

        # ffmpegプロセスを起動し、フレームをパイプで直接渡す
        ffmpeg_process = subprocess.Popen([
                ffmpeg_path, "-y",
                "-f", "rawvideo", "-pix_fmt", "bgr24",
                "-s", f"{width}x{height}", "-r", str(fps),
                "-i", "-",
                "-i", inputMovie,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest",
                finalOutputPath
            ], stdin=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # stderrを別スレッドで継続的に読み取り、詰まらないようにする
        ffmpeg_stderr_lines = []
        def _drain_stderr():
            for line in ffmpeg_process.stderr:
                ffmpeg_stderr_lines.append(line)
        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()
    
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % DETECT_EVERY == 0:
                        small_frame = cv2.resize(frame, detect_size)
                        blurred_small = cv2.GaussianBlur(small_frame, (5, 5), 0)
                        faces = yunet_model.detect(blurred_small)
                        if faces[1] is not None:
                            faces[1][:, :4] /= scale   # 座標を元のフレームサイズに戻す
                        last_faces = faces
            else:
                faces = last_faces

            frame_idx += 1

            # ぼかし処理
            if faces[1] is not None:
                for face in faces[1]:
                    x, y, w, h = face[:4].astype(int)

                    # 小さすぎる顔を無視
                    if w * h < 100 or w < 10 or h < 10:  
                        continue  

                    x, y, w, h = max(0, x), max(0, y), min(width - x, w), min(height - y, h)
                    frame[y:y + h, x:x + w] = blur_face(frame[y:y + h, x:x + w])

            try:
                ffmpeg_process.stdin.write(frame.tobytes())
            except (BrokenPipeError, OSError):
                stderr_output = ffmpeg_process.stderr.read().decode(errors="ignore")
                returncode = ffmpeg_process.poll()
                messagebox.showerror("ffmpegエラー", f"終了コード: {returncode}\n\n{stderr_output}")
                raise

            # プログレスバーを更新
            progress["value"] += 1
            # GUIを更新
            progress_win.update_idletasks()  

        # 後処理
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()
        cap.release()
        
        # 動画と音声をffmpegで合成（再エンコードなし）
        finalOutputPath = os.path.join(dirname, f"{basename}_out.mp4")
    
        # ↓ 音声だけmp3として抽出
        outputAudioFullPath = os.path.join(dirname, f"{basename}.mp3")
        subprocess.run([
            ffmpeg_path, "-y",
            "-i", inputMovie,
            "-vn",                # 映像なし
            "-acodec", "libmp3lame",
            "-q:a", "2",           # 音質（0が最高、2は十分高音質でファイルサイズも抑えめ）
            outputAudioFullPath
        ], check=True, creationflags=subprocess.CREATE_NO_WINDOW)

        # プログレスバーを停止・閉じる
        progress["value"] = total_frames # 100%に設定
        progress_win.update_idletasks()
        progress_win.destroy()

        # 動画出力直後にアクセスすると排他制御により削除等ができないため、1秒待機
        time.sleep(1)
        
        # 処理完了のメッセージを表示
        messagebox.showinfo("処理完了", "動画の書き出しが完了しました。")
        
        # Tkinterメインループを終了
        root.quit()
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        sys.stderr = sys.__stderr__  # 一時的に標準エラーを復元(念のため)
        progress_win.destroy()
        messagebox.showerror("エラーが発生しました", f"{e}\n\n{error_detail}")
        root.quit()

# 別スレッドで処理を実行
thread = threading.Thread(target=process_video)
thread.start()

# Tkinterメインループ
root.mainloop()