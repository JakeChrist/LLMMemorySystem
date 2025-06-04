import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory_manager import MemoryManager
from retrieval.retriever import Retriever
import storage.faiss_index as fi
from encoding import encoder


def test_retriever_with_faiss_index():
    class FakeIndex:
        def __init__(self, dim):
            self.vectors = []

        def add(self, arr):
            for row in arr:
                self.vectors.append(list(row))

        def search(self, arr, k):
            q = arr[0]
            dists = [sum((v_i - q_i) ** 2 for v_i, q_i in zip(v, q)) for v in self.vectors]
            idxs = sorted(range(len(dists)), key=dists.__getitem__)[:k]
            return [[dists[i] for i in idxs]], [idxs]

    fake_faiss = SimpleNamespace(IndexFlatL2=FakeIndex)

    class FakeNP:
        @staticmethod
        def array(data, dtype=None):
            return [list(row) for row in data]

    def fake_encode(text):
        mapping = {
            "the cat sat on the mat": [1.0, 0.0],
            "dogs are wonderful companions": [0.0, 1.0],
            "cat": [1.0, 0.0],
        }
        return mapping[text]

    with patch.object(fi, "faiss", fake_faiss):
        with patch.object(fi, "np", FakeNP):
            with patch.object(encoder, "encode_text", side_effect=fake_encode):
                with patch("core.memory_types.episodic.encode_text", side_effect=fake_encode):
                    with patch("retrieval.retriever.encode_text", side_effect=fake_encode):
                        manager = MemoryManager()
                        manager.add("the cat sat on the mat")
                        manager.add("dogs are wonderful companions")

                        retriever = Retriever(manager.all())
                        results = retriever.query("cat", top_k=1)
                        assert results
                        assert results[0].content == "the cat sat on the mat"
