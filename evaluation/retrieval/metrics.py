import logging

import pandas as pd

logger = logging.getLogger(__name__)

# פונקציות העזר מחוץ לפונקציה המרכזית
def recall_at_k(keyword, docs, k=5):
    """
    בודק האם מילת המפתח נמצאת לפחות באחד מ-k המסמכים הראשונים.
    """
    return int(any(keyword.lower() in d.page_content.lower() for d in docs[:k]))

def mrr(keyword, docs):
    """
    Mean Reciprocal Rank: מחשב את הדירוג ההופכי של המסמך הראשון שמכיל את מילת המפתח.
    """
    for rank, doc in enumerate(docs, 1):
        if keyword.lower() in doc.page_content.lower():
            return 1 / rank
    return 0.0


def evaluate_retrieval(test_set, vstore):
    rows = []
    
    for query_t, kw in test_set:
        logger.debug("QUERY: %s | TARGET KEYWORD: %r", query_t, kw)

        # שליפה סמנטית עם ציונים
        results = vstore.db.similarity_search_with_score(query_t, k=10)
        semantic_docs = [r[0] for r in results]
        
        # הדפסת המסמכים שנשלפו לאבחון
        for i, (doc, score) in enumerate(results, 1):
            is_match = kw.lower() in doc.page_content.lower()
            match_marker = "MATCH" if is_match else "NO MATCH"
            content_snippet = doc.page_content.replace('\n', ' ')[:200]
            logger.debug(
                "Rank %s | Score: %.4f | %s | Source: %s | Content: %s...",
                i,
                score,
                match_marker,
                doc.metadata.get('relative_path', 'Unknown').split('/')[-1],
                content_snippet,
            )

        # מציאת הקובץ הראשון שבו נמצאה מילת המפתח
        source_found = "Not Found"
        for d in semantic_docs:
            if kw.lower() in d.page_content.lower():
                source_found = d.metadata.get('relative_path', 'Unknown')
                break
        
        rows.append({
            "Query": query_t[:45] + "...",
            "Keyword": kw,
            "Relative File": source_found.split('/')[-1],
            "Semantic R@5": recall_at_k(kw, semantic_docs, k=5),
            "Semantic MRR": round(mrr(kw, semantic_docs), 3)
        })
    
    # הדפסת הטבלה המסכמת בסוף
    df = pd.DataFrame(rows).set_index("Query")
    logger.info("Retrieval evaluation summary:\n%s", df.to_string())
    logger.info("Averages:\n%s", df.mean(numeric_only=True).to_string())
    
    return df