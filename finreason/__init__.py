"""FinReason: prompting strategies and prompt optimization for numerical reasoning over financial reports."""
import os

# PyTorch (embeddings) and FAISS each bundle their own OpenMP runtime; on macOS loading both
# with many threads crashes the process. One OpenMP thread avoids the conflict.
os.environ.setdefault("OMP_NUM_THREADS", "1")
