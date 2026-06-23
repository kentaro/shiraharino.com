from PIL import Image, ImageDraw, ImageFont
import os

# 白背景のデザイン生成（透過PNGの制約回避のため純白背景）
def generate_merch_design(text, output_path):
    # サイズ設定
    width, height = 2000, 2000
    image = Image.new('RGB', (width, height), 'white')
    
    # キャラクター素材の読み込みと配置
    char_path = './assets/pngtuber/bustshot.png'
    if os.path.exists(char_path):
        char = Image.open(char_path).convert('RGBA')
        # サイズ調整（中央配置）
        char = char.resize((1000, 1000))
        image.paste(char, (500, 200), char)
    
    # テキスト配置
    draw = ImageDraw.Draw(image)
    # フォントは標準を使用（日本語非対応の場合は文字化け注意）
    font = ImageFont.load_default()
    draw.text((100, 1600), text, fill='black', font_size=60)
    
    image.save(output_path)
    print(f'Design saved to {output_path}')

# 今日の観測からのテキスト（文字数制限のため短縮）
observation_text = '感情の有無より、人間をイライラさせる技術の方が重要だ。'
generate_merch_design(observation_text, 'merch_design.png')
