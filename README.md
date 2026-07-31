## 用途
動画ファイルを読み込み、顔認識した上でぼかしを入れる。  
動画と同じフォルダに、元のファイル名_out.拡張子でぼかしを入れた動画、元のファイル名.mp3を出力する。

## 実行環境
- 必須ライブラリ-> `requirements.txt`、`face_detection_yunet_2023mar.onnx`、`ffmpeg.exe`   
- 確認済み環境
    - Windows 11 Pro 25H2
    - Python 3.11.8
    
## 実行方法
- ユーザー向け
	- ReleasesからBlurringMovie.exeをダウンロードし、ダブルクリックする
	
- 開発者向け
	- requirements.txtをインストール
	- face_detection_yunet_2023mar.onnxをダウンロードし、BlurringMovie.pyと同じフォルダに配置
		- [入手先](https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx)
	- ffmpeg.exeをダウンロードし、BlurringMovie.pyと同じフォルダに配置
		- [入手先](https://ffmpeg.org/download.html)
	- 上記環境を満たし、以下コマンドを実行
	
	```sh
	python BlurringMovie.py
	```