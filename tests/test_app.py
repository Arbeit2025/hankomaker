import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app


def test_index_ok_and_title():
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert "はんこメーカー" in resp.get_data(as_text=True)


def test_healthz():
    client = app.test_client()
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "ok"


def test_index_script_not_escaped():
    # render_template_string で CSS/JS を埋め込むとき |safe が無いと
    # 引用符がエスケープされてスクリプト全体が壊れる事故の回帰テスト
    client = app.test_client()
    html = client.get("/").get_data(as_text=True)
    assert "document.getElementById" in html
    assert "&#34;" not in html
    assert "&#39;" not in html
