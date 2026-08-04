import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from models import AdminSetting
from services.report_service import generate_restock_report


def _get_setting(db: Session, key: str, default: str = ""):
    """Read a single setting from AdminSetting table."""
    s = db.query(AdminSetting).filter(AdminSetting.key == key).first()
    return s.value if s else default


def get_smtp_config(db: Session):
    """Read SMTP configuration from AdminSetting."""
    return {
        "host": _get_setting(db, "smtp_host", ""),
        "port": int(_get_setting(db, "smtp_port", "587")),
        "user": _get_setting(db, "smtp_user", ""),
        "password": _get_setting(db, "smtp_pass", ""),
        "from_email": _get_setting(db, "smtp_from", ""),
        "to_email": _get_setting(db, "smtp_to", ""),
    }


def send_test_email(db: Session, to_email: str):
    """Send a test email to verify SMTP configuration."""
    config = get_smtp_config(db)

    if not config["host"] or not config["user"]:
        return {"ok": False, "msg": "SMTP未配置，请先在管理员设置中配置SMTP"}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "📧 一站式物资管理系统 - 测试邮件"
        msg["From"] = config["from_email"] or config["user"]
        msg["To"] = to_email

        html = f"""
        <html>
        <body style="font-family: sans-serif; padding: 20px;">
          <h2>✅ SMTP 配置测试成功</h2>
          <p>这是一封来自<strong>一站式物资管理系统</strong>的测试邮件。</p>
          <p>如果您收到了这封邮件，说明 SMTP 配置正确，系统可以正常发送补货报表。</p>
          <hr>
          <p style="color: #999; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html", "utf-8"))

        server = smtplib.SMTP(config["host"], config["port"], timeout=15)
        server.starttls()
        server.login(config["user"], config["password"])
        server.sendmail(msg["From"], [to_email], msg.as_string())
        server.quit()

        return {"ok": True, "msg": f"测试邮件已发送到 {to_email}"}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "msg": "SMTP认证失败，请检查邮箱地址和授权码"}
    except smtplib.SMTPConnectError:
        return {"ok": False, "msg": f"无法连接到SMTP服务器 {config['host']}:{config['port']}"}
    except Exception as e:
        return {"ok": False, "msg": f"邮件发送失败: {str(e)}"}


def send_restock_email(db: Session, to_email: str = None, window_days: int = 30):
    """Generate restock report and send via email."""
    config = get_smtp_config(db)

    if not config["host"] or not config["user"]:
        return {"ok": False, "msg": "SMTP未配置，请先在管理员设置中配置SMTP"}

    report = generate_restock_report(db, window_days)
    if not to_email:
        to_email = config["to_email"]
    if not to_email:
        return {"ok": False, "msg": "未设置收件人邮箱，请在管理员设置中配置"}

    # Build HTML email
    urgency_labels = {"critical": "🔴 紧急", "warning": "🟡 预警", "ok": "✅ 正常", "insufficient_data": "📊 数据不足"}
    rows_html = ""
    for item in report["items"]:
        days = f"{int(item['days_until_empty'])}天" if item["days_until_empty"] is not None else "N/A"
        qty = f"{item['suggested_restock_qty']} {item['unit']}" if item["suggested_restock_qty"] > 0 else "-"
        rows_html += f"""
        <tr>
          <td>{item['icon']} {item['name']}</td>
          <td>{item['spec'] or '-'}</td>
          <td style="text-align:right">{item['current_stock']} {item['unit']}</td>
          <td style="text-align:right">{item['daily_velocity']:.1f}/天</td>
          <td style="text-align:right">{days}</td>
          <td style="text-align:right">{qty}</td>
          <td>{urgency_labels.get(item['status'], item['status'])}</td>
        </tr>"""

    html = f"""
    <html>
    <body style="font-family: 'Microsoft YaHei', sans-serif; padding: 20px; background: #f8fafc;">
      <div style="max-width: 700px; margin: 0 auto; background: #fff; border-radius: 16px; padding: 24px; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
        <h2 style="color: #1a2332;">📊 物资补货建议报表</h2>
        <p style="color: #5a6b7d;">报表周期: 最近 {window_days} 天 | 生成时间: {report['generated_at'][:19]}</p>

        <div style="display: flex; gap: 12px; margin: 16px 0;">
          <div style="flex:1; text-align:center; padding:12px; background:#fef2f2; border-radius:10px;">
            <div style="font-size:1.5rem; font-weight:800; color:#dc2626;">{report['summary']['critical_count']}</div>
            <div style="font-size:0.8rem; color:#92400e;">🔴 紧急</div>
          </div>
          <div style="flex:1; text-align:center; padding:12px; background:#fffbeb; border-radius:10px;">
            <div style="font-size:1.5rem; font-weight:800; color:#d97706;">{report['summary']['warning_count']}</div>
            <div style="font-size:0.8rem; color:#a16207;">🟡 预警</div>
          </div>
          <div style="flex:1; text-align:center; padding:12px; background:#f8fafc; border-radius:10px;">
            <div style="font-size:1.5rem; font-weight:800; color:#1a2332;">{report['summary']['total_items']}</div>
            <div style="font-size:0.8rem; color:#5a6b7d;">📦 总计</div>
          </div>
        </div>

        <table style="width:100%; border-collapse:collapse; margin-top:16px; font-size:0.9rem;">
          <thead>
            <tr style="background:#667eea; color:#fff;">
              <th style="padding:10px; text-align:left; border-radius:8px 0 0 0;">物资</th>
              <th style="padding:10px; text-align:left;">规格</th>
              <th style="padding:10px; text-align:right;">库存</th>
              <th style="padding:10px; text-align:right;">日均消耗</th>
              <th style="padding:10px; text-align:right;">预计耗尽</th>
              <th style="padding:10px; text-align:right;">建议补货</th>
              <th style="padding:10px; text-align:left; border-radius:0 8px 0 0;">状态</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>

        <hr style="margin: 20px 0; border: none; border-top: 1px solid #e2e8f0;">
        <p style="color: #999; font-size: 12px;">此报表由一站式物资管理系统自动生成。如有问题请联系管理员。</p>
      </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📊 物资补货报表 - {report['generated_at'][:10]}"
        msg["From"] = config["from_email"] or config["user"]
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))

        server = smtplib.SMTP(config["host"], config["port"], timeout=15)
        server.starttls()
        server.login(config["user"], config["password"])
        server.sendmail(msg["From"], [to_email], msg.as_string())
        server.quit()

        return {"ok": True, "msg": f"补货报表已发送到 {to_email}"}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "msg": "SMTP认证失败，请检查邮箱地址和授权码"}
    except smtplib.SMTPConnectError:
        return {"ok": False, "msg": f"无法连接到SMTP服务器 {config['host']}:{config['port']}"}
    except Exception as e:
        return {"ok": False, "msg": f"邮件发送失败: {str(e)}"}
