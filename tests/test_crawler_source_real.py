from datetime import datetime

from app.services.crawler_source import parse_detail_html, parse_list_html


REAL_LIST_HTML = """
<html>
  <body>
    <ul>
      <li>
        <a href="/doc_5106.html">
          广东医科大学东莞校区学生第一食堂外包经营服务项目公开招标公告
          2026-06-02
          广东医科大学东莞校区学生第一食堂外包经营服务项目公开招标公告
          采购公告
          256人查看
        </a>
      </li>
      <li>
        <a href="/doc_5104.html">
          东莞市常平镇社区卫生服务中心（站点）空调维保服务采购项目结果公告
          2026-05-27
          东莞市常平镇社区卫生服务中心（站点）空调维保服务采购项目结果公告
          中标（成交）结果公告
          5人查看
        </a>
      </li>
    </ul>
  </body>
</html>
"""


REAL_DETAIL_HTML = """
<html>
  <body>
    <div class="content">
      <h2>国家税务总局东莞市税务局2026年“语音通知”外包服务项目简易磋商公告</h2>
      <div>采购公告</div>
      <div>来源：原创</div>
      <div>2026-05-27 11:22:46</div>
      <p>
        和盛咨询（广东）有限公司（以下简称“采购代理机构”）受国家税务总局东莞市税务局
        （以下简称“采购人”）的委托，现就国家税务总局东莞市税务局2026年“语音通知”外包服务项目
        进行简易磋商采购。
      </p>
      <p>采购预算：人民币900,000.00元</p>
      <p>响应文件提交截止时间：2026年06月03日 09时30分</p>
    </div>
  </body>
</html>
"""


def test_parse_hscgfw_list_html_returns_public_notice_items() -> None:
    items = parse_list_html(REAL_LIST_HTML)

    assert items == [
        {
            "title": "广东医科大学东莞校区学生第一食堂外包经营服务项目公开招标公告",
            "source_url": "http://www.hscgfw.com/doc_5106.html",
            "source": "hscgfw",
        }
    ]


def test_parse_hscgfw_detail_html_returns_normalized_tender_payload() -> None:
    detail = parse_detail_html(
        REAL_DETAIL_HTML,
        "http://www.hscgfw.com/doc_5103.html",
    )

    assert detail["source"] == "hscgfw"
    assert detail["source_url"] == "http://www.hscgfw.com/doc_5103.html"
    assert detail["title"] == "国家税务总局东莞市税务局2026年“语音通知”外包服务项目简易磋商公告"
    assert detail["city"] == "东莞"
    assert detail["publish_date"] == datetime(2026, 5, 27, 11, 22, 46)
    assert detail["deadline"] == datetime(2026, 6, 3, 9, 30)
    assert detail["buyer_name"] == "国家税务总局东莞市税务局"
    assert detail["agency_name"] == "和盛咨询（广东）有限公司"
    assert detail["budget_amount"] == "900,000.00"
    assert "进行简易磋商采购" in detail["content"]
