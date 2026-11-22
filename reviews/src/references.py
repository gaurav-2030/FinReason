"""One reference list (IEEE style) shared by all three reviews, so citation numbers never change."""

REFS = [
    ("finqa", 'Z. Chen, W. Chen, C. Smiley, S. Shah, I. Borova, D. Langdon, R. Moussa, M. Beane, T.-H. Huang, B. Routledge, and W. Y. Wang, "FinQA: A dataset of numerical reasoning over financial data," in <i>Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP)</i>, 2021, pp. 3697–3711.'),
    ("tatqa", 'F. Zhu, W. Lei, Y. Huang, C. Wang, S. Zhang, J. Lv, F. Feng, and T.-S. Chua, "TAT-QA: A question answering benchmark on a hybrid of tabular and textual content in finance," in <i>Proc. ACL-IJCNLP</i>, 2021, pp. 3277–3287.'),
    ("convfinqa", 'Z. Chen, S. Li, C. Smiley, Z. Ma, S. Shah, and W. Y. Wang, "ConvFinQA: Exploring the chain of numerical reasoning in conversational finance question answering," in <i>Proc. EMNLP</i>, 2022.'),
    ("docfinqa", 'V. Reddy, R. Koncel-Kedziorski, V. D. Lai, M. Krumdick, C. Lovering, and C. Tanner, "DocFinQA: A long-context financial reasoning dataset," in <i>Proc. 62nd Annu. Meeting of the ACL (Short Papers)</i>, 2024.'),
    ("financebench", 'P. Islam, A. Kannappan, D. Kiela, R. Qian, N. Scherrer, and B. Vidgen, "FinanceBench: A new benchmark for financial question answering," arXiv:2311.11944, 2023.'),
    ("bloomberggpt", 'S. Wu, O. Irsoy, S. Lu, V. Dabravolski, M. Dredze, S. Gehrmann, P. Kambadur, D. Rosenberg, and G. Mann, "BloombergGPT: A large language model for finance," arXiv:2303.17564, 2023.'),
    ("tatllm", 'F. Zhu, Z. Liu, F. Feng, C. Wang, M. Li, and T.-S. Chua, "TAT-LLM: A specialized language model for discrete reasoning over tabular and textual data," in <i>Proc. 5th ACM Int. Conf. AI in Finance (ICAIF)</i>, 2024.'),
    ("eedp", 'P. Srivastava, M. Malik, V. Gupta, T. Ganu, and D. Roth, "Evaluating LLMs\' mathematical reasoning in financial document question answering," in <i>Findings of the ACL: ACL 2024</i>, 2024, pp. 3853–3878.'),
    ("gpt3", 'T. Brown <i>et al.</i>, "Language models are few-shot learners," in <i>Advances in Neural Information Processing Systems (NeurIPS)</i>, vol. 33, 2020.'),
    ("cot", 'J. Wei, X. Wang, D. Schuurmans, M. Bosma, B. Ichter, F. Xia, E. Chi, Q. Le, and D. Zhou, "Chain-of-thought prompting elicits reasoning in large language models," in <i>NeurIPS</i>, 2022.'),
    ("zscot", 'T. Kojima, S. S. Gu, M. Reid, Y. Matsuo, and Y. Iwasawa, "Large language models are zero-shot reasoners," in <i>NeurIPS</i>, 2022.'),
    ("sc", 'X. Wang, J. Wei, D. Schuurmans, Q. Le, E. Chi, S. Narang, A. Chowdhery, and D. Zhou, "Self-consistency improves chain of thought reasoning in language models," in <i>Proc. Int. Conf. Learning Representations (ICLR)</i>, 2023.'),
    ("l2m", 'D. Zhou <i>et al.</i>, "Least-to-most prompting enables complex reasoning in large language models," in <i>ICLR</i>, 2023.'),
    ("decomp", 'T. Khot, H. Trivedi, M. Finlayson, Y. Fu, K. Richardson, P. Clark, and A. Sabharwal, "Decomposed prompting: A modular approach for solving complex tasks," in <i>ICLR</i>, 2023.'),
    ("pot", 'W. Chen, X. Ma, X. Wang, and W. W. Cohen, "Program of thoughts prompting: Disentangling computation from reasoning for numerical reasoning tasks," <i>Trans. Machine Learning Research (TMLR)</i>, 2023.'),
    ("pal", 'L. Gao, A. Madaan, S. Zhou, U. Alon, P. Liu, Y. Yang, J. Callan, and G. Neubig, "PAL: Program-aided language models," in <i>Proc. Int. Conf. Machine Learning (ICML)</i>, 2023.'),
    ("ape", 'Y. Zhou, A. I. Muresanu, Z. Han, K. Paster, S. Pitis, H. Chan, and J. Ba, "Large language models are human-level prompt engineers," in <i>ICLR</i>, 2023.'),
    ("opro", 'C. Yang, X. Wang, Y. Lu, H. Liu, Q. V. Le, D. Zhou, and X. Chen, "Large language models as optimizers," in <i>ICLR</i>, 2024.'),
    ("dspy", 'O. Khattab <i>et al.</i>, "DSPy: Compiling declarative language model calls into self-improving pipelines," in <i>ICLR</i>, 2024.'),
    ("mipro", 'K. Opsahl-Ong, M. J. Ryan, J. Purtell, D. Broman, C. Potts, M. Zaharia, and O. Khattab, "Optimizing instructions and demonstrations for multi-stage language model programs," in <i>Proc. EMNLP</i>, 2024.'),
    ("textgrad", 'M. Yuksekgonul, F. Bianchi, J. Boen, S. Liu, P. Lu, Z. Huang, C. Guestrin, and J. Zou, "Optimizing generative AI by backpropagating language model feedback," <i>Nature</i>, vol. 639, pp. 609–616, 2025.'),
    ("tablellm", 'Y. Sui, M. Zhou, M. Zhou, S. Han, and D. Zhang, "Table meets LLM: Can large language models understand structured table data? A benchmark and empirical study," in <i>Proc. 17th ACM Int. Conf. Web Search and Data Mining (WSDM)</i>, 2024.'),
    ("bm25", 'S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," <i>Foundations and Trends in Information Retrieval</i>, vol. 3, no. 4, pp. 333–389, 2009.'),
    ("sbert", 'N. Reimers and I. Gurevych, "Sentence-BERT: Sentence embeddings using Siamese BERT-networks," in <i>Proc. EMNLP-IJCNLP</i>, 2019.'),
    ("faiss", 'J. Johnson, M. Douze, and H. Jégou, "Billion-scale similarity search with GPUs," <i>IEEE Trans. Big Data</i>, vol. 7, no. 3, pp. 535–547, 2021.'),
    ("rrf", 'G. V. Cormack, C. L. A. Clarke, and S. Büttcher, "Reciprocal rank fusion outperforms Condorcet and individual rank learning methods," in <i>Proc. 32nd Int. ACM SIGIR Conf.</i>, 2009, pp. 758–759.'),
    ("rag", 'P. Lewis <i>et al.</i>, "Retrieval-augmented generation for knowledge-intensive NLP tasks," in <i>NeurIPS</i>, 2020.'),
    ("gsmsym", 'I. Mirzadeh, K. Alizadeh, H. Shahrokhi, O. Tuzel, S. Bengio, and M. Farajtabar, "GSM-Symbolic: Understanding the limitations of mathematical reasoning in large language models," in <i>ICLR</i>, 2025.'),
    ("qwen3", 'A. Yang <i>et al.</i>, "Qwen3 technical report," arXiv:2505.09388, 2025.'),
    ("mcnemar", 'Q. McNemar, "Note on the sampling error of the difference between correlated proportions or percentages," <i>Psychometrika</i>, vol. 12, no. 2, pp. 153–157, 1947.'),
    ("bootstrap", 'B. Efron, "Bootstrap methods: Another look at the jackknife," <i>The Annals of Statistics</i>, vol. 7, no. 1, pp. 1–26, 1979.'),
    ("dror", 'R. Dror, G. Baumer, S. Shlomov, and R. Reichart, "The hitchhiker\'s guide to testing statistical significance in natural language processing," in <i>Proc. 56th Annu. Meeting of the ACL</i>, 2018, pp. 1383–1392.'),
    ("holm", 'S. Holm, "A simple sequentially rejective multiple test procedure," <i>Scandinavian Journal of Statistics</i>, vol. 6, no. 2, pp. 65–70, 1979.'),
    ("binder", 'Z. Cheng <i>et al.</i>, "Binding language models in symbolic languages," in <i>ICLR</i>, 2023.'),
    ("pands", 'L. Wang, W. Xu, Y. Lan, Z. Hu, Y. Lan, R. K.-W. Lee, and E.-P. Lim, "Plan-and-solve prompting: Improving zero-shot chain-of-thought reasoning by large language models," in <i>Proc. 61st Annu. Meeting of the ACL</i>, 2023.'),
    # recent closely related work (added after a 2026 literature check; appended so earlier numbers stay the same)
    ("indfin", 'CompoundingAI, "IndFin-Bench: A benchmark grounded in Indian financial filings," dataset on Hugging Face (CompoundingAI/IndFin-Bench), Apr. 2026.'),
    ("indiafin", 'R. S. Pall, "IndiaFinBench: An evaluation benchmark for large language model performance on Indian financial regulatory text," arXiv:2604.19298, 2026.'),
    ("verifin", 'B. Hall, S. Shome, and W. Eiers, "VeriFin: A neurosymbolic framework for verifying LLM-generated financial claims," arXiv:2608.10213, 2026.'),
    ("dcrc", 'H. Chen, X. Tang, Q. Liu, W. Shi, S. Li, F. Lyu, W. Luo, X. Du, and X. He, "Fighting numerical hallucinations via data-centric compilation for online financial QA," in <i>Proc. ACM SIGKDD Conf. Knowledge Discovery and Data Mining (KDD), ADS Track</i>, 2026.'),
    ("finreasoning", 'Z. Tang, H. E, Z. Ma, H. He, J. Liu, Z. Yang, Z. Rong, R. Li, K. Ji, Q. Huang, X. Hu, Y. Liu, and Q. Zheng, "FinanceReasoning: Benchmarking financial numerical reasoning more credible, comprehensive and challenging," in <i>Proc. 63rd Annu. Meeting of the ACL (Long Papers)</i>, 2025, pp. 15721–15749.'),
]

INDEX = {key: i + 1 for i, (key, _) in enumerate(REFS)}


def cite(*keys):
    """cite('cot', 'sc') -> '[10], [12]'"""
    return ", ".join(f"[{INDEX[k]}]" for k in keys)


def ref_list_html(cls="refs", keys=None):
    items = REFS if keys is None else [r for r in REFS if r[0] in keys]
    return f'<ol class="{cls}">' + "".join(f'<li value="{INDEX[k]}">{t}</li>' for k, t in items) + "</ol>"
