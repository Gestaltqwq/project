"""邮件服务：高潜筛选、LLM 生成、记录 CRUD、Prompt 管理

【MVC 归属】Service 层
"""
from typing import Optional

import numpy as np

from app.core.database import SessionLocal
from app.core.response import BizException
from app.core.config import settings
from app.models.customer import Customer
from app.models.prompt_template import PromptTemplate
from app.models.email_record import EmailRecord
from app.services.llm_service import LLMService, DEFAULT_PROMPT_TEMPLATE


def get_prompt() -> dict:
    db = SessionLocal()
    try:
        tpl = PromptTemplate.ensure_active(db, DEFAULT_PROMPT_TEMPLATE)
        return tpl.to_dict()
    finally:
        db.close()


def update_prompt(content: str) -> dict:
    db = SessionLocal()
    try:
        tpl = PromptTemplate.update_content(db, content)
        return tpl.to_dict()
    finally:
        db.close()


def _customer_dict(c: Customer) -> dict:
    return c.to_dict()


def targets(percentile: Optional[float] = None, min_prob: Optional[float] = None,
            page: int = 1, per_page: int = 20) -> dict:
    """筛选高潜客户：min_prob=按概率阈值；否则 percentile=按分位数（默认 top 10%）"""
    db = SessionLocal()
    try:
        rows = db.query(Customer).all()
    finally:
        db.close()
    if not rows:
        raise BizException(2001, "暂无数据，请先上传")
    if all(c.predicted_prob is None for c in rows):
        raise BizException(3002, "请先执行预测")

    if min_prob is not None:
        # 按概率阈值筛选：购买概率 >= min_prob 的用户
        threshold = float(min_prob)
        candidates = [c for c in rows if c.predicted_prob is not None and c.predicted_prob >= min_prob]
    else:
        # 按分位数筛选：percentile=0.9 → 概率最高的 10%
        probs = np.array([c.predicted_prob for c in rows])
        threshold = float(np.quantile(probs, percentile or 0.9))
        candidates = [c for c in rows if c.predicted_prob >= threshold]
    candidates.sort(key=lambda c: c.predicted_prob, reverse=True)

    total = len(candidates)
    pages = (total + per_page - 1) // per_page if per_page else 0
    start = (page - 1) * per_page
    items = candidates[start:start + per_page]
    return {
        "threshold": round(threshold, 4),
        "total": total,
        "customers": [_customer_dict(c) for c in items],
    }


def generate(limit: Optional[int], customer_ids: Optional[list], user_id: Optional[int]) -> dict:
    """批量生成营销邮件（limit=top N；customer_ids=指定客户）"""
    db = SessionLocal()
    try:
        if customer_ids:
            customers = db.query(Customer).filter(Customer.id.in_(customer_ids)).all()
        else:
            rows = db.query(Customer).all()
            if all(c.predicted_prob is None for c in rows):
                raise BizException(3002, "请先执行预测")
            # 排除已生成过邮件的客户（避免重复生成同一批人）
            generated_ids = {r[0] for r in db.query(EmailRecord.customer_id).all()}
            rows = [c for c in rows if c.id not in generated_ids]
            if not rows:
                raise BizException(2001, "所有高潜客户都已生成过邮件")
            rows.sort(key=lambda c: c.predicted_prob or 0, reverse=True)
            customers = rows[:limit] if limit else rows[:5]

        if not customers:
            raise BizException(2001, "没有可生成邮件的客户")

        tpl = PromptTemplate.ensure_active(db, DEFAULT_PROMPT_TEMPLATE)

        records, failed = [], 0
        llm = LLMService()  # AI 方案 §3.4：未配 KEY → 全部 failed，不抛异常

        # 增强：LLM 调用是纯 I/O，用线程池并发加速（DB 写入仍在主线程，避免会话竞争）
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(
                lambda c: (c.id, llm.generate_email(_customer_dict(c), tpl.content)),
                customers,
            ))

        for cid, result in results:
            if result["success"]:
                rec = EmailRecord(
                    customer_id=cid,
                    email_subject=str(result["subject"])[:200],
                    email_content=str(result["content"]),
                    status="generated",
                    created_by=user_id,
                )
                records.append({"customer_id": cid, "status": "generated",
                                "subject": result["subject"]})
            else:
                failed += 1
                rec = EmailRecord(
                    customer_id=cid, email_subject="生成失败",
                    email_content=f"LLM 调用失败: {result['error']}",
                    status="failed", created_by=user_id,
                )
                records.append({"customer_id": cid, "status": "failed"})
            db.add(rec)
        db.commit()
    finally:
        db.close()

    return {"generated_count": len(records) - failed, "failed_count": failed, "records": records}


def list_records(page: int, per_page: int, status: Optional[str], user_id: Optional[int], is_admin: bool) -> dict:
    db = SessionLocal()
    try:
        q = db.query(EmailRecord)
        if not is_admin:
            q = q.filter(EmailRecord.created_by == user_id)
        if status:
            q = q.filter(EmailRecord.status == status)
        total = q.count()
        pages = (total + per_page - 1) // per_page if per_page else 0
        items = q.order_by(EmailRecord.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

        # 补充创建人用户名（一次批量查询，避免 N+1）
        username_map = {}
        if is_admin and items:
            from app.models.user import User
            ids = [rec.created_by for rec in items if rec.created_by]
            if ids:
                for u in db.query(User).filter(User.id.in_(ids)).all():
                    username_map[u.id] = u.username

        result = []
        for rec in items:
            d = rec.to_dict()
            if is_admin:
                d["created_by_username"] = username_map.get(rec.created_by)
            result.append(d)
        return {"items": result, "total": total, "page": page, "per_page": per_page, "pages": pages}
    finally:
        db.close()


def _check_access(rec: EmailRecord, user_id: Optional[int], is_admin: bool):
    """归属校验（修复 IDOR）：非 admin 只能操作自己创建的记录"""
    if not is_admin and rec.created_by != user_id:
        raise BizException(1003, "无权访问该邮件记录", 403)


def get_record(record_id: int, user_id: Optional[int] = None, is_admin: bool = True) -> dict:
    db = SessionLocal()
    try:
        rec = db.query(EmailRecord).filter(EmailRecord.id == record_id).first()
        if not rec:
            raise BizException(2001, "邮件记录不存在", 404)
        _check_access(rec, user_id, is_admin)
        return rec.to_dict()
    finally:
        db.close()


def update_record(record_id: int, email_subject: Optional[str], email_content: Optional[str],
                  user_id: Optional[int] = None, is_admin: bool = True) -> dict:
    db = SessionLocal()
    try:
        rec = db.query(EmailRecord).filter(EmailRecord.id == record_id).first()
        if not rec:
            raise BizException(2001, "邮件记录不存在", 404)
        _check_access(rec, user_id, is_admin)
        if email_subject is not None:
            rec.email_subject = email_subject
        if email_content is not None:
            rec.email_content = email_content
        rec.status = "edited"
        db.commit()
        db.refresh(rec)
        return rec.to_dict()
    finally:
        db.close()


def set_status(record_id: int, status: str,
               user_id: Optional[int] = None, is_admin: bool = True) -> dict:
    db = SessionLocal()
    try:
        rec = db.query(EmailRecord).filter(EmailRecord.id == record_id).first()
        if not rec:
            raise BizException(2001, "邮件记录不存在", 404)
        _check_access(rec, user_id, is_admin)
        rec.status = status
        db.commit()
        db.refresh(rec)
        return rec.to_dict()
    finally:
        db.close()


def delete_record(record_id: int, user_id: Optional[int] = None, is_admin: bool = True) -> dict:
    db = SessionLocal()
    try:
        rec = db.query(EmailRecord).filter(EmailRecord.id == record_id).first()
        if not rec:
            raise BizException(2001, "邮件记录不存在", 404)
        _check_access(rec, user_id, is_admin)
        db.delete(rec)
        db.commit()
        return {"success": True}
    finally:
        db.close()


def batch_delete(record_ids: list, user_id: Optional[int] = None, is_admin: bool = True) -> dict:
    """批量删除（非 admin 只删自己的，越权部分自动跳过）"""
    db = SessionLocal()
    try:
        q = db.query(EmailRecord).filter(EmailRecord.id.in_(record_ids))
        if not is_admin:
            q = q.filter(EmailRecord.created_by == user_id)
        deleted = q.delete(synchronize_session=False)
        db.commit()
        return {"deleted_count": deleted}
    finally:
        db.close()
