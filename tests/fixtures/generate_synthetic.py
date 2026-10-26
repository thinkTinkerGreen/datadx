"""Generate synthetic fixture packs for tests and CI.

Contains ONLY invented, harmless text and clearly fake PII/secrets.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA = pa.schema(
    [
        ("doc_id", pa.string()),
        ("source", pa.string()),
        ("lang_label", pa.string()),
        ("text", pa.string()),
    ]
)

SYNTHETIC_DOCS = [
    {
        "doc_id": "syn_clean_001",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "हा एक पूर्णपणे स्वच्छ आणि सुंदर मराठी मजकूर आहे. यात कोणताही दोष नाही.",
    },
    {
        "doc_id": "syn_a1_002",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "या मजकुरात\u200bझिरो विड्थ स्पेस आहे. तसेच ZWNJ\u200c आणि ZWJ\u200d देखील आहेत जे वाचले पाहिजेत.",
    },
    {
        "doc_id": "syn_a2_003",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "कंट्रोल कॅरेक्टर येथे आहे:\x07आणि येथे देखील\x1f तसेच CRLF\r\nआहे.",
    },
    {
        "doc_id": "syn_a3_004",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "येथे काही मोजिबाके आहे: à¤®à¤°à¤¾à¤ à¥€ मजकूर चाचणी.",
    },
    {
        "doc_id": "syn_a4_005",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "येथे रीप्लेसमेंट कॅरेक्टर आहेत: \ufffd \ufffd \ufffd आणि आणखी एक \ufffd.",
    },
    {
        "doc_id": "syn_b1_006",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "येथे एचटीएमएल एंटिटी आहे: &amp; आणि &nbsp; आणि &#2361;.",
    },
    {
        "doc_id": "syn_b2_007",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "येथे टॅग्स आहेत: <div>मराठी मजकूर</div><br/> आणि पॅराग्राफ.",
    },
    {
        "doc_id": "syn_b3_008",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "<|im_start|>system\nतू एक हुशार सहाय्यक आहेस.<|im_end|>\n<|im_start|>user\nनमस्कार.<|im_end|>",
    },
    {
        "doc_id": "syn_c2_009",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "ही एक पुनरावृत्ती ओळ आहे.\nही एक पुनरावृत्ती ओळ आहे.\nही एक पुनरावृत्ती ओळ आहे.\nकाही वेगळा मजकूर.",
    },
    {
        "doc_id": "syn_g1_010",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "येथे तुटलेली मात्रा आहे: क िशोर आणि व िशाल अभ्यास करत आहेत.",
    },
    {
        "doc_id": "syn_f1_011",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "माझा ईमेल fake_user_987654@example.com आहे आणि संपर्क +91 9876543210 आहे.",
    },
    {
        "doc_id": "syn_h1_012",
        "source": "synthetic",
        "lang_label": "mar_Deva",
        "text": "हा एक पूर्णपणे स्वच्छ आणि सुंदर मराठी मजकूर आहे. यात कोणताही दोष नाही.",
    },
]

# Synthetic gold standard docs (clean baseline)
GOLD_DOCS = [
    {
        "doc_id": f"gold_clean_{i:03d}",
        "source": "synthetic_gold",
        "lang_label": "mar_Deva",
        "text": f"हा सुवर्ण संचातील स्वच्छ मराठी दस्तऐवज क्रमांक {i} आहे. भाषा आणि व्याकरण शुद्ध आहे।",
    }
    for i in range(1, 201)
]


def main() -> None:
    fixtures_dir = Path(__file__).parent
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write synthetic pack
    pack_table = pa.Table.from_pylist(SYNTHETIC_DOCS, schema=SCHEMA)
    pack_path = fixtures_dir / "synthetic_pack.parquet"
    pq.write_table(pack_table, pack_path, compression="zstd")
    print(f"Generated synthetic pack ({len(SYNTHETIC_DOCS)} rows): {pack_path}")

    # 2. Write synthetic gold set
    gold_table = pa.Table.from_pylist(GOLD_DOCS, schema=SCHEMA)
    gold_path = fixtures_dir / "synthetic_gold.parquet"
    pq.write_table(gold_table, gold_path, compression="zstd")
    print(f"Generated synthetic gold set ({len(GOLD_DOCS)} rows): {gold_path}")


if __name__ == "__main__":
    main()
