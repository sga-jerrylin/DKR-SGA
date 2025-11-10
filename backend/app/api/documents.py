"""
文档管理 API
"""
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger

from app.models.document import Document, DocumentUploadResponse
from app.core.library_manager import LibraryManager
from app.core.document_processor import DocumentProcessor
from app.core.classifier import DocumentClassifier

router = APIRouter(prefix="/documents", tags=["documents"])

# 全局实例
library_manager = LibraryManager()
document_processor = DocumentProcessor()
classifier = DocumentClassifier()


@router.get("/", response_model=List[Document])
async def list_documents(category: str = None):
    """
    获取文档列表
    
    Args:
        category: 可选，按分类筛选
    """
    try:
        documents = library_manager.list_documents(category=category)
        return documents
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}", response_model=Document)
async def get_document(doc_id: str):
    """获取单个文档详情"""
    try:
        document = library_manager.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/batch")
async def upload_documents_batch(files: List[UploadFile] = File(...)):
    """
    批量上传文档

    Args:
        files: 多个 PDF 文件

    Returns:
        批量上传结果
    """
    results = []

    for file in files:
        try:
            # 验证文件类型
            if not file.filename.endswith('.pdf'):
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "只支持 PDF 文件"
                })
                continue

            # 调用单文件上传逻辑
            result = await _process_single_upload(file)
            results.append({
                "filename": file.filename,
                "success": result["success"],
                "doc_id": result.get("doc_id"),
                "category": result.get("category"),
                "error": result.get("error")
            })

        except Exception as e:
            logger.error(f"处理文件 {file.filename} 失败: {e}")
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })

    # 统计结果
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)

    return {
        "success": success_count > 0,
        "total": total_count,
        "success_count": success_count,
        "failed_count": total_count - success_count,
        "results": results
    }


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    上传单个文档（Agent-First：自动分类）

    工作流程：
    1. 保存上传的 PDF
    2. 处理文档（PDF → Video + Summary）
    3. 使用 LLM 自动分类
    4. 添加到文档库
    """
    try:
        # 验证文件类型
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持 PDF 文件")

        result = await _process_single_upload(file)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "上传失败"))

        return DocumentUploadResponse(
            success=True,
            doc_id=result["doc_id"],
            category=result["category"],
            message=f"文档已成功上传并分类到 '{result['category']}'"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _process_single_upload(file: UploadFile) -> dict:
    """
    处理单个文件上传（内部方法）

    Returns:
        上传结果字典
    """
    try:
        logger.info(f"开始处理上传文档: {file.filename}")
        
        # 生成文档 ID
        import uuid
        from datetime import datetime
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 保存上传文件到 documents 目录
        from app.config import get_settings
        settings = get_settings()
        settings.documents_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = settings.documents_dir / f"{doc_id}.pdf"

        with open(pdf_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"PDF 已保存: {pdf_path}")
        
        # 处理文档（PDF → Video + Summary）
        process_result = await document_processor.process_document(
            pdf_path=str(pdf_path),
            doc_id=doc_id,
            title=file.filename.replace('.pdf', '')
        )
        
        if not process_result["success"]:
            raise HTTPException(status_code=500, detail=f"文档处理失败: {process_result.get('error')}")
        
        # 自动分类
        # 构造 summary_data，包含 page_summaries
        summaries = process_result.get("summaries", [])
        page_summaries = [s.get("summary", "") for s in summaries]
        summary_data = {
            "page_summaries": page_summaries,
            "summaries": summaries
        }
        classify_result = await classifier.classify(
            title=file.filename,
            summary_data=summary_data
        )

        category = classify_result.get("category", "其他")
        logger.info(f"文档自动分类: {category} (置信度: {classify_result.get('confidence', 0):.2f})")

        # 生成文档级别的 Summary（取前 3 页的 Summary 合并）
        doc_summary = "\n\n".join(page_summaries[:3]) if page_summaries else "无摘要"
        if len(doc_summary) > 500:
            doc_summary = doc_summary[:500] + "..."

        # 添加到文档库
        title = file.filename.replace('.pdf', '')
        filename = file.filename  # 保留原始文件名
        metadata = {
            "filename": filename,  # 原始文件名
            "file_path": str(pdf_path),
            "video_path": process_result.get("video_path"),
            "summary_path": process_result.get("summary_path"),
            "page_count": process_result.get("page_count", 0),
            "doc_summary": doc_summary,  # 文档级别的 Summary
            "keywords": process_result.get("keywords", []),
            "upload_time": datetime.now().isoformat()
        }

        library_manager.add_document(
            doc_id=doc_id,
            title=title,
            category=category,
            category_confidence=classify_result.get('confidence', 0.0),
            metadata=metadata
        )

        logger.info(f"文档上传成功: {doc_id}")

        return {
            "success": True,
            "doc_id": doc_id,
            "category": category,
            "message": f"文档已成功上传并分类到 '{category}'"
        }

    except Exception as e:
        logger.error(f"上传文档失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    try:
        success = library_manager.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")
        
        logger.info(f"文档已删除: {doc_id}")
        return {"success": True, "message": f"文档 {doc_id} 已删除"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

