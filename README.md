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
	- ReleasesからBlurringMovie.zipをダウンロードし、任意のフォルダに解凍
	- 解凍したフォルダ構成を変えず、BlurringMovie.exeをダブルクリックで起動し、動画ファイルを選択する
	- face_detection_yunet_2023mar.onnx及びffmpeg.exeを移動・削除した場合、プログラムはエラー終了する
	
- 開発者向け
	- requirements.txtをインストール
	- [Releases](https://github.com/yajimayajiuma/BlurringMovie/releases/tag/v1.1.0) から最新のzipをダウンロードし、
	  `face_detection_yunet_2023mar.onnx` と `ffmpeg.exe` を`BlurringMovie.py` と同じフォルダに配置
	- 上記環境を満たし、以下コマンドを実行
	
	```sh
	python BlurringMovie.py
	```

## 使用ライブラリ・モデルについて

- 本ソフトウェアは [FFmpeg](https://ffmpeg.org) を利用しています。
  FFmpegはGNU General Public License v3 (GPLv3) の下で配布されています。
  ライセンス全文は同梱の `LICENSE` を参照してください。
  ソースコードは [FFmpeg公式サイト](https://ffmpeg.org/download.html) から入手可能です。
  （本配布物には [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) が提供する
  ビルド済みバイナリを使用しています）

- 顔検出には [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
  （Apache License 2.0）を使用しています。