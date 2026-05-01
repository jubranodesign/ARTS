import pandas as pd

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
        print(f"\n{'='*60}")
        print(f"🔍 QUERY: {query_t}")
        print(f"🎯 TARGET KEYWORD: '{kw}'")
        print(f"{'='*60}")

        # שליפה סמנטית עם ציונים
        results = vstore.db.similarity_search_with_score(query_t, k=10)
        semantic_docs = [r[0] for r in results]
        
        # הדפסת המסמכים שנשלפו לאבחון
        for i, (doc, score) in enumerate(results, 1):
            is_match = kw.lower() in doc.page_content.lower()
            match_marker = "✅ [MATCH]" if is_match else "❌ [NO MATCH]"
            
            print(f"\nRank {i} | Score: {score:.4f} | {match_marker}")
            print(f"Source: {doc.metadata.get('relative_path', 'Unknown').split('/')[-1]}")
            # מדפיסים רק את 200 התווים הראשונים כדי לא להציף את הטרמינל
            content_snippet = doc.page_content.replace('\n', ' ')[:200]
            print(f"Content: {content_snippet}...")
            print(f"{'-'*30}")

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
    print(f"\n\n{'#'*20} SUMMARY TABLE {'#'*20}")
    print(df.to_string())
    print(f"\n{'Averages':-<50}")
    print(df.mean(numeric_only=True).to_string())
    
    return df