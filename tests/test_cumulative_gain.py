import pytest
import torch
import numpy as np

import hypothesis
from hypothesis import strategies as strat
from hypothesis import assume, given

import sklearn
from sklearn.metrics import dcg_score
from sklearn.metrics import ndcg_score

from ranking_metrics_torch.cumulative_gain import dcg_at
from ranking_metrics_torch.cumulative_gain import ndcg_at
from tests.conftest import scores_at_ks


def test_dcg_has_correct_shape(
    batch_size: int, cutoffs: torch.Tensor, scores: torch.Tensor, labels: torch.Tensor
) -> None:

    dcg_at_ks = dcg_at(cutoffs, scores, labels)
    assert len(dcg_at_ks.shape) == 2
    assert dcg_at_ks.shape == (batch_size, len(cutoffs))


def test_dcg_when_nothing_is_relevant(
    batch_size: int, num_items: int, cutoffs: torch.Tensor, scores: torch.Tensor
) -> None:

    dcg_at_ks = dcg_at(cutoffs, scores, torch.zeros(batch_size, num_items))
    assert (dcg_at_ks == torch.zeros(batch_size, len(cutoffs))).all()


@given(scores_at_ks())
def test_dcg_matches_sklearn(scores_at_ks):
    ks, pred_scores, true_scores = scores_at_ks

    for i in range(len(pred_scores)):
        assume(sum(pred_scores[i]) > 0)
        assume(sum(true_scores[i]) > 0)
        assume(len(set(pred_scores[i])) == len(pred_scores[i]))

    dcgs_at_k = dcg_at(
        torch.tensor(ks),
        torch.tensor(pred_scores, dtype=torch.float64),
        torch.tensor(true_scores, dtype=torch.float64),
    )

    for i in range(len(pred_scores)):
        sklearn_dcgs_at_k = [
            dcg_score([true_scores[i][:k]], [pred_scores[i][:k]], k=k, ignore_ties=True)
            for k in ks
        ]

        assert dcgs_at_k[i].tolist() == pytest.approx(sklearn_dcgs_at_k)

    assert 1 == 0


def test_ndcg_has_correct_shape(
    batch_size: int, cutoffs: torch.Tensor, scores: torch.Tensor, labels: torch.Tensor
) -> None:

    ndcg_at_ks = ndcg_at(cutoffs, scores, labels)
    assert len(ndcg_at_ks.shape) == 2
    assert ndcg_at_ks.shape == (batch_size, len(cutoffs))


def test_ndcg_when_largest_k_is_smaller_than_labels(
    batch_size: int, cutoffs: torch.Tensor, scores: torch.Tensor, labels: torch.Tensor
) -> None:

    ndcg_at_ks = ndcg_at(cutoffs, scores, labels)

    ndcg_at_1k = ndcg_at(cutoffs[:1], scores, labels)
    assert ndcg_at_1k[0] == ndcg_at_ks[0][0]

    ndcg_at_2ks = ndcg_at(cutoffs[:2], scores, labels)
    assert ndcg_at_2ks[0][0] == ndcg_at_ks[0][0]
    assert ndcg_at_2ks[0][1] == ndcg_at_ks[0][1]


def test_ndcg_when_nothing_is_relevant(
    batch_size: int, num_items: int, cutoffs: torch.Tensor, scores: torch.Tensor
) -> None:

    ndcg_at_ks = ndcg_at(cutoffs, scores, torch.zeros(batch_size, num_items))
    assert (ndcg_at_ks == torch.zeros(batch_size, len(cutoffs))).all()


@given(scores_at_ks())
def test_ndcg_matches_sklearn(scores_at_ks):
    ks, pred_scores, true_scores = scores_at_ks

    for i in range(len(pred_scores)):
        assume(sum(pred_scores[i]) > 0)
        assume(sum(true_scores[i]) > 0)
        assume(len(set(pred_scores[i])) == len(pred_scores[i]))

    ndcgs_at_k = ndcg_at(
        torch.tensor(ks),
        torch.tensor(pred_scores, dtype=torch.float64),
        torch.tensor(true_scores, dtype=torch.float64),
    )

    for i in range(len(pred_scores)):
        sklearn_dcgs_at_k = [
            ndcg_score(
                [true_scores[i][:k]], [pred_scores[i][:k]], k=k, ignore_ties=True
            )
            for k in ks
        ]

        assert ndcgs_at_k[i].tolist() == pytest.approx(sklearn_dcgs_at_k)


def test_dcg_of_1darray_matches_sklearn():
    true1d = np.array([[2, 5, 3, 1]])
    scores1d = np.array([[0.3, 1.0, 0.7, 0.4]])
    k = 3

    sk_result = dcg_score(y_true=true1d, y_score=scores1d, k=3)
    rm_result = dcg_at(
        ks=torch.tensor([k]),
        labels=torch.from_numpy(true1d),
        scores=torch.from_numpy(scores1d),
    )
    assert rm_result.numpy().mean() == pytest.approx(sk_result)


def test_ndcg_of_1darray_matches_sklearn():
    true1d = np.array([[2, 5, 3, 1]])
    scores1d = np.array([[0.3, 1.0, 0.7, 0.4]])
    k = 3

    sk_result = ndcg_score(y_true=true1d, y_score=scores1d, k=3)
    rm_result = ndcg_at(
        ks=torch.tensor([k]),
        labels=torch.from_numpy(true1d),
        scores=torch.from_numpy(scores1d),
    )
    assert rm_result.numpy().mean() == pytest.approx(sk_result)

