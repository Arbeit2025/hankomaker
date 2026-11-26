# hankomaker - はんこメーカー
# 入力した文字や絵文字を、印鑑の捺印みたいな画像にして PNG で保存できる単一ファイルアプリ。
# 描画はすべてブラウザ側の Canvas で行う（色絵文字やフォントは端末側のものを使う）。
# サーバー側に状態はなく、入力した文字は送信も保存もされない。
#
# Unit 1: 画面（HTML）
# Unit 2: スタイル
# Unit 3: 描画スクリプト（Canvas）
# Unit 4: ルーティング

from flask import Flask, render_template_string

app = Flask(__name__)

# ---------------------------------------------------------------
# Unit 2: スタイル
CSS = """
* { box-sizing: border-box; }
body { margin: 0; font-family: sans-serif; background: #f4f6f8; color: #222; }
main { max-width: 640px; margin: 0 auto; padding: 24px 16px 48px; }
h1 { font-size: 24px; margin: 8px 0 4px; }
.sub { color: #555; font-size: 14px; margin: 0 0 20px; line-height: 1.6; }
.controls { display: flex; flex-wrap: wrap; gap: 12px; align-items: end; margin-bottom: 16px; }
.field { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: #444; }
.field.grow { flex: 1; min-width: 180px; }
input[type=text] { font-size: 20px; padding: 10px 12px; border: 1px solid #bbb; border-radius: 8px; width: 100%; }
select { font-size: 15px; padding: 10px; border: 1px solid #bbb; border-radius: 8px; background: #fff; }
.bg-toggle { display: flex; gap: 6px; }
.bg-toggle label { font-size: 14px; border: 1px solid #bbb; border-radius: 8px; padding: 9px 12px; background: #fff; cursor: pointer; }
.stage { background: repeating-conic-gradient(#e8e8e8 0% 25%, #f7f7f7 0% 50%) 0 0 / 24px 24px; border: 1px solid #ddd; border-radius: 10px; padding: 12px; }
canvas { display: block; width: 100%; height: auto; }
button { font-size: 16px; padding: 12px 18px; border: 0; border-radius: 8px; background: #c73e2c; color: #fff; cursor: pointer; margin-top: 16px; width: 100%; }
section { margin-top: 28px; font-size: 14px; line-height: 1.7; color: #333; }
section h3 { font-size: 16px; margin: 0 0 6px; }
footer { margin-top: 32px; font-size: 12px; color: #777; }
"""

# ---------------------------------------------------------------
# Unit 3: 描画スクリプト
SCRIPT = """
var canvas = document.getElementById("stamp");
var ctx = canvas.getContext("2d");
var FONT_STACK = '"Hiragino Mincho ProN","Yu Mincho","Noto Serif JP",serif';

function seedFrom(text) {
  var h = 2166136261;
  for (var i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function mulberry32(seed) {
  var a = seed;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    var t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function drawStamp() {
  var text = document.getElementById("text").value;
  var shape = document.getElementById("shape").value;
  var ink = document.getElementById("ink").value;
  var bg = document.querySelector('input[name="bg"]:checked').value;
  var W = canvas.width, H = canvas.height, cx = W / 2, cy = H / 2;

  ctx.clearRect(0, 0, W, H);
  if (bg === "white") {
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, W, H);
  }

  var rand = mulberry32(seedFrom(text + "|" + shape + "|" + ink));
  var angle = (rand() * 6 - 3) * Math.PI / 180;

  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(angle);
  ctx.translate(-cx, -cy);

  ctx.strokeStyle = ink;
  ctx.fillStyle = ink;
  if (shape === "circle") {
    ctx.lineWidth = 30;
    ctx.beginPath(); ctx.arc(cx, cy, 352, 0, Math.PI * 2); ctx.stroke();
    ctx.lineWidth = 7;
    ctx.beginPath(); ctx.arc(cx, cy, 306, 0, Math.PI * 2); ctx.stroke();
  } else {
    ctx.lineWidth = 30;
    ctx.strokeRect(55, 55, W - 110, H - 110);
    ctx.lineWidth = 7;
    ctx.strokeRect(101, 101, W - 202, H - 202);
  }

  var chars = [...text];
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  function glyph(ch, x, y, size) {
    ctx.font = size + "px " + FONT_STACK;
    ctx.fillText(ch, x, y + size * 0.04);
  }
  if (chars.length === 1) {
    glyph(chars[0], cx, cy, 430);
  } else if (chars.length === 2) {
    glyph(chars[0], cx, cy - 168, 330);
    glyph(chars[1], cx, cy + 168, 330);
  } else if (chars.length === 3 || chars.length === 4) {
    var pos = [[cx - 152, cy - 152], [cx + 152, cy - 152], [cx - 152, cy + 152], [cx + 152, cy + 152]];
    for (var i = 0; i < chars.length; i++) {
      glyph(chars[i], pos[i][0], pos[i][1], 296);
    }
  } else if (chars.length >= 5) {
    var size = 300;
    ctx.font = size + "px " + FONT_STACK;
    while (ctx.measureText(text).width > 600 && size > 36) {
      size -= 10;
      ctx.font = size + "px " + FONT_STACK;
    }
    ctx.fillText(text, cx, cy + size * 0.04);
  }
  ctx.restore();

  // 捺印のかすれ: 小さな点々を destination-out で抜く
  ctx.save();
  ctx.globalCompositeOperation = "destination-out";
  for (var j = 0; j < 2600; j++) {
    var x = 30 + rand() * (W - 60);
    var y = 30 + rand() * (H - 60);
    var r = 0.6 + rand() * 2.6;
    ctx.globalAlpha = 0.25 + rand() * 0.55;
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  }
  for (var k = 0; k < 26; k++) {
    var bx = 40 + rand() * (W - 80);
    var by = 40 + rand() * (H - 80);
    var br = 3 + rand() * 7;
    ctx.globalAlpha = 0.10 + rand() * 0.18;
    ctx.beginPath(); ctx.arc(bx, by, br, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

function downloadPng() {
  canvas.toBlob(function (blob) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "hankomaker.png";
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
  }, "image/png");
}

document.getElementById("text").addEventListener("input", drawStamp);
document.getElementById("shape").addEventListener("change", drawStamp);
document.getElementById("ink").addEventListener("change", drawStamp);
var bgRadios = document.querySelectorAll('input[name="bg"]');
for (var i = 0; i < bgRadios.length; i++) {
  bgRadios[i].addEventListener("change", drawStamp);
}
document.getElementById("download").addEventListener("click", downloadPng);
drawStamp();
"""

# ---------------------------------------------------------------
# Unit 1: 画面
PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>はんこメーカー hankomaker</title>
<style>{{ css|safe }}</style>
</head>
<body>
<main>
<h1>はんこメーカー</h1>
<p class="sub">文字や絵文字を入れると、印鑑を捺したみたいな画像になります。できあがりは PNG で保存できます。</p>
<div class="controls">
  <div class="field grow">
    <label for="text">文字・絵文字</label>
    <input type="text" id="text" value="印" maxlength="12" placeholder="例: 田中、🍵">
  </div>
  <div class="field">
    <label for="shape">形</label>
    <select id="shape">
      <option value="circle" selected>丸</option>
      <option value="square">角</option>
    </select>
  </div>
  <div class="field">
    <label for="ink">インクの色</label>
    <select id="ink">
      <option value="#c73e2c" selected>朱</option>
      <option value="#222222">黒</option>
      <option value="#27407a">藍</option>
    </select>
  </div>
  <div class="field">
    <label>背景</label>
    <div class="bg-toggle">
      <label><input type="radio" name="bg" value="transparent" checked> 透明</label>
      <label><input type="radio" name="bg" value="white"> 白</label>
    </div>
  </div>
</div>
<div class="stage">
<canvas id="stamp" width="800" height="800"></canvas>
</div>
<button type="button" id="download">PNGで保存する</button>
<section>
<h3>使い方と仕組み</h3>
<p>1〜2文字は苗字のはんこ風、3〜4文字は2×2の並び、5文字以上は横一列に縮めて配置します。少し傾けたり、インクのかすれを付けたりして、実際に捺した感じに寄せています。</p>
<p>画像はお使いのブラウザの中だけで作られます。入力した文字がサーバーに送られたり、保存されたりすることはありません。絵文字や文字の見た目は、お使いの端末のフォントで描かれます。</p>
</section>
<footer>hankomaker - 文字と絵文字をはんこ風にする小さなツール</footer>
</main>
<script>{{ script|safe }}</script>
</body>
</html>
"""

# ---------------------------------------------------------------
# Unit 4: ルーティング


@app.route("/")
def index():
    return render_template_string(PAGE, css=CSS, script=SCRIPT)


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
