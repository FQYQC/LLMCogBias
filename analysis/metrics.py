import numpy as np


def compute_clip_cohen_d(A, B):
    """
    Compute Cohen's d for two sets of clips.
    Please ensure check A>B
    """
    if len(A) == 1:
        A = np.concatenate([A, A])
    if len(B) == 1:
        B = np.concatenate([B, B])
    var_A = np.var(A, ddof=1)
    var_B = np.var(B, ddof=1)
    n_A = len(A)
    n_B = len(B)

    pooled_var = ((n_A - 1) * var_A + (n_B - 1) * var_B) / (n_A + n_B - 2)
    if pooled_var < 1e-5:
        return 0
    d = (np.mean(A) - np.mean(B)) / np.sqrt(pooled_var)

    return np.clip(d, 0, 2)


def compute_linear_l(A, target=1, morethan="other", tot=40):
    n_A = (A == target).sum()
    if morethan == "other":
        n_B = (A != target).sum()
    else:
        n_B = 0

    if tot == 0:
        return 0
    l = 2 * (n_A - n_B) / tot
    return np.clip(l, 0, 2)


if __name__ == "__main__":
    a = np.array([5, 5, 5, 5, 5, 5, 5, 5, 5, 5])
    b = np.array([5, 5, 5, 5, 5, 4, 5, 5, 5, 5])
    print(compute_clip_cohen_d(a, b))